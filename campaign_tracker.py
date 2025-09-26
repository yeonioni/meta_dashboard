#!/usr/bin/env python3
"""
캠페인 '[엠아트]250922' 전용 추적 시스템

이 스크립트는 특정 캠페인과 그 하위 광고 세트들의 성과 데이터를 
1시간 주기로 수집하여 구글 스프레드시트에 업데이트합니다.

- 광고 세트별 데이터: 각 광고 세트의 성과 지표
- 일별 데이터: 날짜별 성과 변화 추이

대시보드 없이 스프레드시트만 업데이트하는 간소화된 시스템입니다.
"""

import logging
import time
import schedule
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd

from meta_api_client import MetaAPIClient
from data_processor import DataProcessor
from sheets_manager import SheetsManager
from config import *

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('campaign_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CampaignTracker:
    """캠페인 '[엠아트]250922' 전용 추적 클래스"""
    
    def __init__(self):
        self.target_campaign_name = "[엠아트]250922"
        self.meta_client = None
        self.data_processor = DataProcessor()
        self.sheets_manager = None
        self.target_campaign_id = None
        
    def initialize(self):
        """클라이언트 초기화"""
        try:
            logger.info("캠페인 추적 시스템을 초기화합니다...")
            
            # Meta API 클라이언트 초기화
            self.meta_client = MetaAPIClient()
            logger.info("Meta API 클라이언트 초기화 완료")
            
            # Google Sheets 관리자 초기화
            self.sheets_manager = SheetsManager()
            logger.info("Google Sheets 관리자 초기화 완료")
            
            # 타겟 캠페인 ID 찾기
            self._find_target_campaign()
            
            logger.info("캠페인 추적 시스템 초기화 완료")
            
        except Exception as e:
            logger.error(f"초기화 실패: {e}")
            raise
    
    def _find_target_campaign(self):
        """타겟 캠페인 '[엠아트]250922' 찾기"""
        try:
            logger.info(f"캠페인 '{self.target_campaign_name}' 검색 중...")
            
            campaigns = self.meta_client.get_campaigns()
            self.target_campaign_id = self.data_processor.filter_campaign_data(campaigns)
            
            if self.target_campaign_id:
                logger.info(f"타겟 캠페인을 찾았습니다: {self.target_campaign_id}")
            else:
                raise Exception(f"캠페인 '{self.target_campaign_name}'을 찾을 수 없습니다.")
                
        except Exception as e:
            logger.error(f"타겟 캠페인 검색 실패: {e}")
            raise
    
    def collect_and_update_data(self):
        """데이터 수집 및 스프레드시트 업데이트"""
        logger.info(f"캠페인 '{self.target_campaign_name}' 데이터 수집을 시작합니다...")
        
        try:
            # 광고 세트 목록 조회
            adsets = self.meta_client.get_adsets_by_campaign(self.target_campaign_id)
            if not adsets:
                logger.warning("광고 세트가 없습니다.")
                return
            
            logger.info(f"{len(adsets)}개의 광고 세트를 발견했습니다.")
            adset_ids = [adset['adset_id'] for adset in adsets]
            
            # 최근 30일 데이터 수집
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            date_from = start_date.strftime('%Y-%m-%d')
            date_to = end_date.strftime('%Y-%m-%d')
            
            logger.info(f"데이터 수집 기간: {date_from} ~ {date_to}")
            
            # 성과 데이터 조회
            insights_df = self.meta_client.get_adset_insights(
                adset_ids, date_from, date_to
            )
            
            if insights_df.empty:
                logger.warning("수집된 성과 데이터가 없습니다.")
                return
            
            logger.info(f"{len(insights_df)}건의 성과 데이터를 수집했습니다.")
            
            # 데이터 처리
            insights_df = self.data_processor.calculate_performance_metrics(insights_df)
            
            # 1. 광고 세트별 데이터 집계
            adset_data = self._aggregate_adset_data(insights_df)
            logger.info(f"광고 세트별 데이터 집계 완료: {len(adset_data)}개")
            
            # 2. 일별 데이터 집계
            daily_data = self._aggregate_daily_data(insights_df)
            logger.info(f"일별 데이터 집계 완료: {len(daily_data)}일")
            
            # 3. Google Sheets 업데이트
            self._update_sheets(adset_data, daily_data)
            
            logger.info("데이터 수집 및 업데이트 완료")
            
        except Exception as e:
            logger.error(f"데이터 수집 및 업데이트 실패: {e}")
    
    def _aggregate_adset_data(self, insights_df: pd.DataFrame) -> pd.DataFrame:
        """광고 세트별 데이터 집계"""
        try:
            # 광고 세트별로 최근 30일 데이터 합계/평균 계산
            adset_data = insights_df.groupby(['adset_id', 'adset_name']).agg({
                'spend': 'sum',                    # 지출금액 합계
                'impressions': 'sum',              # 노출 합계
                'reach': 'sum',                    # 도달 합계
                'link_clicks': 'sum',              # 링크클릭 합계
                'landing_page_views': 'sum',       # 랜딩페이지조회 합계
                'ctr': 'mean',                     # CTR 평균
                'cpm': 'mean'                      # CPM 평균
            }).reset_index()
            
            # 소수점 정리
            adset_data['ctr'] = adset_data['ctr'].round(2)
            adset_data['cpm'] = adset_data['cpm'].round(2)
            
            # 성과 순으로 정렬 (지출금액 기준)
            adset_data = adset_data.sort_values('spend', ascending=False)
            
            return adset_data
            
        except Exception as e:
            logger.error(f"광고 세트별 데이터 집계 실패: {e}")
            return pd.DataFrame()
    
    def _aggregate_daily_data(self, insights_df: pd.DataFrame) -> pd.DataFrame:
        """일별 데이터 집계"""
        try:
            # 날짜별로 모든 광고 세트 데이터 합계/평균 계산
            daily_data = insights_df.groupby('date').agg({
                'spend': 'sum',                    # 지출금액 합계
                'impressions': 'sum',              # 노출 합계
                'reach': 'sum',                    # 도달 합계
                'link_clicks': 'sum',              # 링크클릭 합계
                'landing_page_views': 'sum',       # 랜딩페이지조회 합계
                'ctr': 'mean',                     # CTR 평균
                'cpm': 'mean'                      # CPM 평균
            }).reset_index()
            
            # 소수점 정리
            daily_data['ctr'] = daily_data['ctr'].round(2)
            daily_data['cpm'] = daily_data['cpm'].round(2)
            
            # 날짜 순으로 정렬
            daily_data = daily_data.sort_values('date')
            
            return daily_data
            
        except Exception as e:
            logger.error(f"일별 데이터 집계 실패: {e}")
            return pd.DataFrame()
    
    def _update_sheets(self, adset_data: pd.DataFrame, daily_data: pd.DataFrame):
        """Google Sheets 업데이트"""
        try:
            logger.info("Google Sheets 업데이트를 시작합니다...")
            
            # 데이터 준비
            sheets_data = self.data_processor.prepare_sheets_data_for_campaign(
                adset_data, daily_data
            )
            
            if not sheets_data:
                logger.warning("업데이트할 데이터가 없습니다.")
                return
            
            # 시트 업데이트
            results = self.sheets_manager.upload_campaign_data(sheets_data)
            
            # 포맷팅 적용
            self.sheets_manager.add_campaign_data_formatting()
            
            # 결과 확인
            successful_updates = sum(results.values())
            total_updates = len(results)
            
            if successful_updates > 0:
                logger.info(f"Google Sheets 업데이트 완료: {successful_updates}/{total_updates} 시트")
                logger.info(f"스프레드시트 URL: {self.sheets_manager.get_spreadsheet_url()}")
            else:
                logger.warning("Google Sheets 업데이트에 실패했습니다.")
                
        except Exception as e:
            logger.error(f"Google Sheets 업데이트 실패: {e}")
    
    def run_once(self):
        """한 번만 실행 (GitHub Actions 최적화)"""
        try:
            logger.info("=== 캠페인 추적 단일 실행 시작 ===")
            logger.info(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 초기화
            logger.info("시스템 초기화 중...")
            self.initialize()
            
            # 데이터 수집 및 업데이트
            logger.info("데이터 수집 및 업데이트 시작...")
            self.collect_and_update_data()
            
            # 성공 메시지
            logger.info("✅ 단일 실행 완료")
            logger.info(f"스프레드시트 URL: {self.sheets_manager.get_spreadsheet_url() if self.sheets_manager else 'N/A'}")
            logger.info("=== 캠페인 추적 단일 실행 종료 ===")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 단일 실행 실패: {e}")
            logger.error("상세 오류 정보:", exc_info=True)
            return False
    
    def setup_schedule(self):
        """1시간 주기 스케줄 설정"""
        try:
            # 1시간마다 데이터 수집 및 업데이트
            schedule.every(1).hours.do(self.collect_and_update_data)
            
            logger.info("스케줄이 설정되었습니다.")
            logger.info("- 캠페인 데이터 업데이트: 1시간마다")
            logger.info(f"- 타겟 캠페인: {self.target_campaign_name}")
            logger.info("- 업데이트 시트: '광고 세트별 데이터', '일별 데이터'")
            
        except Exception as e:
            logger.error(f"스케줄 설정 실패: {e}")
            raise
    
    def run_scheduler(self):
        """스케줄러 실행"""
        try:
            logger.info("캠페인 추적 스케줄러를 시작합니다...")
            
            # 초기화
            self.initialize()
            
            # 첫 번째 데이터 수집 (즉시 실행)
            logger.info("초기 데이터 수집을 시작합니다...")
            self.collect_and_update_data()
            
            # 스케줄 설정
            self.setup_schedule()
            
            logger.info("스케줄러가 실행 중입니다. Ctrl+C로 중지할 수 있습니다.")
            
            # 스케줄 실행
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 스케줄 체크
                
        except KeyboardInterrupt:
            logger.info("스케줄러가 사용자에 의해 중지되었습니다.")
        except Exception as e:
            logger.error(f"스케줄러 실행 중 오류: {e}")
    
    def get_status(self) -> Dict:
        """현재 상태 정보 반환"""
        try:
            if not self.target_campaign_id:
                return {"status": "not_initialized", "campaign": self.target_campaign_name}
            
            # 광고 세트 개수 확인
            adsets = self.meta_client.get_adsets_by_campaign(self.target_campaign_id)
            adset_count = len(adsets) if adsets else 0
            
            return {
                "status": "ready",
                "campaign_name": self.target_campaign_name,
                "campaign_id": self.target_campaign_id,
                "adset_count": adset_count,
                "sheets_url": self.sheets_manager.get_spreadsheet_url() if self.sheets_manager else None,
                "last_update": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}

def main():
    """메인 함수"""
    import sys
    
    tracker = CampaignTracker()
    
    # 명령행 인수 확인
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "once":
            # 한 번만 실행
            logger.info("단일 실행 모드")
            success = tracker.run_once()
            sys.exit(0 if success else 1)  # GitHub Actions에서 성공/실패 상태 전달
            
        elif command == "status":
            # 상태 확인
            tracker.initialize()
            status = tracker.get_status()
            print(f"상태: {status}")
            
        elif command == "schedule":
            # 스케줄러 실행
            logger.info("스케줄러 모드")
            tracker.run_scheduler()
            
        else:
            print("사용법:")
            print("  python campaign_tracker.py once      # 한 번만 실행")
            print("  python campaign_tracker.py status    # 상태 확인")
            print("  python campaign_tracker.py schedule  # 스케줄러 실행")
    else:
        # 기본값: 스케줄러 실행
        logger.info("기본 모드: 스케줄러 실행")
        tracker.run_scheduler()

if __name__ == "__main__":
    main()
