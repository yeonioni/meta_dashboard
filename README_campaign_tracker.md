# 캠페인 '[엠아트]250922' 추적 시스템

특정 캠페인 "[엠아트]250922"와 그 하위 광고 세트들의 성과 데이터를 1시간 주기로 수집하여 구글 스프레드시트에 자동 업데이트하는 시스템입니다.

## 주요 기능

- ✅ 특정 캠페인 "[엠아트]250922"만 추적
- ✅ 1시간 주기 자동 데이터 수집 및 업데이트
- ✅ 구글 스프레드시트에 2개 시트 생성:
  - **광고 세트별 데이터**: 각 광고 세트의 성과 지표
  - **일별 데이터**: 날짜별 성과 변화 추이
- ✅ 대시보드 없는 간소화된 시스템
- ✅ 자동 포맷팅 (통화, 퍼센트, 숫자 형식)

## 수집 데이터

### 광고 세트별 데이터
- 광고세트명
- 지출금액 (₩)
- 노출 수
- 도달 수
- 결과 수
- CTR (%)
- CPM (₩)

### 일별 데이터
- 날짜
- 지출금액 (₩)
- 노출 수
- 도달 수
- 결과 수
- CTR (%)
- CPM (₩)

## 설치 및 설정

### 1. 환경 변수 설정

`.env` 파일을 생성하고 다음 정보를 입력하세요:

```env
# Meta Marketing API
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
META_ACCESS_TOKEN=your_access_token
META_AD_ACCOUNT_ID=act_your_account_id

# Google Sheets API
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_SHEET_ID=your_sheet_id
```

### 2. Google Sheets API 설정

1. Google Cloud Console에서 프로젝트 생성
2. Google Sheets API 활성화
3. 서비스 계정 생성 및 JSON 키 다운로드
4. JSON 키 파일을 `credentials.json`으로 저장
5. 구글 스프레드시트를 생성하고 서비스 계정에 편집 권한 부여

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

## 사용법

### 기본 실행 (스케줄러 모드)
```bash
python run_campaign_tracker.py
```
- 1시간 주기로 자동 실행
- Ctrl+C로 중지

### 한 번만 실행
```bash
python run_campaign_tracker.py once
```
- 즉시 데이터 수집 및 업데이트
- 테스트용으로 유용

### 상태 확인
```bash
python run_campaign_tracker.py status
```
- 캠페인 정보 및 연결 상태 확인

### 스케줄러 실행 (명시적)
```bash
python run_campaign_tracker.py schedule
```
- 기본 실행과 동일

## 로그 파일

- `campaign_tracker.log`: 시스템 실행 로그
- 실시간 콘솔 출력도 제공

## 파일 구조

```
meta_dashboard/
├── campaign_tracker.py          # 메인 추적 시스템
├── run_campaign_tracker.py      # 실행 스크립트
├── meta_api_client.py           # Meta API 클라이언트
├── data_processor.py            # 데이터 처리
├── sheets_manager.py            # Google Sheets 관리
├── config.py                    # 설정
├── requirements.txt             # 의존성
├── .env                         # 환경 변수 (생성 필요)
├── credentials.json             # Google API 키 (생성 필요)
└── campaign_tracker.log         # 로그 파일
```

## 주의사항

1. **캠페인 이름**: 정확히 "[엠아트]250922"로 설정된 캠페인만 추적됩니다.
2. **API 제한**: Meta API 호출 제한을 고려하여 1시간 주기로 설정되었습니다.
3. **데이터 범위**: 최근 30일 데이터를 수집합니다.
4. **네트워크**: 안정적인 인터넷 연결이 필요합니다.

## 문제 해결

### 캠페인을 찾을 수 없는 경우
- Meta 광고 관리자에서 캠페인 이름이 정확히 "[엠아트]250922"인지 확인
- 광고 계정 ID가 올바른지 확인

### Google Sheets 업데이트 실패
- 서비스 계정에 스프레드시트 편집 권한이 있는지 확인
- GOOGLE_SHEET_ID가 올바른지 확인

### API 오류
- Meta 액세스 토큰이 유효한지 확인
- API 호출 제한에 걸리지 않았는지 확인

## 지원

문제가 발생하면 로그 파일(`campaign_tracker.log`)을 확인하거나 상태 확인 명령어를 사용하세요.

```bash
python run_campaign_tracker.py status
```
