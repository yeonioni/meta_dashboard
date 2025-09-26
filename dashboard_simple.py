import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import logging
from typing import Dict, List

from meta_api_client import MetaAPIClient
from data_processor import DataProcessor

# 페이지 설정
st.set_page_config(
    page_title="Meta 광고 성과 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 사이드바 설정
st.sidebar.title("🎯 Meta 광고 성과 대시보드")
st.sidebar.markdown("---")

# 캐시된 데이터 로드 함수들
@st.cache_data(ttl=3600)  # 1시간 캐시
def load_campaigns():
    """캠페인 목록 로드"""
    try:
        client = MetaAPIClient()
        campaigns = client.get_campaigns()
        return campaigns
    except Exception as e:
        st.error(f"캠페인 로드 실패: {e}")
        return []

@st.cache_data(ttl=1800)  # 30분 캐시
def load_campaign_data(campaign_id: str, days: int):
    """캠페인 데이터 로드"""
    try:
        client = MetaAPIClient()
        processor = DataProcessor()
        
        # 광고 세트 목록 조회
        adsets = client.get_adsets_by_campaign(campaign_id)
        if not adsets:
            return None, None, None
        
        adset_ids = [adset['adset_id'] for adset in adsets]
        
        # 날짜 범위 설정
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        date_from = start_date.strftime('%Y-%m-%d')
        date_to = end_date.strftime('%Y-%m-%d')
        
        # 성과 데이터 조회
        insights_df = client.get_adset_insights(adset_ids, date_from, date_to)
        
        if insights_df.empty:
            return None, None, None
        
        # 데이터 처리 및 분석
        insights_df = processor.calculate_performance_metrics(insights_df)
        comparison_data = processor.compare_adsets_performance(insights_df)
        trend_data = processor.analyze_daily_trends(insights_df)
        
        return insights_df, comparison_data, trend_data
        
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None, None, None

def create_adset_performance_chart(comparison_data: Dict):
    """광고세트별 성과 차트 생성"""
    if not comparison_data or 'adset_rankings' not in comparison_data:
        return None
    
    df = pd.DataFrame(comparison_data['adset_rankings'])
    
    # 상위 10개 광고세트
    top_10 = df.head(10)
    
    # 서브플롯 생성
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('CTR (%)', 'CPM', '결과 수', '지출금액'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # CTR 차트
    fig.add_trace(
        go.Bar(x=top_10['adset_name'], y=top_10['ctr'], 
               name='CTR', marker_color='lightblue'),
        row=1, col=1
    )
    
    # CPM 차트
    fig.add_trace(
        go.Bar(x=top_10['adset_name'], y=top_10['cpm'], 
               name='CPM', marker_color='lightcoral'),
        row=1, col=2
    )
    
    # 결과 수 차트
    fig.add_trace(
        go.Bar(x=top_10['adset_name'], y=top_10['results'], 
               name='결과', marker_color='lightgreen'),
        row=2, col=1
    )
    
    # 지출금액 차트
    fig.add_trace(
        go.Bar(x=top_10['adset_name'], y=top_10['spend'], 
               name='지출금액', marker_color='gold'),
        row=2, col=2
    )
    
    fig.update_layout(
        height=600,
        title_text="상위 10개 광고세트 성과 비교",
        showlegend=False
    )
    
    # x축 레이블 회전
    fig.update_xaxes(tickangle=-45)
    
    return fig

def create_daily_trend_chart(trend_data: Dict):
    """일별 트렌드 차트 생성"""
    if not trend_data or 'daily_data' not in trend_data:
        return None
    
    df = pd.DataFrame(trend_data['daily_data'])
    df['date'] = pd.to_datetime(df['date'])
    
    # 서브플롯 생성
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=('일별 지출금액', '일별 노출수', '일별 도달수', '일별 결과', '일별 CTR', '일별 CPM'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # 지출금액
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['spend'], mode='lines+markers', 
                   name='지출금액', line=dict(color='red')),
        row=1, col=1
    )
    
    # 노출수
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['impressions'], mode='lines+markers', 
                   name='노출수', line=dict(color='blue')),
        row=1, col=2
    )
    
    # 도달수
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['reach'], mode='lines+markers', 
                   name='도달수', line=dict(color='green')),
        row=2, col=1
    )
    
    # 결과
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['results'], mode='lines+markers', 
                   name='결과', line=dict(color='orange')),
        row=2, col=2
    )
    
    # CTR
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['ctr'], mode='lines+markers', 
                   name='CTR', line=dict(color='purple')),
        row=3, col=1
    )
    
    # CPM
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['cpm'], mode='lines+markers', 
                   name='CPM', line=dict(color='brown')),
        row=3, col=2
    )
    
    fig.update_layout(
        height=800,
        title_text="일별 성과 트렌드",
        showlegend=False
    )
    
    return fig

