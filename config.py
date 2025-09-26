import os
from dotenv import load_dotenv

load_dotenv()

# Meta Marketing API 설정
META_APP_ID = os.getenv('META_APP_ID')
META_APP_SECRET = os.getenv('META_APP_SECRET')
META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
META_AD_ACCOUNT_ID = os.getenv('META_AD_ACCOUNT_ID')

# Google Sheets API 설정
GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')

# API 설정
API_VERSION = 'v19.0'  # 2025년 8월 기준 최신 버전
BASE_URL = f'https://graph.facebook.com/{API_VERSION}'

# 데이터 수집 설정
DEFAULT_FIELDS = [
    'campaign_id',
    'campaign_name',
    'adset_id',
    'adset_name',
    'impressions',
    'clicks',
    'spend',
    'reach',
    'frequency',
    'ctr',
    'cpc',
    'cpm',
    'cpp',
    'conversions',
    'conversion_rate',
    'cost_per_conversion',
    'roas',
    'video_views',
    'video_view_rate'
]

# 시간 설정
DEFAULT_TIME_RANGE = 30  # 기본 30일
REFRESH_INTERVAL = 3600

# API 호출 제한 설정
MAX_RETRIES = 3  # 최대 재시도 횟수
BASE_WAIT_TIME = 60  # 기본 대기 시간 (초)
REQUEST_DELAY = 1  # 요청 간 지연 시간 (초)  # 1시간마다 새로고침 