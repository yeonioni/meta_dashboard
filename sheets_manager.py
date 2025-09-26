import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from config import GOOGLE_CREDENTIALS_PATH, GOOGLE_SHEET_ID

logger = logging.getLogger(__name__)

class SheetsManager:
    """Google Sheets 연동 및 데이터 관리 클래스"""
    
    def __init__(self, credentials_path: str = GOOGLE_CREDENTIALS_PATH, sheet_id: str = GOOGLE_SHEET_ID):
        """Sheets Manager 초기화"""
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self.client = None
        self.spreadsheet = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Google Sheets API 클라이언트 초기화"""
        try:
            # 서비스 계정 인증
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # 환경 변수에서 서비스 계정 키 확인 (GitHub Actions용)
            service_account_key = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
            
            if service_account_key:
                # 환경 변수에서 JSON 키 로드 (GitHub Actions)
                service_account_info = json.loads(service_account_key)
                credentials = Credentials.from_service_account_info(
                    service_account_info, scopes=scopes
                )
                logger.info("환경 변수에서 Google 서비스 계정 키를 로드했습니다.")
            else:
                # 파일에서 키 로드 (로컬 환경)
                credentials = Credentials.from_service_account_file(
                    self.credentials_path, scopes=scopes
                )
                logger.info(f"파일에서 Google 서비스 계정 키를 로드했습니다: {self.credentials_path}")
            
            self.client = gspread.authorize(credentials)
            
            # 스프레드시트 열기 또는 생성
            try:
                self.spreadsheet = self.client.open_by_key(self.sheet_id)
                logger.info(f"기존 스프레드시트에 연결되었습니다: {self.spreadsheet.title}")
            except gspread.SpreadsheetNotFound:
                logger.warning("지정된 스프레드시트를 찾을 수 없습니다. 새로 생성합니다.")
                self.spreadsheet = self.create_new_spreadsheet()
            
        except Exception as e:
            logger.error(f"Google Sheets 클라이언트 초기화 실패: {e}")
            raise
    
    def create_new_spreadsheet(self, title: str = None) -> gspread.Spreadsheet:
        """새 스프레드시트 생성"""
        try:
            if title is None:
                title = f"Meta 광고 성과 대시보드 - {datetime.now().strftime('%Y%m%d_%H%M')}"
            
            spreadsheet = self.client.create(title)
            logger.info(f"새 스프레드시트가 생성되었습니다: {spreadsheet.title}")
            logger.info(f"스프레드시트 URL: {spreadsheet.url}")
            
            return spreadsheet
            
        except Exception as e:
            logger.error(f"스프레드시트 생성 실패: {e}")
            raise
    
    def get_or_create_worksheet(self, sheet_name: str, rows: int = 1000, cols: int = 26) -> gspread.Worksheet:
        """워크시트 가져오기 또는 생성"""
        try:
            # 기존 워크시트 확인
            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
                logger.info(f"기존 워크시트를 사용합니다: {sheet_name}")
                return worksheet
            except gspread.WorksheetNotFound:
                # 새 워크시트 생성
                worksheet = self.spreadsheet.add_worksheet(
                    title=sheet_name, rows=rows, cols=cols
                )
                logger.info(f"새 워크시트가 생성되었습니다: {sheet_name}")
                return worksheet
                
        except Exception as e:
            logger.error(f"워크시트 생성/조회 실패: {e}")
            raise
    
    def upload_dataframe_to_sheet(self, 
                                 df: pd.DataFrame, 
                                 sheet_name: str, 
                                 include_header: bool = True,
                                 clear_existing: bool = True) -> bool:
        """DataFrame을 Google Sheets에 업로드"""
        try:
            if df.empty:
                logger.warning(f"빈 DataFrame입니다. {sheet_name} 시트 업로드를 건너뜁니다.")
                return False
            
            # 워크시트 가져오기/생성
            worksheet = self.get_or_create_worksheet(sheet_name)
            
            # 기존 데이터 삭제 (선택사항)
            if clear_existing:
                worksheet.clear()
            
            # 데이터 준비
            if include_header:
                # 헤더와 데이터를 함께 업로드
                values = [df.columns.tolist()] + df.values.tolist()
            else:
                values = df.values.tolist()
            
            # 데이터 타입 변환 (Google Sheets 호환성)
            formatted_values = []
            for row in values:
                formatted_row = []
                for cell in row:
                    if pd.isna(cell):
                        formatted_row.append("")
                    elif isinstance(cell, (int, float)):
                        formatted_row.append(float(cell) if not pd.isna(cell) else 0)
                    else:
                        formatted_row.append(str(cell))
                formatted_values.append(formatted_row)
            
            # 배치 업데이트로 성능 최적화
            worksheet.update(formatted_values, value_input_option='USER_ENTERED')
            
            # 헤더 포맷팅 (첫 번째 행을 굵게)
            if include_header and len(formatted_values) > 0:
                self.format_header_row(worksheet, len(df.columns))
            
            logger.info(f"{sheet_name} 시트에 {len(df)}행 데이터가 업로드되었습니다.")
            return True
            
        except Exception as e:
            logger.error(f"{sheet_name} 시트 업로드 실패: {e}")
            return False
    
    def format_header_row(self, worksheet: gspread.Worksheet, num_cols: int):
        """헤더 행 포맷팅"""
        try:
            # 헤더 행을 굵게 만들고 배경색 설정
            header_range = f"A1:{chr(65 + num_cols - 1)}1"
            
            worksheet.format(header_range, {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
            })
            
            # 열 너비를 130으로 설정
            try:
                worksheet.columns_auto_resize(0, num_cols - 1)
                # 추가적으로 열 너비 설정 시도
                for i in range(num_cols):
                    col_letter = chr(65 + i)  # A, B, C, ...
                    worksheet.update_dimension_property(
                        dimension='COLUMNS',
                        start_index=i,
                        end_index=i,
                        property_name='pixelSize',
                        value=130
                    )
            except:
                # 기본 자동 크기 조정만 수행
                worksheet.columns_auto_resize(0, num_cols - 1)
            
        except Exception as e:
            logger.warning(f"헤더 포맷팅 실패: {e}")
    
    def create_summary_dashboard(self, 
                               comparison_data: Dict, 
                               trend_data: Dict, 
                               insights: List[Dict]) -> bool:
        """요약 대시보드 시트 생성"""
        try:
            worksheet = self.get_or_create_worksheet("📊 대시보드 요약")
            worksheet.clear()
            
            # 대시보드 제목
            current_time = datetime.now().strftime('%Y년 %m월 %d일 %H:%M')
            title_data = [
                [f"Meta 광고 성과 대시보드 - {current_time}"],
                [""],
                ["📈 주요 성과 지표"]
            ]
            
            # 주요 지표 추가
            if comparison_data:
                performance_gap = comparison_data.get('performance_gap', {})
                title_data.extend([
                    ["상위 성과자 평균 ROAS", f"{performance_gap.get('top_avg_roas', 0):.2f}"],
                    ["하위 성과자 평균 ROAS", f"{performance_gap.get('bottom_avg_roas', 0):.2f}"],
                    ["ROAS 개선 잠재력", f"{performance_gap.get('roas_improvement_potential', 0):.2f}"],
                    ["총 광고세트 수", comparison_data.get('total_adsets', 0)]
                ])
            
            title_data.extend([
                [""],
                ["🔍 주요 인사이트"]
            ])
            
            # 인사이트 추가
            for i, insight in enumerate(insights[:5], 1):  # 상위 5개 인사이트만
                priority_emoji = "🔴" if insight['priority'] == 'high' else "🟡" if insight['priority'] == 'medium' else "🟢"
                title_data.extend([
                    [f"{priority_emoji} {insight['title']}"],
                    [insight['description']],
                    [f"💡 {insight['recommendation']}"],
                    [""]
                ])
            
            # 시트 링크 안내
            title_data.extend([
                [""],
                ["📋 상세 데이터 시트"],
                ["• '광고세트 성과 비교' - 광고세트별 상세 성과 데이터"],
                ["• '일간 성과 트렌드' - 날짜별 성과 변화 추이"],
                ["• '요약 통계' - 전체 성과 요약 정보"]
            ])
            
            # 데이터 업로드
            worksheet.update(title_data, value_input_option='USER_ENTERED')
            
            # 제목 포맷팅
            worksheet.format("A1", {
                "textFormat": {"bold": True, "fontSize": 16},
                "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 1.0},
                "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}}
            })
            
            # 섹션 제목 포맷팅
            worksheet.format("A3", {"textFormat": {"bold": True, "fontSize": 14}})
            
            logger.info("대시보드 요약 시트가 생성되었습니다.")
            return True
            
        except Exception as e:
            logger.error(f"대시보드 요약 시트 생성 실패: {e}")
            return False
    
    def upload_campaign_data(self, sheets_data: Dict) -> Dict[str, bool]:
        """특정 캠페인 데이터를 Google Sheets에 업로드"""
        results = {}
        
        try:
            # 1. 광고 세트별 데이터 시트
            if 'adset_performance' in sheets_data:
                results['adset_performance'] = self.upload_dataframe_to_sheet(
                    sheets_data['adset_performance'], 
                    "광고 세트별 데이터"
                )
            
            # 2. 일별 데이터 시트
            if 'daily_trend' in sheets_data:
                results['daily_trend'] = self.upload_dataframe_to_sheet(
                    sheets_data['daily_trend'], 
                    "일별 데이터"
                )
            
            # 성공한 업로드 개수 로그
            successful_uploads = sum(results.values())
            total_uploads = len(results)
            logger.info(f"캠페인 데이터 업로드 완료: {successful_uploads}/{total_uploads} 시트 성공")
            
            return results
            
        except Exception as e:
            logger.error(f"캠페인 데이터 업로드 실패: {e}")
            return results
    
    def upload_all_data(self, sheets_data: Dict, insights: List[Dict] = None) -> Dict[str, bool]:
        """모든 데이터를 Google Sheets에 업로드 (기존 호환성 유지)"""
        results = {}
        
        try:
            # 1. 광고세트 성과 비교 시트
            if 'adset_performance' in sheets_data:
                results['adset_performance'] = self.upload_dataframe_to_sheet(
                    sheets_data['adset_performance'], 
                    "광고세트 성과 비교"
                )
            
            # 2. 일간 성과 트렌드 시트
            if 'daily_trend' in sheets_data:
                results['daily_trend'] = self.upload_dataframe_to_sheet(
                    sheets_data['daily_trend'], 
                    "일간 성과 트렌드"
                )
            
            # 3. 요약 통계 시트
            if 'summary' in sheets_data:
                results['summary'] = self.upload_dataframe_to_sheet(
                    sheets_data['summary'], 
                    "요약 통계"
                )
            
            # 4. 인사이트 시트
            if insights:
                insights_df = pd.DataFrame(insights)
                if not insights_df.empty:
                    # 컬럼명 한글화
                    insights_df.columns = ['유형', '제목', '설명', '추천사항', '우선순위']
                    results['insights'] = self.upload_dataframe_to_sheet(
                        insights_df, 
                        "인사이트 및 추천사항"
                    )
            
            # 성공한 업로드 개수 로그
            successful_uploads = sum(results.values())
            total_uploads = len(results)
            logger.info(f"데이터 업로드 완료: {successful_uploads}/{total_uploads} 시트 성공")
            
            return results
            
        except Exception as e:
            logger.error(f"데이터 업로드 실패: {e}")
            return results
    
    def add_campaign_data_formatting(self):
        """캠페인 데이터 시트 포맷팅 적용"""
        try:
            # 광고 세트별 데이터 시트 포맷팅
            try:
                worksheet = self.spreadsheet.worksheet("광고 세트별 데이터")
                
                # 열 너비 자동 조정 (9개 컬럼)
                worksheet.columns_auto_resize(0, 8)
                
                # 숫자 컬럼에 천 단위 구분자 적용
                money_columns = ["B:B", "H:H"]  # 지출금액, CPM
                for col_range in money_columns:
                    worksheet.format(col_range, {"numberFormat": {"type": "CURRENCY", "pattern": "₩#,##0"}})
                
                # CTR 컬럼 포맷팅 (값을 100으로 나누고 퍼센트 형식 적용)
                worksheet.format("G:G", {"numberFormat": {"type": "PERCENT", "pattern": "0.00%"}})
                
                # 숫자 컬럼 포맷팅
                number_columns = ["C:C", "D:D", "E:E", "F:F"]  # 노출, 도달, 링크클릭, 랜딩페이지조회
                for col_range in number_columns:
                    worksheet.format(col_range, {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}})
                
                # 업데이트 일시 컬럼 포맷팅
                worksheet.format("I:I", {"numberFormat": {"type": "DATE_TIME", "pattern": "yyyy-mm-dd hh:mm:ss"}})
                
            except gspread.WorksheetNotFound:
                pass
            
            # 일별 데이터 시트 포맷팅
            try:
                worksheet = self.spreadsheet.worksheet("일별 데이터")
                
                # 열 너비 자동 조정
                worksheet.columns_auto_resize(0, 7)
                
                # 날짜 컬럼 포맷팅
                worksheet.format("A:A", {"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}})
                
                # 숫자 컬럼에 천 단위 구분자 적용
                money_columns = ["B:B", "H:H"]  # 지출금액, CPM
                for col_range in money_columns:
                    worksheet.format(col_range, {"numberFormat": {"type": "CURRENCY", "pattern": "₩#,##0"}})
                
                # CTR 컬럼 포맷팅 (값을 100으로 나누고 퍼센트 형식 적용)
                worksheet.format("G:G", {"numberFormat": {"type": "PERCENT", "pattern": "0.00%"}})
                
                # 숫자 컬럼 포맷팅
                number_columns = ["C:C", "D:D", "E:E", "F:F"]  # 노출, 도달, 링크클릭, 랜딩페이지조회
                for col_range in number_columns:
                    worksheet.format(col_range, {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}})
                
            except gspread.WorksheetNotFound:
                pass
            
            logger.info("캠페인 데이터 포맷팅이 적용되었습니다.")
            
        except Exception as e:
            logger.warning(f"캠페인 데이터 포맷팅 적용 실패: {e}")
    
    def add_data_validation_and_formatting(self):
        """데이터 검증 및 고급 포맷팅 적용 (기존 호환성 유지)"""
        try:
            # 광고세트 성과 비교 시트 포맷팅
            try:
                worksheet = self.spreadsheet.worksheet("광고세트 성과 비교")
                
                # 숫자 컬럼에 천 단위 구분자 적용
                money_columns = ["B:B", "G:G", "H:H"]  # 광고비, CPC, CPM
                for col_range in money_columns:
                    worksheet.format(col_range, {"numberFormat": {"type": "CURRENCY", "pattern": "₩#,##0"}})
                
                # 퍼센트 컬럼 포맷팅
                percent_columns = ["F:F", "J:J"]  # CTR, 전환율
                for col_range in percent_columns:
                    worksheet.format(col_range, {"numberFormat": {"type": "PERCENT", "pattern": "0.00%"}})
                
                # 조건부 서식 - ROAS 기준
                worksheet.format("I:I", {
                    "conditionalFormatRules": [{
                        "ranges": [{"sheetId": worksheet.id, "startColumnIndex": 8, "endColumnIndex": 9}],
                        "gradientRule": {
                            "minpoint": {"color": {"red": 1, "green": 0.4, "blue": 0.4}, "type": "MIN"},
                            "maxpoint": {"color": {"red": 0.4, "green": 1, "blue": 0.4}, "type": "MAX"}
                        }
                    }]
                })
                
            except gspread.WorksheetNotFound:
                pass
            
            # 일간 성과 트렌드 시트 포맷팅
            try:
                worksheet = self.spreadsheet.worksheet("일간 성과 트렌드")
                
                # 날짜 컬럼 포맷팅
                worksheet.format("A:A", {"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}})
                
                # 차트 생성을 위한 데이터 범위 설정 (수동으로 차트 생성 필요)
                
            except gspread.WorksheetNotFound:
                pass
            
            logger.info("고급 포맷팅이 적용되었습니다.")
            
        except Exception as e:
            logger.warning(f"고급 포맷팅 적용 실패: {e}")
    
    def share_spreadsheet(self, email_addresses: List[str], role: str = 'reader'):
        """스프레드시트 공유"""
        try:
            for email in email_addresses:
                self.spreadsheet.share(email, perm_type='user', role=role)
                logger.info(f"스프레드시트가 {email}에게 {role} 권한으로 공유되었습니다.")
                
        except Exception as e:
            logger.error(f"스프레드시트 공유 실패: {e}")
    
    def get_spreadsheet_url(self) -> str:
        """스프레드시트 URL 반환"""
        if self.spreadsheet:
            return self.spreadsheet.url
        return ""
    
    def create_automated_report(self, 
                              comparison_data: Dict, 
                              trend_data: Dict, 
                              insights: List[Dict]) -> bool:
        """자동화된 종합 리포트 생성"""
        try:
            # 1. 데이터 시트들 생성
            from data_processor import DataProcessor
            processor = DataProcessor()
            sheets_data = processor.prepare_sheets_data(comparison_data, trend_data)
            
            # 2. 모든 데이터 업로드
            upload_results = self.upload_all_data(sheets_data, insights)
            
            # 3. 대시보드 요약 시트 생성
            dashboard_created = self.create_summary_dashboard(comparison_data, trend_data, insights)
            
            # 4. 고급 포맷팅 적용
            self.add_data_validation_and_formatting()
            
            # 성공 여부 확인
            successful_uploads = sum(upload_results.values())
            total_expected = len(sheets_data) + (1 if insights else 0)
            
            success = successful_uploads >= total_expected and dashboard_created
            
            if success:
                logger.info("자동화된 리포트가 성공적으로 생성되었습니다.")
                logger.info(f"스프레드시트 URL: {self.get_spreadsheet_url()}")
            else:
                logger.warning("리포트 생성 중 일부 오류가 발생했습니다.")
            
            return success
            
        except Exception as e:
            logger.error(f"자동화된 리포트 생성 실패: {e}")
            return False 