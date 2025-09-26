# 🚀 GitHub Actions 자동화 설정 가이드

GitHub Actions를 사용하여 캠페인 추적을 1시간마다 자동으로 실행하는 방법입니다.

## 📋 설정 단계

### 1. GitHub Repository 생성 및 코드 업로드

```bash
# 현재 프로젝트를 GitHub에 업로드
git init
git add .
git commit -m "Initial commit: 캠페인 추적 시스템"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/meta_dashboard.git
git push -u origin main
```

### 2. GitHub Secrets 설정

GitHub Repository → Settings → Secrets and variables → Actions → New repository secret

다음 Secrets를 추가해주세요:

#### 🔑 Meta API Secrets
- **META_APP_ID**: Meta 앱 ID
- **META_APP_SECRET**: Meta 앱 시크릿
- **META_ACCESS_TOKEN**: Meta 액세스 토큰
- **META_AD_ACCOUNT_ID**: Meta 광고 계정 ID

#### 📊 Google Sheets Secrets
- **GOOGLE_SHEET_ID**: Google 스프레드시트 ID
- **GOOGLE_SERVICE_ACCOUNT_KEY**: Google 서비스 계정 JSON 키 (전체 내용)

### 3. Google 서비스 계정 키 설정

1. Google Cloud Console에서 서비스 계정 생성
2. Google Sheets API 활성화
3. 서비스 계정 키 다운로드 (JSON 파일)
4. JSON 파일 전체 내용을 `GOOGLE_SERVICE_ACCOUNT_KEY` Secret에 추가

예시:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
```

### 4. 스프레드시트 권한 설정

Google 스프레드시트에 서비스 계정 이메일을 편집자로 공유:
1. 스프레드시트 열기
2. 공유 버튼 클릭
3. 서비스 계정 이메일 추가 (예: `your-service-account@your-project.iam.gserviceaccount.com`)
4. 권한을 "편집자"로 설정

## ⚙️ 워크플로우 설정

`.github/workflows/campaign_tracker.yml` 파일이 자동으로 생성되었습니다.

### 실행 스케줄
- **자동 실행**: 매시간 정각 (UTC 기준)
- **수동 실행**: GitHub Actions 탭에서 "Run workflow" 버튼으로 언제든 실행 가능

### 한국 시간 기준 실행 시간
UTC와 한국 시간(KST)은 9시간 차이가 있습니다:
- UTC 00:00 → KST 09:00
- UTC 01:00 → KST 10:00
- UTC 02:00 → KST 11:00
- ...

## 🔍 모니터링 및 확인

### 1. 실행 상태 확인
- GitHub Repository → Actions 탭
- 각 실행의 로그 확인 가능

### 2. 로그 다운로드
- 실행 완료 후 "Artifacts" 섹션에서 로그 파일 다운로드 가능
- 7일간 보관됨

### 3. 실패 시 알림
- 실행 실패 시 GitHub에서 이메일 알림 발송
- Actions 탭에서 실패 원인 확인 가능

## 🛠️ 문제 해결

### 자주 발생하는 문제들

#### 1. Secrets 설정 오류
```
Error: 환경 변수가 설정되지 않았습니다
```
→ GitHub Secrets가 올바르게 설정되었는지 확인

#### 2. Google Sheets 권한 오류
```
Error: Insufficient Permission
```
→ 서비스 계정이 스프레드시트에 편집자로 공유되었는지 확인

#### 3. Meta API 오류
```
Error: Invalid access token
```
→ Meta 액세스 토큰이 유효한지 확인 (토큰은 주기적으로 갱신 필요)

### 수동 테스트

워크플로우 설정 후 수동으로 테스트해보세요:
1. GitHub Repository → Actions 탭
2. "캠페인 추적 자동화" 워크플로우 선택
3. "Run workflow" 버튼 클릭
4. 실행 결과 확인

## 📈 비용 및 제한사항

### GitHub Actions 무료 한도
- **Public Repository**: 무제한 무료
- **Private Repository**: 월 2,000분 무료

### 예상 사용량
- 1회 실행당 약 2-3분 소요
- 1시간마다 실행 시 월 약 1,500분 사용
- Private Repository도 무료 한도 내에서 사용 가능

## 🎯 다음 단계

1. **알림 설정**: Slack이나 Discord 웹훅 추가
2. **데이터 백업**: 정기적으로 데이터 백업 자동화
3. **성과 분석**: 추가 지표 및 알림 조건 설정

## 📞 지원

문제가 발생하면 다음을 확인해주세요:
1. GitHub Actions 실행 로그
2. Secrets 설정 상태
3. Google Sheets 권한
4. Meta API 토큰 유효성

설정 완료 후 첫 번째 수동 실행으로 모든 것이 정상 작동하는지 확인해보세요! 🚀
