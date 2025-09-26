import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """광고 성과 데이터 처리 및 분석 클래스"""
    
    def __init__(self):
        # 사용자 요청 지표: 노출, 도달, 링크클릭, 랜딩페이지조회, 지출금액, CTR, CPM
        self.performance_metrics = [
            'impressions', 'reach', 'link_clicks', 'landing_page_views', 'spend', 'ctr', 'cpm'
        ]
        # 특정 캠페인 필터링
        self.target_campaign_name = "[엠아트]250922"
    
    def calculate_performance_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """성과 지표 계산 및 보완"""
        if df.empty:
            return df
        
        df = df.copy()
        
        # 기본 지표들은 이미 API에서 계산되어 옴
        # 추가 계산이 필요한 지표들만 처리
        
        # 링크클릭당 비용 (Cost Per Link Click) 계산
        df['cost_per_link_click'] = np.where(df['link_clicks'] > 0, 
                                           df['spend'] / df['link_clicks'], 0)
        
        # 랜딩페이지조회당 비용 (Cost Per Landing Page View) 계산
        df['cost_per_landing_page_view'] = np.where(df['landing_page_views'] > 0, 
                                                  df['spend'] / df['landing_page_views'], 0)
        
        # 도달률 (Reach Rate) 계산 - 도달/노출 비율
        df['reach_rate'] = np.where(df['impressions'] > 0, 
                                  (df['reach'] / df['impressions']) * 100, 0)
        
        # 효율성 점수 계산 (CTR, CPM, 링크클릭당 비용 기반)
        df['efficiency_score'] = self.calculate_efficiency_score(df)
        
        # 무한대 및 NaN 값 처리
        df = df.replace([np.inf, -np.inf], 0)
        df = df.fillna(0)
        
        # 소수점 정리
        numeric_columns = ['ctr', 'cpm', 'cost_per_link_click', 'cost_per_landing_page_view', 'reach_rate', 'efficiency_score']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].round(2)
        
        return df
    
    def calculate_efficiency_score(self, df: pd.DataFrame) -> pd.Series:
        """광고 세트 효율성 점수 계산 (CTR, CPM, 링크클릭당 비용 기반)"""
        try:
            # 정규화를 위한 최대값 설정
            max_ctr = df['ctr'].quantile(0.95) if df['ctr'].max() > 0 else 1
            min_cpm = df['cpm'].quantile(0.05) if df['cpm'].min() > 0 else 1  # CPM은 낮을수록 좋음
            min_cost_per_click = df['cost_per_link_click'].quantile(0.05) if df['cost_per_link_click'].min() > 0 else 1  # 링크클릭당 비용도 낮을수록 좋음
            
            # 각 지표를 0-1 스케일로 정규화
            normalized_ctr = np.clip(df['ctr'] / max_ctr, 0, 1)
            # CPM과 링크클릭당 비용은 역정규화 (낮을수록 좋은 점수)
            normalized_cpm = np.clip(1 - (df['cpm'] / df['cpm'].quantile(0.95)), 0, 1) if df['cpm'].max() > 0 else 0
            normalized_cost_per_click = np.clip(1 - (df['cost_per_link_click'] / df['cost_per_link_click'].quantile(0.95)), 0, 1) if df['cost_per_link_click'].max() > 0 else 0
            
            # 가중 평균으로 효율성 점수 계산 (CTR 40%, CPM 30%, 링크클릭당 비용 30%)
            efficiency_score = (normalized_ctr * 0.4 + 
                              normalized_cpm * 0.3 + 
                              normalized_cost_per_click * 0.3) * 100
            
            return efficiency_score
            
        except Exception as e:
            logger.warning(f"효율성 점수 계산 실패: {e}")
            return pd.Series([0] * len(df))
    
    def compare_adsets_performance(self, df: pd.DataFrame) -> Dict:
        """광고 세트 성과 비교 분석"""
        if df.empty:
            return {}
        
        try:
            # 광고 세트별 집계
            adset_summary = df.groupby(['adset_id', 'adset_name']).agg({
                'spend': 'sum',                    # 지출금액
                'impressions': 'sum',              # 노출
                'reach': 'sum',                    # 도달
                'link_clicks': 'sum',              # 링크클릭
                'landing_page_views': 'sum',       # 랜딩페이지조회
                'ctr': 'mean',                     # CTR
                'cpm': 'mean',                     # CPM
                'efficiency_score': 'mean'
            }).reset_index()
            
            # 계산된 지표 추가
            adset_summary = self.calculate_performance_metrics(adset_summary)
            
            # 성과 순위 (효율성 점수 기준)
            adset_summary = adset_summary.sort_values('efficiency_score', ascending=False)
            
            # 상위/하위 성과자 식별
            total_adsets = len(adset_summary)
            top_performers = adset_summary.head(max(1, total_adsets // 4))  # 상위 25%
            bottom_performers = adset_summary.tail(max(1, total_adsets // 4))  # 하위 25%
            
            # 성과 차이 분석
            performance_gap = {
                'top_avg_ctr': top_performers['ctr'].mean(),
                'bottom_avg_ctr': bottom_performers['ctr'].mean(),
                'top_avg_cpm': top_performers['cpm'].mean(),
                'bottom_avg_cpm': bottom_performers['cpm'].mean(),
                'top_avg_cost_per_result': top_performers['cost_per_result'].mean(),
                'bottom_avg_cost_per_result': bottom_performers['cost_per_result'].mean(),
                'ctr_improvement_potential': top_performers['ctr'].mean() - bottom_performers['ctr'].mean(),
                'cpm_improvement_potential': bottom_performers['cpm'].mean() - top_performers['cpm'].mean()  # CPM은 낮을수록 좋음
            }
            
            return {
                'adset_rankings': adset_summary.to_dict('records'),
                'top_performers': top_performers.to_dict('records'),
                'bottom_performers': bottom_performers.to_dict('records'),
                'performance_gap': performance_gap,
                'total_adsets': total_adsets
            }
            
        except Exception as e:
            logger.error(f"광고 세트 성과 비교 실패: {e}")
            return {}
    
    def analyze_daily_trends(self, df: pd.DataFrame) -> Dict:
        """일간 성과 트렌드 분석"""
        if df.empty:
            return {}
        
        try:
            # 일별 집계
            daily_data = df.groupby('date').agg({
                'spend': 'sum',                    # 지출금액
                'impressions': 'sum',              # 노출
                'reach': 'sum',                    # 도달
                'link_clicks': 'sum',              # 링크클릭
                'landing_page_views': 'sum',       # 랜딩페이지조회
                'ctr': 'mean',                     # CTR
                'cpm': 'mean'                      # CPM
            }).reset_index()
            
            # 계산된 지표 추가
            daily_data = self.calculate_performance_metrics(daily_data)
            daily_data = daily_data.sort_values('date')
            
            # 트렌드 분석
            if len(daily_data) >= 7:  # 최소 7일 데이터
                # 최근 7일 vs 이전 7일 비교
                recent_7days = daily_data.tail(7)
                previous_7days = daily_data.iloc[-14:-7] if len(daily_data) >= 14 else daily_data.head(7)
                
                trend_analysis = {
                    'spend_trend': self.calculate_trend_percentage(
                        previous_7days['spend'].sum(), recent_7days['spend'].sum()
                    ),
                    'impressions_trend': self.calculate_trend_percentage(
                        previous_7days['impressions'].sum(), recent_7days['impressions'].sum()
                    ),
                    'reach_trend': self.calculate_trend_percentage(
                        previous_7days['reach'].sum(), recent_7days['reach'].sum()
                    ),
                    'results_trend': self.calculate_trend_percentage(
                        previous_7days['results'].sum(), recent_7days['results'].sum()
                    ),
                    'ctr_trend': self.calculate_trend_percentage(
                        previous_7days['ctr'].mean(), recent_7days['ctr'].mean()
                    ),
                    'cpm_trend': self.calculate_trend_percentage(
                        previous_7days['cpm'].mean(), recent_7days['cpm'].mean()
                    )
                }
            else:
                trend_analysis = {}
            
            # 요일별 성과 패턴 분석
            daily_data['weekday'] = pd.to_datetime(daily_data['date']).dt.day_name()
            weekday_performance = daily_data.groupby('weekday').agg({
                'spend': 'mean',
                'ctr': 'mean',
                'cpm': 'mean',
                'results': 'mean'
            }).reset_index()
            
            # 최고/최저 성과일 식별 (효율성 점수 기준)
            best_day = daily_data.loc[daily_data['efficiency_score'].idxmax()] if 'efficiency_score' in daily_data.columns and daily_data['efficiency_score'].max() > 0 else None
            worst_day = daily_data.loc[daily_data['efficiency_score'].idxmin()] if 'efficiency_score' in daily_data.columns and len(daily_data) > 1 else None
            
            return {
                'daily_data': daily_data.to_dict('records'),
                'trend_analysis': trend_analysis,
                'weekday_performance': weekday_performance.to_dict('records'),
                'best_performance_day': best_day.to_dict() if best_day is not None else None,
                'worst_performance_day': worst_day.to_dict() if worst_day is not None else None,
                'total_days': len(daily_data)
            }
            
        except Exception as e:
            logger.error(f"일간 트렌드 분석 실패: {e}")
            return {}
    
    def calculate_trend_percentage(self, old_value: float, new_value: float) -> float:
        """트렌드 변화율 계산"""
        if old_value == 0:
            return 100.0 if new_value > 0 else 0.0
        return round(((new_value - old_value) / old_value) * 100, 2)
    
    def generate_insights_and_recommendations(self, comparison_data: Dict, trend_data: Dict) -> List[Dict]:
        """성과 데이터 기반 인사이트 및 추천사항 생성"""
        insights = []
        
        try:
            # 광고 세트 성과 인사이트
            if comparison_data and 'performance_gap' in comparison_data:
                gap = comparison_data['performance_gap']
                
                if gap['roas_improvement_potential'] > 1.0:
                    insights.append({
                        'type': 'performance_gap',
                        'title': '광고 세트 성과 격차 발견',
                        'description': f"상위 성과 광고 세트와 하위 성과 광고 세트 간 ROAS 차이가 {gap['roas_improvement_potential']:.2f}입니다.",
                        'recommendation': '하위 성과 광고 세트의 타겟팅, 크리에이티브, 입찰 전략을 상위 성과자와 비교하여 최적화하세요.',
                        'priority': 'high'
                    })
                
                if gap['top_avg_ctr'] > gap['bottom_avg_ctr'] * 2:
                    insights.append({
                        'type': 'ctr_optimization',
                        'title': 'CTR 개선 기회',
                        'description': f"상위 성과자의 평균 CTR({gap['top_avg_ctr']:.2f}%)이 하위 성과자({gap['bottom_avg_ctr']:.2f}%)보다 2배 이상 높습니다.",
                        'recommendation': '하위 성과 광고 세트의 광고 소재와 메시지를 개선하여 클릭률을 높이세요.',
                        'priority': 'medium'
                    })
            
            # 트렌드 인사이트
            if trend_data and 'trend_analysis' in trend_data:
                trends = trend_data['trend_analysis']
                
                if 'spend_trend' in trends and trends['spend_trend'] > 20:
                    insights.append({
                        'type': 'budget_alert',
                        'title': '광고비 급증 알림',
                        'description': f"최근 7일간 광고비가 {trends['spend_trend']:.1f}% 증가했습니다.",
                        'recommendation': '예산 증가 대비 성과 개선을 확인하고, 필요시 입찰 조정을 고려하세요.',
                        'priority': 'high'
                    })
                
                if 'roas_trend' in trends and trends['roas_trend'] < -15:
                    insights.append({
                        'type': 'roas_decline',
                        'title': 'ROAS 하락 경고',
                        'description': f"최근 7일간 ROAS가 {abs(trends['roas_trend']):.1f}% 하락했습니다.",
                        'recommendation': '광고 피로도, 경쟁 상황, 타겟 오디언스 변화를 점검하고 전략을 조정하세요.',
                        'priority': 'high'
                    })
                
                if 'conversions_trend' in trends and trends['conversions_trend'] > 30:
                    insights.append({
                        'type': 'conversion_growth',
                        'title': '전환 성과 개선',
                        'description': f"최근 7일간 전환이 {trends['conversions_trend']:.1f}% 증가했습니다.",
                        'recommendation': '현재 성과가 좋은 광고 세트에 예산을 추가 배정하여 성과를 극대화하세요.',
                        'priority': 'medium'
                    })
            
            # 요일별 성과 인사이트
            if trend_data and 'weekday_performance' in trend_data:
                weekday_data = pd.DataFrame(trend_data['weekday_performance'])
                if not weekday_data.empty:
                    best_weekday = weekday_data.loc[weekday_data['roas'].idxmax()]
                    worst_weekday = weekday_data.loc[weekday_data['roas'].idxmin()]
                    
                    if best_weekday['roas'] > worst_weekday['roas'] * 1.5:
                        insights.append({
                            'type': 'weekday_pattern',
                            'title': '요일별 성과 패턴 발견',
                            'description': f"{best_weekday['weekday']}의 ROAS({best_weekday['roas']:.2f})가 {worst_weekday['weekday']}({worst_weekday['roas']:.2f})보다 현저히 높습니다.",
                            'recommendation': f"{best_weekday['weekday']}에 예산을 집중하고, {worst_weekday['weekday']}의 광고 전략을 재검토하세요.",
                            'priority': 'medium'
                        })
            
        except Exception as e:
            logger.error(f"인사이트 생성 실패: {e}")
        
        # 우선순위별 정렬
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        insights.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return insights
    
    def prepare_sheets_data_for_campaign(self, adset_data: pd.DataFrame, daily_data: pd.DataFrame) -> Dict:
        """특정 캠페인의 Google Sheets 업로드용 데이터 준비"""
        sheets_data = {}
        
        try:
            # 광고 세트별 데이터 시트
            if not adset_data.empty:
                # 업데이트 일시 추가
                from datetime import datetime
                adset_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 필요한 컬럼만 선택하고 순서 정리
                adset_columns = [
                    'adset_name', 'spend', 'impressions', 'reach', 'link_clicks', 'landing_page_views', 'ctr', 'cpm', 'updated_at'
                ]
                # 존재하는 컬럼만 선택
                available_columns = [col for col in adset_columns if col in adset_data.columns]
                adset_summary = adset_data[available_columns].copy()
                
                # 컬럼명 한글화
                column_mapping = {
                    'adset_name': '광고세트명',
                    'spend': '지출금액',
                    'impressions': '노출',
                    'reach': '도달',
                    'link_clicks': '링크클릭',
                    'landing_page_views': '랜딩페이지조회',
                    'ctr': 'CTR(%)',
                    'cpm': 'CPM',
                    'updated_at': '업데이트 일시'
                }
                
                # CTR 값을 100으로 나누어 올바른 퍼센트 값으로 변환
                if 'ctr' in adset_summary.columns:
                    adset_summary['ctr'] = adset_summary['ctr'] / 100
                
                adset_summary.rename(columns=column_mapping, inplace=True)
                sheets_data['adset_performance'] = adset_summary
            
            # 일별 데이터 시트
            if not daily_data.empty:
                # 날짜 포맷 조정
                daily_df = daily_data.copy()
                if 'date' in daily_df.columns:
                    daily_df['date'] = pd.to_datetime(daily_df['date']).dt.strftime('%Y-%m-%d')
                
                # 필요한 컬럼만 선택
                daily_columns = [
                    'date', 'spend', 'impressions', 'reach', 'link_clicks', 'landing_page_views', 'ctr', 'cpm'
                ]
                # 존재하는 컬럼만 선택
                available_daily_columns = [col for col in daily_columns if col in daily_df.columns]
                daily_summary = daily_df[available_daily_columns].copy()
                
                # 컬럼명 한글화
                daily_column_mapping = {
                    'date': '날짜',
                    'spend': '지출금액',
                    'impressions': '노출',
                    'reach': '도달',
                    'link_clicks': '링크클릭',
                    'landing_page_views': '랜딩페이지조회',
                    'ctr': 'CTR(%)',
                    'cpm': 'CPM'
                }
                
                # CTR 값을 100으로 나누어 올바른 퍼센트 값으로 변환
                if 'ctr' in daily_summary.columns:
                    daily_summary['ctr'] = daily_summary['ctr'] / 100
                
                daily_summary.rename(columns=daily_column_mapping, inplace=True)
                sheets_data['daily_trend'] = daily_summary
            
        except Exception as e:
            logger.error(f"Sheets 데이터 준비 실패: {e}")
        
        return sheets_data
    
    def filter_campaign_data(self, campaigns_data: List[Dict]) -> str:
        """특정 캠페인 '[엠아트]250922' 필터링"""
        try:
            for campaign in campaigns_data:
                if campaign.get('campaign_name') == self.target_campaign_name:
                    return campaign.get('campaign_id')
            
            logger.warning(f"캠페인 '{self.target_campaign_name}'을 찾을 수 없습니다.")
            return None
            
        except Exception as e:
            logger.error(f"캠페인 필터링 실패: {e}")
            return None 