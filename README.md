# Meta 광고 성과 대시보드

메타 마케팅 API와 연동하여 특정 캠페인 안에 있는 광고 세트들의 성과를 비교하고 일간 성과를 추적하는 대시보드입니다. 분석 결과는 Google Sheets에 자동으로 연동됩니다.

## 🚀 주요 기능

### 📊 성과 분석
- **광고 세트 성과 비교**: 캠페인 내 모든 광고 세트의 성과를 효율성 점수 기준으로 순위화
- **일간 성과 트렌드**: 날짜별 광고비, ROAS, 클릭수, 전환수 변화 추이 분석
- **인사이트 및 추천사항**: AI 기반 성과 분석으로 개선점 자동 도출

### 📈 대시보드 기능
- **실시간 데이터 시각화**: Plotly를 활용한 인터랙티브 차트
- **자동 새로고침**: 설정 가능한 주기로 데이터 자동 업데이트
- **다중 캠페인 지원**: 여러 캠페인을 동시에 모니터링

### 📋 Google Sheets 연동
- **자동 리포트 생성**: 분석 결과를 구조화된 스프레드시트로 자동 생성
- **실시간 동기화**: 성과 데이터의 실시간 업데이트
- **팀 공유**: 이메일 기반 스프레드시트 공유 기능

### ⏰ 자동화 기능
- **일간 성과 추적**: 매일 자동으로 성과 데이터 수집 및 분석
- **성과 알림**: 설정된 임계값 기준으로 성과 이상 알림
- **주간 요약 리포트**: 주간 성과 요약 자동 생성

## 🛠️ 기술 스택

- **Backend**: Python 3.8+
- **API**: Meta Marketing API v19.0 (2025년 8월 기준 최신)
- **Frontend**: Streamlit
- **데이터 처리**: Pandas, NumPy
- **시각화**: Plotly
- **스프레드시트**: Google Sheets API
- **스케줄링**: Schedule
- **로깅**: Python logging

## 📋 사전 요구사항

### Meta Marketing API 설정
1. [Meta for Developers](https://developers.facebook.com/)에서 앱 생성
2. Marketing API 권한 신청 및 승인
3. 다음 권한 필요:
   - `ads_read`
   - `read_insights`
   - `ads_management`

### Google Sheets API 설정
1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. Google Sheets API 및 Google Drive API 활성화
3. 서비스 계정 생성 및 JSON 키 파일 다운로드

## 🚀 설치 및 설정

### 1. 프로젝트 클론
```bash
git clone <repository-url>
cd meta_dashboard
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
`env_example.txt`를 참고하여 `.env` 파일 생성:

```bash
# Meta Marketing API 설정
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_ACCESS_TOKEN=your_meta_access_token
META_AD_ACCOUNT_ID=act_your_ad_account_id

# Google Sheets API 설정
GOOGLE_CREDENTIALS_PATH=path/to/your/credentials.json
GOOGLE_SHEET_ID=your_google_sheet_id
```

### 5. Google Sheets 권한 설정
- 다운로드한 서비스 계정 JSON 파일을 프로젝트 루트에 배치
- 분석 결과를 저장할 Google Sheets를 서비스 계정 이메일과 공유

## 💻 사용법

### 대시보드 실행
```bash
streamlit run dashboard.py
```

브라우저에서 `http://localhost:8501`로 접속하여 대시보드 사용

### 자동화 스케줄러 실행
```bash
python scheduler.py
```

### 개별 모듈 사용 예시

#### Meta API 클라이언트
```python
from meta_api_client import MetaAPIClient

client = MetaAPIClient()
campaigns = client.get_campaigns()
adsets = client.get_adsets_by_campaign('campaign_id')
insights = client.get_adset_insights(['adset_id'], '2025-01-01', '2025-01-31')
```

#### 데이터 처리
```python
from data_processor import DataProcessor

processor = DataProcessor()
processed_data = processor.calculate_performance_metrics(insights_df)
comparison = processor.compare_adsets_performance(processed_data)
trends = processor.analyze_daily_trends(processed_data)
```

#### Google Sheets 연동
```python
from sheets_manager import SheetsManager

sheets = SheetsManager()
sheets.create_automated_report(comparison_data, trend_data, insights)
```

## 📊 대시보드 기능 상세

### 주요 성과 지표
- 총 광고세트 수
- 상위/하위 성과자 평균 ROAS
- ROAS 개선 잠재력

### 성과 분석 차트
1. **상위 10개 광고세트 ROAS**: 막대 차트로 최고 성과 광고세트 시각화
2. **효율성 분석**: 광고비 대비 효율성 점수 산점도
3. **일간 트렌드**: 4개 지표(광고비, ROAS, 클릭수, 전환수)의 시계열 차트

### 인사이트 및 추천사항
- 성과 격차 분석
- CTR 개선 기회 식별
- 예산 최적화 제안
- 요일별 성과 패턴 분석

## 🔄 자동화 스케줄

### 기본 스케줄
- **일간 리포트**: 매일 오전 9시
- **주간 요약**: 매주 월요일 오전 10시
- **성과 체크**: 2시간마다

### 알림 임계값 (기본값)
- ROAS 하락: -15%
- 광고비 증가: +20%
- 전환 감소: -20%

## 📁 프로젝트 구조

```
meta_dashboard/
├── config.py              # 설정 파일
├── meta_api_client.py      # Meta API 클라이언트
├── data_processor.py       # 데이터 처리 및 분석
├── sheets_manager.py       # Google Sheets 연동
├── dashboard.py            # Streamlit 대시보드
├── scheduler.py            # 자동화 스케줄러
├── requirements.txt        # 패키지 의존성
├── env_example.txt         # 환경변수 예시
├── README.md              # 프로젝트 문서
└── daily_data/            # 일간 데이터 저장 폴더
```

## 🔧 설정 옵션

### 스케줄러 설정 (`scheduler_config.json`)
```json
{
  "campaigns": [
    {
      "campaign_id": "campaign_id",
      "campaign_name": "Campaign Name",
      "active": true
    }
  ],
  "alert_thresholds": {
    "roas_decline_threshold": -15,
    "spend_increase_threshold": 20,
    "conversion_decline_threshold": -20
  },
  "schedule_times": {
    "daily_report": "09:00",
    "weekly_summary": "monday 10:00"
  }
}
```

## 🚨 문제 해결

### 일반적인 오류

#### Meta API 인증 오류
- Access Token 만료 확인
- 앱 권한 설정 확인
- Ad Account ID 형식 확인 (`act_` 접두사 포함)

#### Google Sheets API 오류
- 서비스 계정 JSON 파일 경로 확인
- 스프레드시트 공유 권한 확인
- API 할당량 초과 여부 확인

#### 데이터 로드 오류
- 캠페인 ID 유효성 확인
- 날짜 범위 설정 확인
- 네트워크 연결 상태 확인

### 로그 확인
```bash
# 스케줄러 로그
tail -f scheduler.log

# 대시보드 로그
# Streamlit 터미널 출력 확인
```

## 📈 성능 최적화

### 데이터 캐싱
- Streamlit 캐시 활용으로 API 호출 최소화
- 캠페인 데이터: 1시간 캐시
- 성과 데이터: 30분 캐시

### API 호출 최적화
- 배치 요청으로 API 호출 수 감소
- 에러 처리 및 재시도 로직 구현
- Rate Limit 준수

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해 주세요.

---

**Meta 광고 성과 대시보드** - 2025년 8월 기준 최신 API 사용 