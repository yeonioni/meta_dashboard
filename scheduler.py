import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import json
import os

from meta_api_client import MetaAPIClient
from data_processor import DataProcessor
from sheets_manager import SheetsManager
from config import *

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PerformanceScheduler:
    """일간 성과 추적 및 자동화 스케줄러"""
    
    def __init__(self):
        self.meta_client = None
        self.data_processor = DataProcessor()
        self.sheets_manager = None
        self.config_file = 'scheduler_config.json'
        self.load_config()
        
    def load_config(self):
        """스케줄러 설정 로드"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                # 기본 설정
                self.config = {
                    'campaigns': [],  # 모니터링할 캠페인 ID 목록
                    'notification_emails': [],  # 알림 받을 이메일 목록
                    'alert_thresholds': {
                        'roas_decline_threshold': -15,  # ROAS 하락 임계값 (%)
                        'spend_increase_threshold': 20,  # 광고비 증가 임계값 (%)
                        'conversion_decline_threshold': -20  # 전환 하락 임계값 (%)
                    },
                    'schedule_times': {
                        'hourly_update': 1,  # 1시간마다 업데이트
                        'daily_report': '09:00',  # 일간 리포트 시간
                        'weekly_summary': 'monday 10:00',  # 주간 요약 시간
                        'performance_check': '*/2'  # 2시간마다 성과 체크
                    },
                    'sheets_config': {
                        'auto_update': True,
                        'create_daily_sheets': True,
                        'archive_old_data': True
                    }
                }
                self.save_config()
                
        except Exception as e:
            logger.error(f"설정 로드 실패: {e}")
            self.config = {}
    
    def save_config(self):
        """스케줄러 설정 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"설정 저장 실패: {e}")
    
    def initialize_clients(self):
        """API 클라이언트 초기화"""
        try:
            self.meta_client = MetaAPIClient()
            self.sheets_manager = SheetsManager()
            logger.info("API 클라이언트가 초기화되었습니다.")
        except Exception as e:
            logger.error(f"API 클라이언트 초기화 실패: {e}")
            raise
    
    def add_campaign_to_monitor(self, campaign_id: str, campaign_name: str = None):
        """모니터링할 캠페인 추가"""
        try:
            campaign_info = {
                'campaign_id': campaign_id,
                'campaign_name': campaign_name or campaign_id,
                'added_date': datetime.now().isoformat(),
                'active': True
            }
            
            # 중복 확인
            existing_campaigns = [c['campaign_id'] for c in self.config.get('campaigns', [])]
            if campaign_id not in existing_campaigns:
                self.config.setdefault('campaigns', []).append(campaign_info)
                self.save_config()
                logger.info(f"캠페인 {campaign_id}이 모니터링 목록에 추가되었습니다.")
            else:
                logger.warning(f"캠페인 {campaign_id}은 이미 모니터링 중입니다.")
                
        except Exception as e:
            logger.error(f"캠페인 추가 실패: {e}")
    
    def remove_campaign_from_monitor(self, campaign_id: str):
        """모니터링에서 캠페인 제거"""
        try:
            campaigns = self.config.get('campaigns', [])
            self.config['campaigns'] = [c for c in campaigns if c['campaign_id'] != campaign_id]
            self.save_config()
            logger.info(f"캠페인 {campaign_id}이 모니터링에서 제거되었습니다.")
        except Exception as e:
            logger.error(f"캠페인 제거 실패: {e}")
    
    def collect_campaign_performance_data(self):
        """특정 캠페인 '[엠아트]250922' 성과 데이터 수집"""
        logger.info("캠페인 '[엠아트]250922' 성과 데이터 수집을 시작합니다.")
        
        try:
            if not self.meta_client:
                self.initialize_clients()
            
            # 모든 캠페인 조회하여 '[엠아트]250922' 찾기
            campaigns = self.meta_client.get_campaigns()
            target_campaign_id = self.data_processor.filter_campaign_data(campaigns)
            
            if not target_campaign_id:
                logger.error("캠페인 '[엠아트]250922'를 찾을 수 없습니다.")
                return
            
            # 광고 세트 목록 조회
            adsets = self.meta_client.get_adsets_by_campaign(target_campaign_id)
            if not adsets:
                logger.warning(f"캠페인 {target_campaign_id}에 광고 세트가 없습니다.")
                return
            
            adset_ids = [adset['adset_id'] for adset in adsets]
            
            # 최근 30일 데이터 수집 (광고 세트별 데이터용)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            date_from = start_date.strftime('%Y-%m-%d')
            date_to = end_date.strftime('%Y-%m-%d')
            
            # 성과 데이터 조회
            insights_df = self.meta_client.get_adset_insights(
                adset_ids, date_from, date_to
            )
            
            if insights_df.empty:
                logger.warning("수집된 성과 데이터가 없습니다.")
                return
            
            # 데이터 처리
            insights_df = self.data_processor.calculate_performance_metrics(insights_df)
            
            # 광고 세트별 데이터 (최신 데이터 기준으로 집계)
            adset_data = insights_df.groupby(['adset_id', 'adset_name']).agg({
                'spend': 'sum',
                'impressions': 'sum',
                'reach': 'sum',
                'results': 'sum',
                'ctr': 'mean',
                'cpm': 'mean'
            }).reset_index()
            
            # 일별 데이터 (최근 30일)
            daily_data = insights_df.groupby('date').agg({
                'spend': 'sum',
                'impressions': 'sum',
                'reach': 'sum',
                'results': 'sum',
                'ctr': 'mean',
                'cpm': 'mean'
            }).reset_index()
            
            # Google Sheets 업데이트
            if self.config.get('sheets_config', {}).get('auto_update', True):
                self._update_campaign_sheets(adset_data, daily_data)
            
            logger.info(f"캠페인 데이터 수집 완료: 광고세트 {len(adset_data)}개, 일별 데이터 {len(daily_data)}일")
            
        except Exception as e:
            logger.error(f"캠페인 성과 데이터 수집 실패: {e}")
    
    def collect_daily_performance_data(self):
        """일간 성과 데이터 수집 (기존 호환성 유지)"""
        logger.info("일간 성과 데이터 수집을 시작합니다.")
        
        try:
            if not self.meta_client:
                self.initialize_clients()
            
            all_performance_data = []
            campaigns = self.config.get('campaigns', [])
            
            for campaign_info in campaigns:
                if not campaign_info.get('active', True):
                    continue
                    
                campaign_id = campaign_info['campaign_id']
                
                try:
                    # 어제 데이터 수집
                    yesterday = datetime.now() - timedelta(days=1)
                    date_str = yesterday.strftime('%Y-%m-%d')
                    
                    # 광고 세트 목록 조회
                    adsets = self.meta_client.get_adsets_by_campaign(campaign_id)
                    if not adsets:
                        logger.warning(f"캠페인 {campaign_id}에 광고 세트가 없습니다.")
                        continue
                    
                    adset_ids = [adset['adset_id'] for adset in adsets]
                    
                    # 성과 데이터 조회
                    insights_df = self.meta_client.get_adset_insights(
                        adset_ids, date_str, date_str
                    )
                    
                    if not insights_df.empty:
                        # 데이터 처리
                        insights_df = self.data_processor.calculate_performance_metrics(insights_df)
                        
                        # 캠페인 정보 추가
                        insights_df['collection_date'] = datetime.now().isoformat()
                        insights_df['campaign_name'] = campaign_info.get('campaign_name', campaign_id)
                        
                        all_performance_data.append({
                            'campaign_id': campaign_id,
                            'campaign_name': campaign_info.get('campaign_name', campaign_id),
                            'data': insights_df.to_dict('records'),
                            'summary': self._calculate_campaign_summary(insights_df)
                        })
                        
                        logger.info(f"캠페인 {campaign_id} 데이터 수집 완료: {len(insights_df)}건")
                    
                except Exception as e:
                    logger.error(f"캠페인 {campaign_id} 데이터 수집 실패: {e}")
                    continue
            
            # 수집된 데이터 저장
            if all_performance_data:
                self._save_daily_data(all_performance_data, yesterday)
                
                # Google Sheets 업데이트 (설정에 따라)
                if self.config.get('sheets_config', {}).get('auto_update', True):
                    self._update_sheets_with_daily_data(all_performance_data, yesterday)
                
                # 성과 알림 체크
                self._check_performance_alerts(all_performance_data)
                
            logger.info(f"일간 성과 데이터 수집 완료: {len(all_performance_data)}개 캠페인")
            
        except Exception as e:
            logger.error(f"일간 성과 데이터 수집 실패: {e}")
    
    def _calculate_campaign_summary(self, df):
        """캠페인 요약 통계 계산"""
        return {
            'total_spend': df['spend'].sum(),
            'total_impressions': df['impressions'].sum(),
            'total_clicks': df['clicks'].sum(),
            'total_conversions': df['conversions'].sum(),
            'avg_ctr': df['ctr'].mean(),
            'avg_cpc': df['cpc'].mean(),
            'avg_roas': df['roas'].mean(),
            'adset_count': len(df)
        }
    
    def _save_daily_data(self, performance_data: List[Dict], date: datetime):
        """일간 데이터를 파일로 저장"""
        try:
            # 데이터 디렉토리 생성
            data_dir = 'daily_data'
            os.makedirs(data_dir, exist_ok=True)
            
            # 날짜별 파일명
            filename = f"{data_dir}/performance_{date.strftime('%Y%m%d')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(performance_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"일간 데이터가 저장되었습니다: {filename}")
            
        except Exception as e:
            logger.error(f"일간 데이터 저장 실패: {e}")
    
    def _update_campaign_sheets(self, adset_data: pd.DataFrame, daily_data: pd.DataFrame):
        """Google Sheets에 캠페인 데이터 업데이트"""
        try:
            if not self.sheets_manager:
                self.sheets_manager = SheetsManager()
            
            # 데이터 준비
            sheets_data = self.data_processor.prepare_sheets_data_for_campaign(adset_data, daily_data)
            
            # 시트 업데이트
            results = self.sheets_manager.upload_campaign_data(sheets_data)
            
            # 포맷팅 적용
            self.sheets_manager.add_campaign_data_formatting()
            
            if any(results.values()):
                logger.info("Google Sheets 캠페인 데이터 업데이트 완료")
            else:
                logger.warning("Google Sheets 업데이트에 실패했습니다")
                
        except Exception as e:
            logger.error(f"Google Sheets 캠페인 데이터 업데이트 실패: {e}")
    
    def _update_sheets_with_daily_data(self, performance_data: List[Dict], date: datetime):
        """Google Sheets에 일간 데이터 업데이트 (기존 호환성 유지)"""
        try:
            if not self.sheets_manager:
                self.sheets_manager = SheetsManager()
            
            # 일간 요약 데이터 준비
            daily_summary = []
            for campaign_data in performance_data:
                summary = campaign_data['summary']
                daily_summary.append({
                    '날짜': date.strftime('%Y-%m-%d'),
                    '캠페인명': campaign_data['campaign_name'],
                    '광고비': summary['total_spend'],
                    '노출수': summary['total_impressions'],
                    '클릭수': summary['total_clicks'],
                    '전환수': summary['total_conversions'],
                    'CTR': summary['avg_ctr'],
                    'CPC': summary['avg_cpc'],
                    'ROAS': summary['avg_roas'],
                    '광고세트수': summary['adset_count']
                })
            
            if daily_summary:
                df = pd.DataFrame(daily_summary)
                
                # 일간 트렌드 시트에 추가 (기존 데이터에 append)
                success = self.sheets_manager.upload_dataframe_to_sheet(
                    df, 
                    "일간 성과 트렌드", 
                    include_header=False,
                    clear_existing=False
                )
                
                if success:
                    logger.info("Google Sheets 일간 데이터 업데이트 완료")
                
        except Exception as e:
            logger.error(f"Google Sheets 업데이트 실패: {e}")
    
    def _check_performance_alerts(self, performance_data: List[Dict]):
        """성과 알림 체크"""
        try:
            alerts = []
            thresholds = self.config.get('alert_thresholds', {})
            
            for campaign_data in performance_data:
                campaign_name = campaign_data['campaign_name']
                summary = campaign_data['summary']
                
                # 이전 데이터와 비교 (7일 전 데이터)
                previous_data = self._get_previous_performance_data(
                    campaign_data['campaign_id'], days_ago=7
                )
                
                if previous_data:
                    # ROAS 변화 체크
                    roas_change = self._calculate_percentage_change(
                        previous_data.get('avg_roas', 0), summary['avg_roas']
                    )
                    
                    if roas_change < thresholds.get('roas_decline_threshold', -15):
                        alerts.append({
                            'type': 'roas_decline',
                            'campaign': campaign_name,
                            'message': f"ROAS가 {abs(roas_change):.1f}% 하락했습니다.",
                            'current_value': summary['avg_roas'],
                            'previous_value': previous_data.get('avg_roas', 0),
                            'severity': 'high'
                        })
                    
                    # 광고비 변화 체크
                    spend_change = self._calculate_percentage_change(
                        previous_data.get('total_spend', 0), summary['total_spend']
                    )
                    
                    if spend_change > thresholds.get('spend_increase_threshold', 20):
                        alerts.append({
                            'type': 'spend_increase',
                            'campaign': campaign_name,
                            'message': f"광고비가 {spend_change:.1f}% 증가했습니다.",
                            'current_value': summary['total_spend'],
                            'previous_value': previous_data.get('total_spend', 0),
                            'severity': 'medium'
                        })
                    
                    # 전환 변화 체크
                    conversion_change = self._calculate_percentage_change(
                        previous_data.get('total_conversions', 0), summary['total_conversions']
                    )
                    
                    if conversion_change < thresholds.get('conversion_decline_threshold', -20):
                        alerts.append({
                            'type': 'conversion_decline',
                            'campaign': campaign_name,
                            'message': f"전환수가 {abs(conversion_change):.1f}% 감소했습니다.",
                            'current_value': summary['total_conversions'],
                            'previous_value': previous_data.get('total_conversions', 0),
                            'severity': 'high'
                        })
            
            # 알림 발송
            if alerts:
                self._send_alerts(alerts)
                
        except Exception as e:
            logger.error(f"성과 알림 체크 실패: {e}")
    
    def _get_previous_performance_data(self, campaign_id: str, days_ago: int = 7):
        """이전 성과 데이터 조회"""
        try:
            target_date = datetime.now() - timedelta(days=days_ago)
            filename = f"daily_data/performance_{target_date.strftime('%Y%m%d')}.json"
            
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for campaign_data in data:
                    if campaign_data['campaign_id'] == campaign_id:
                        return campaign_data['summary']
            
            return None
            
        except Exception as e:
            logger.warning(f"이전 데이터 조회 실패: {e}")
            return None
    
    def _calculate_percentage_change(self, old_value: float, new_value: float) -> float:
        """변화율 계산"""
        if old_value == 0:
            return 100.0 if new_value > 0 else 0.0
        return ((new_value - old_value) / old_value) * 100
    
    def _send_alerts(self, alerts: List[Dict]):
        """알림 발송 (로그 기록)"""
        try:
            # 심각도별 분류
            high_alerts = [a for a in alerts if a['severity'] == 'high']
            medium_alerts = [a for a in alerts if a['severity'] == 'medium']
            
            logger.warning(f"성과 알림 발생: 높음 {len(high_alerts)}건, 보통 {len(medium_alerts)}건")
            
            for alert in alerts:
                logger.warning(f"[{alert['severity'].upper()}] {alert['campaign']}: {alert['message']}")
            
            # 실제 이메일 발송 로직은 여기에 구현
            # (SMTP 설정, 이메일 템플릿 등)
            
        except Exception as e:
            logger.error(f"알림 발송 실패: {e}")
    
    def generate_weekly_summary(self):
        """주간 요약 리포트 생성"""
        logger.info("주간 요약 리포트 생성을 시작합니다.")
        
        try:
            # 지난 7일간의 데이터 수집
            weekly_data = []
            for i in range(7):
                date = datetime.now() - timedelta(days=i+1)
                filename = f"daily_data/performance_{date.strftime('%Y%m%d')}.json"
                
                if os.path.exists(filename):
                    with open(filename, 'r', encoding='utf-8') as f:
                        daily_data = json.load(f)
                        weekly_data.extend(daily_data)
            
            if not weekly_data:
                logger.warning("주간 요약을 위한 데이터가 없습니다.")
                return
            
            # 캠페인별 주간 집계
            campaign_summaries = {}
            for daily_campaign in weekly_data:
                campaign_id = daily_campaign['campaign_id']
                
                if campaign_id not in campaign_summaries:
                    campaign_summaries[campaign_id] = {
                        'campaign_name': daily_campaign['campaign_name'],
                        'total_spend': 0,
                        'total_impressions': 0,
                        'total_clicks': 0,
                        'total_conversions': 0,
                        'daily_count': 0
                    }
                
                summary = daily_campaign['summary']
                campaign_summaries[campaign_id]['total_spend'] += summary['total_spend']
                campaign_summaries[campaign_id]['total_impressions'] += summary['total_impressions']
                campaign_summaries[campaign_id]['total_clicks'] += summary['total_clicks']
                campaign_summaries[campaign_id]['total_conversions'] += summary['total_conversions']
                campaign_summaries[campaign_id]['daily_count'] += 1
            
            # 주간 요약 Google Sheets 업데이트
            if self.config.get('sheets_config', {}).get('auto_update', True):
                self._create_weekly_summary_sheet(campaign_summaries)
            
            logger.info(f"주간 요약 리포트 생성 완료: {len(campaign_summaries)}개 캠페인")
            
        except Exception as e:
            logger.error(f"주간 요약 리포트 생성 실패: {e}")
    
    def _create_weekly_summary_sheet(self, campaign_summaries: Dict):
        """주간 요약 시트 생성"""
        try:
            if not self.sheets_manager:
                self.sheets_manager = SheetsManager()
            
            # 주간 요약 데이터 준비
            weekly_summary = []
            for campaign_id, summary in campaign_summaries.items():
                # 평균 지표 계산
                avg_ctr = (summary['total_clicks'] / summary['total_impressions'] * 100) if summary['total_impressions'] > 0 else 0
                avg_cpc = (summary['total_spend'] / summary['total_clicks']) if summary['total_clicks'] > 0 else 0
                roas = 0  # 실제 매출 데이터가 있다면 계산
                
                weekly_summary.append({
                    '캠페인명': summary['campaign_name'],
                    '주간 광고비': summary['total_spend'],
                    '주간 노출수': summary['total_impressions'],
                    '주간 클릭수': summary['total_clicks'],
                    '주간 전환수': summary['total_conversions'],
                    '평균 CTR': avg_ctr,
                    '평균 CPC': avg_cpc,
                    '데이터 일수': summary['daily_count']
                })
            
            if weekly_summary:
                df = pd.DataFrame(weekly_summary)
                
                # 주간 요약 시트 생성/업데이트
                week_start = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
                sheet_name = f"주간요약_{week_start}"
                
                success = self.sheets_manager.upload_dataframe_to_sheet(
                    df, sheet_name, include_header=True, clear_existing=True
                )
                
                if success:
                    logger.info(f"주간 요약 시트 생성 완료: {sheet_name}")
                
        except Exception as e:
            logger.error(f"주간 요약 시트 생성 실패: {e}")
    
    def setup_schedule(self):
        """스케줄 설정"""
        try:
            schedule_config = self.config.get('schedule_times', {})
            
            # 1시간마다 캠페인 데이터 업데이트
            hourly_interval = schedule_config.get('hourly_update', 1)
            schedule.every(hourly_interval).hours.do(self.collect_campaign_performance_data)
            
            # 일간 리포트 (매일 오전 9시) - 기존 호환성 유지
            daily_time = schedule_config.get('daily_report', '09:00')
            schedule.every().day.at(daily_time).do(self.collect_daily_performance_data)
            
            # 주간 요약 (매주 월요일 오전 10시)
            schedule.every().monday.at("10:00").do(self.generate_weekly_summary)
            
            # 성과 체크 (2시간마다)
            schedule.every(2).hours.do(self._performance_health_check)
            
            logger.info("스케줄이 설정되었습니다.")
            logger.info(f"- 캠페인 데이터 업데이트: {hourly_interval}시간마다")
            logger.info(f"- 일간 리포트: 매일 {daily_time}")
            logger.info("- 주간 요약: 매주 월요일 10:00")
            logger.info("- 성과 체크: 2시간마다")
            
        except Exception as e:
            logger.error(f"스케줄 설정 실패: {e}")
    
    def _performance_health_check(self):
        """성과 상태 체크 (간단한 모니터링)"""
        try:
            logger.info("성과 상태 체크를 수행합니다.")
            
            # 현재 활성 캠페인 상태 확인
            if not self.meta_client:
                self.initialize_clients()
            
            campaigns = self.config.get('campaigns', [])
            active_campaigns = [c for c in campaigns if c.get('active', True)]
            
            logger.info(f"모니터링 중인 활성 캠페인: {len(active_campaigns)}개")
            
            # 간단한 상태 체크 (API 연결 확인 등)
            for campaign_info in active_campaigns[:3]:  # 처음 3개만 체크
                try:
                    campaign_id = campaign_info['campaign_id']
                    adsets = self.meta_client.get_adsets_by_campaign(campaign_id)
                    logger.info(f"캠페인 {campaign_id}: {len(adsets)}개 광고세트 확인")
                except Exception as e:
                    logger.warning(f"캠페인 {campaign_id} 상태 체크 실패: {e}")
            
        except Exception as e:
            logger.error(f"성과 상태 체크 실패: {e}")
    
    def run_scheduler(self):
        """스케줄러 실행"""
        logger.info("성과 추적 스케줄러를 시작합니다.")
        
        try:
            self.initialize_clients()
            self.setup_schedule()
            
            logger.info("스케줄러가 실행 중입니다. Ctrl+C로 중지할 수 있습니다.")
            
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 스케줄 체크
                
        except KeyboardInterrupt:
            logger.info("스케줄러가 사용자에 의해 중지되었습니다.")
        except Exception as e:
            logger.error(f"스케줄러 실행 중 오류: {e}")

def main():
    """메인 함수"""
    scheduler = PerformanceScheduler()
    
    # 예시: 캠페인 추가
    # scheduler.add_campaign_to_monitor('your_campaign_id', 'Campaign Name')
    
    # 스케줄러 실행
    scheduler.run_scheduler()

if __name__ == "__main__":
    main() 