def create_adset_comparison_table(comparison_data: Dict):
    """광고세트 비교 테이블 생성"""
    if not comparison_data or 'adset_rankings' not in comparison_data:
        return None
    
    df = pd.DataFrame(comparison_data['adset_rankings'])
    
    # 필요한 컬럼만 선택하고 이름 변경
    display_df = df[['adset_name', 'impressions', 'reach', 'results', 'spend', 'ctr', 'cpm']].copy()
    display_df.columns = ['광고세트명', '노출수', '도달수', '결과', '지출금액', 'CTR(%)', 'CPM']
    
    # 숫자 포맷팅
    display_df['노출수'] = display_df['노출수'].apply(lambda x: f"{x:,}")
    display_df['도달수'] = display_df['도달수'].apply(lambda x: f"{x:,}")
    display_df['결과'] = display_df['결과'].apply(lambda x: f"{x:,}")
    display_df['지출금액'] = display_df['지출금액'].apply(lambda x: f"₩{x:,.0f}")
    display_df['CTR(%)'] = display_df['CTR(%)'].apply(lambda x: f"{x:.2f}%")
    display_df['CPM'] = display_df['CPM'].apply(lambda x: f"₩{x:,.0f}")
    
    return display_df

def create_daily_data_table(trend_data: Dict):
    """일별 데이터 테이블 생성"""
    if not trend_data or 'daily_data' not in trend_data:
        return None
    
    df = pd.DataFrame(trend_data['daily_data'])
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    
    # 필요한 컬럼만 선택하고 이름 변경
    display_df = df[['date', 'impressions', 'reach', 'results', 'spend', 'ctr', 'cpm']].copy()
    display_df.columns = ['날짜', '노출수', '도달수', '결과', '지출금액', 'CTR(%)', 'CPM']
    
    # 숫자 포맷팅
    display_df['노출수'] = display_df['노출수'].apply(lambda x: f"{x:,}")
    display_df['도달수'] = display_df['도달수'].apply(lambda x: f"{x:,}")
    display_df['결과'] = display_df['결과'].apply(lambda x: f"{x:,}")
    display_df['지출금액'] = display_df['지출금액'].apply(lambda x: f"₩{x:,.0f}")
    display_df['CTR(%)'] = display_df['CTR(%)'].apply(lambda x: f"{x:.2f}%")
    display_df['CPM'] = display_df['CPM'].apply(lambda x: f"₩{x:,.0f}")
    
    return display_df

# 메인 앱
def main():
    st.title("📊 Meta 광고 성과 대시보드")
    st.markdown("---")
    
    # 사이드바 - 캠페인 선택
    campaigns = load_campaigns()
    
    if not campaigns:
        st.error("캠페인을 불러올 수 없습니다.")
        return
    
    campaign_options = {f"{camp['campaign_name']} ({camp['campaign_id']})": camp['campaign_id'] 
                       for camp in campaigns}
    
    selected_campaign_display = st.sidebar.selectbox(
        "📋 캠페인 선택",
        options=list(campaign_options.keys())
    )
    
    selected_campaign_id = campaign_options[selected_campaign_display]
    
    # 날짜 범위 선택
    days_options = {
        "최근 7일": 7,
        "최근 14일": 14,
        "최근 30일": 30,
        "최근 60일": 60
    }
    
    selected_days_display = st.sidebar.selectbox(
        "📅 분석 기간",
        options=list(days_options.keys()),
        index=2  # 기본값: 최근 30일
    )
    
    selected_days = days_options[selected_days_display]
    
    # 데이터 로드
    with st.spinner("데이터를 불러오는 중..."):
        insights_df, comparison_data, trend_data = load_campaign_data(selected_campaign_id, selected_days)
    
    if insights_df is None:
        st.warning("선택한 캠페인에 대한 데이터가 없습니다.")
        return
    
    # 요약 지표
    st.subheader("📈 성과 요약")
    
    total_spend = insights_df['spend'].sum()
    total_impressions = insights_df['impressions'].sum()
    total_reach = insights_df['reach'].sum()
    total_results = insights_df['results'].sum()
    avg_ctr = insights_df['ctr'].mean()
    avg_cpm = insights_df['cpm'].mean()
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("총 지출금액", f"₩{total_spend:,.0f}")
    with col2:
        st.metric("총 노출수", f"{total_impressions:,}")
    with col3:
        st.metric("총 도달수", f"{total_reach:,}")
    with col4:
        st.metric("총 결과", f"{total_results:,}")
    with col5:
        st.metric("평균 CTR", f"{avg_ctr:.2f}%")
    with col6:
        st.metric("평균 CPM", f"₩{avg_cpm:,.0f}")
    
    st.markdown("---")
    
    # 광고세트별 성과 차트
    st.subheader("🎯 광고세트별 성과")
    adset_chart = create_adset_performance_chart(comparison_data)
    if adset_chart:
        st.plotly_chart(adset_chart, width='stretch')
    
    # 일별 트렌드 차트
    st.subheader("📅 일별 성과 트렌드")
    trend_chart = create_daily_trend_chart(trend_data)
    if trend_chart:
        st.plotly_chart(trend_chart, width='stretch')
    
    # 데이터 테이블들
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 광고세트별 데이터")
        adset_table = create_adset_comparison_table(comparison_data)
        if adset_table is not None:
            st.dataframe(adset_table, width='stretch', height=400)
    
    with col2:
        st.subheader("📅 일별 데이터")
        daily_table = create_daily_data_table(trend_data)
        if daily_table is not None:
            st.dataframe(daily_table, width='stretch', height=400)

if __name__ == "__main__":
    main()


