import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.exceptions import FacebookRequestError
from config import *

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetaAPIClient:
    """메타 마케팅 API 클라이언트"""
    
    def __init__(self):
        """API 클라이언트 초기화"""
        try:
            FacebookAdsApi.init(META_APP_ID, META_APP_SECRET, META_ACCESS_TOKEN)
            self.ad_account = AdAccount(META_AD_ACCOUNT_ID)
            logger.info("Meta API 클라이언트가 성공적으로 초기화되었습니다.")
        except Exception as e:
            logger.error(f"Meta API 초기화 실패: {e}")
            raise
    
    def _handle_rate_limit_error(self, error: FacebookRequestError, retry_count: int = 0, max_retries: int = 3):
        """API 호출 제한 에러 처리"""
        if hasattr(error, '_api_error_code') and error._api_error_code == 17:
            # 에러 코드 17: User request limit reached
            if retry_count < max_retries:
                # 지수 백오프: 2^retry_count * 60초 대기
                wait_time = (2 ** retry_count) * 60
                logger.warning(f"API 호출 제한 도달. {wait_time}초 후 재시도 ({retry_count + 1}/{max_retries})")
                time.sleep(wait_time)
                return True
            else:
                logger.error("최대 재시도 횟수 초과. API 호출 제한이 해제될 때까지 기다려주세요.")
                return False
        return False
    
    def _safe_api_call(self, api_func, *args, **kwargs):
        """안전한 API 호출 (재시도 로직 포함)"""
        max_retries = 3
        for retry_count in range(max_retries + 1):
            try:
                return api_func(*args, **kwargs)
            except FacebookRequestError as e:
                if self._handle_rate_limit_error(e, retry_count, max_retries):
                    continue
                else:
                    raise e
            except Exception as e:
                logger.error(f"API 호출 중 예상치 못한 오류: {e}")
                raise e
        
        # 모든 재시도 실패
        raise Exception("API 호출 제한으로 인해 요청을 완료할 수 없습니다. 나중에 다시 시도해주세요.")
    
    def get_campaigns(self, limit: int = 100) -> List[Dict]:
        """캠페인 목록 조회"""
        def _get_campaigns_api():
            return self.ad_account.get_campaigns(
                fields=[
                    Campaign.Field.id,
                    Campaign.Field.name,
                    Campaign.Field.status,
                    Campaign.Field.objective,
                    Campaign.Field.created_time,
                    Campaign.Field.updated_time
                ],
                params={'limit': limit}
            )
        
        try:
            campaigns = self._safe_api_call(_get_campaigns_api)
            
            campaign_list = []
            for campaign in campaigns:
                campaign_list.append({
                    'campaign_id': campaign.get('id'),
                    'campaign_name': campaign.get('name'),
                    'status': campaign.get('status'),
                    'objective': campaign.get('objective'),
                    'created_time': campaign.get('created_time'),
                    'updated_time': campaign.get('updated_time')
                })
            
            logger.info(f"{len(campaign_list)}개의 캠페인을 조회했습니다.")
            return campaign_list
            
        except Exception as e:
            logger.error(f"캠페인 조회 실패: {e}")
            return []
    
    def get_adsets_by_campaign(self, campaign_id: str) -> List[Dict]:
        """특정 캠페인의 광고 세트 목록 조회"""
        def _get_adsets_api():
            campaign = Campaign(campaign_id)
            return campaign.get_ad_sets(
                fields=[
                    AdSet.Field.id,
                    AdSet.Field.name,
                    AdSet.Field.status,
                    AdSet.Field.campaign_id,
                    AdSet.Field.created_time,
                    AdSet.Field.updated_time,
                    AdSet.Field.daily_budget,
                    AdSet.Field.lifetime_budget,
                    AdSet.Field.targeting
                ]
            )
        
        try:
            adsets = self._safe_api_call(_get_adsets_api)
            
            adset_list = []
            for adset in adsets:
                adset_list.append({
                    'adset_id': adset.get('id'),
                    'adset_name': adset.get('name'),
                    'campaign_id': adset.get('campaign_id'),
                    'status': adset.get('status'),
                    'created_time': adset.get('created_time'),
                    'updated_time': adset.get('updated_time'),
                    'daily_budget': adset.get('daily_budget'),
                    'lifetime_budget': adset.get('lifetime_budget')
                })
            
            logger.info(f"캠페인 {campaign_id}에서 {len(adset_list)}개의 광고 세트를 조회했습니다.")
            return adset_list
            
        except Exception as e:
            logger.error(f"광고 세트 조회 실패: {e}")
            return []
    
    def get_adset_insights(self, 
                          adset_ids: List[str], 
                          date_from: str, 
                          date_to: str,
                          fields: Optional[List[str]] = None) -> pd.DataFrame:
        """광고 세트 성과 데이터 조회"""
        if fields is None:
            fields = DEFAULT_FIELDS
        
        try:
            # 사용자 요청 데이터: 노출, 도달, 결과, 지출금액, CTR, CPM
            insights_fields = [
                AdsInsights.Field.campaign_id,
                AdsInsights.Field.campaign_name,
                AdsInsights.Field.adset_id,
                AdsInsights.Field.adset_name,
                AdsInsights.Field.impressions,  # 노출
                AdsInsights.Field.reach,        # 도달
                AdsInsights.Field.spend,        # 지출금액
                AdsInsights.Field.ctr,          # CTR
                AdsInsights.Field.cpm,          # CPM
                'actions'  # 결과 (전환/액션)
            ]
            
            all_insights = []
            
            for adset_id in adset_ids:
                try:
                    # API 호출 간 지연 추가
                    time.sleep(REQUEST_DELAY)
                    
                    def _get_insights_api():
                        adset = AdSet(adset_id)
                        return adset.get_insights(
                            fields=insights_fields,
                            params={
                                'time_range': {
                                    'since': date_from,
                                    'until': date_to
                                },
                                'level': 'adset',
                                'time_increment': 1  # 일별 데이터 (1일 단위)
                            }
                        )
                    
                    insights = self._safe_api_call(_get_insights_api)
                    
                    for insight in insights:
                        insight_data = {
                            'date': insight.get('date_start'),
                            'campaign_id': insight.get('campaign_id'),
                            'campaign_name': insight.get('campaign_name'),
                            'adset_id': insight.get('adset_id'),
                            'adset_name': insight.get('adset_name'),
                            'impressions': int(insight.get('impressions', 0)),  # 노출
                            'reach': int(insight.get('reach', 0)),              # 도달
                            'spend': float(insight.get('spend', 0)),            # 지출금액
                            'ctr': float(insight.get('ctr', 0)),                # CTR
                            'cpm': float(insight.get('cpm', 0))                 # CPM
                        }
                        
                        # 액션 데이터 처리 (actions)
                        actions = insight.get('actions', [])
                        link_clicks = 0
                        landing_page_views = 0
                        
                        if actions:
                            for action in actions:
                                action_type = action.get('action_type')
                                value = float(action.get('value', 0))
                                
                                if action_type == 'link_click':
                                    link_clicks += value
                                elif action_type == 'landing_page_view':
                                    landing_page_views += value
                        
                        insight_data['link_clicks'] = link_clicks
                        insight_data['landing_page_views'] = landing_page_views
                        
                        all_insights.append(insight_data)
                        
                except Exception as e:
                    logger.warning(f"광고 세트 {adset_id} 성과 데이터 조회 실패: {e}")
                    continue
            
            df = pd.DataFrame(all_insights)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values(['date', 'adset_name'])
            
            logger.info(f"{len(all_insights)}개의 성과 데이터를 조회했습니다.")
            return df
            
        except Exception as e:
            logger.error(f"성과 데이터 조회 실패: {e}")
            return pd.DataFrame()
    
    def get_campaign_performance_summary(self, campaign_id: str, days: int = 30) -> Dict:
        """캠페인 성과 요약 데이터"""
        try:
            # 날짜 범위 설정
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            date_from = start_date.strftime('%Y-%m-%d')
            date_to = end_date.strftime('%Y-%m-%d')
            
            # 광고 세트 목록 조회
            adsets = self.get_adsets_by_campaign(campaign_id)
            if not adsets:
                return {}
            
            adset_ids = [adset['adset_id'] for adset in adsets]
            
            # 성과 데이터 조회
            insights_df = self.get_adset_insights(adset_ids, date_from, date_to)
            
            if insights_df.empty:
                return {}
            
            # 캠페인 전체 요약
            campaign_summary = {
                'campaign_id': campaign_id,
                'total_spend': insights_df['spend'].sum(),
                'total_impressions': insights_df['impressions'].sum(),
                'total_clicks': insights_df['clicks'].sum(),
                'total_conversions': insights_df['conversions'].sum(),
                'avg_ctr': insights_df['ctr'].mean(),
                'avg_cpc': insights_df['cpc'].mean(),
                'avg_cpm': insights_df['cpm'].mean(),
                'avg_roas': insights_df['roas'].mean(),
                'adset_count': len(adset_ids),
                'date_range': f"{date_from} ~ {date_to}"
            }
            
            # 광고 세트별 성과 순위
            adset_performance = insights_df.groupby(['adset_id', 'adset_name']).agg({
                'spend': 'sum',
                'impressions': 'sum',
                'clicks': 'sum',
                'conversions': 'sum',
                'ctr': 'mean',
                'cpc': 'mean',
                'cpm': 'mean',
                'roas': 'mean'
            }).reset_index()
            
            # 성과 순위 (ROAS 기준)
            adset_performance = adset_performance.sort_values('roas', ascending=False)
            campaign_summary['top_adsets'] = adset_performance.head(10).to_dict('records')
            
            return campaign_summary
            
        except Exception as e:
            logger.error(f"캠페인 성과 요약 조회 실패: {e}")
            return {}
    
    def get_daily_performance_trend(self, campaign_id: str, days: int = 30) -> pd.DataFrame:
        """일간 성과 트렌드 데이터"""
        try:
            # 날짜 범위 설정
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            date_from = start_date.strftime('%Y-%m-%d')
            date_to = end_date.strftime('%Y-%m-%d')
            
            # 광고 세트 목록 조회
            adsets = self.get_adsets_by_campaign(campaign_id)
            if not adsets:
                return pd.DataFrame()
            
            adset_ids = [adset['adset_id'] for adset in adsets]
            
            # 일별 성과 데이터 조회
            insights_df = self.get_adset_insights(adset_ids, date_from, date_to)
            
            if insights_df.empty:
                return pd.DataFrame()
            
            # 일별 집계
            daily_trend = insights_df.groupby('date').agg({
                'spend': 'sum',
                'impressions': 'sum',
                'clicks': 'sum',
                'conversions': 'sum',
                'reach': 'sum'
            }).reset_index()
            
            # 계산된 지표 추가
            daily_trend['ctr'] = (daily_trend['clicks'] / daily_trend['impressions'] * 100).round(2)
            daily_trend['cpc'] = (daily_trend['spend'] / daily_trend['clicks']).round(2)
            daily_trend['cpm'] = (daily_trend['spend'] / daily_trend['impressions'] * 1000).round(2)
            daily_trend['conversion_rate'] = (daily_trend['conversions'] / daily_trend['clicks'] * 100).round(2)
            
            # 무한대 및 NaN 값 처리
            daily_trend = daily_trend.replace([float('inf'), -float('inf')], 0)
            daily_trend = daily_trend.fillna(0)
            
            return daily_trend.sort_values('date')
            
        except Exception as e:
            logger.error(f"일간 성과 트렌드 조회 실패: {e}")
            return pd.DataFrame() 