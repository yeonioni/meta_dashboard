import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import logging
from typing import Dict, List
import time

from meta_api_client import MetaAPIClient
from data_processor import DataProcessor
from sheets_manager import SheetsManager

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
            return None, None, None, []
        
        adset_ids = [adset['adset_id'] for adset in adsets]
        
        # 날짜 범위 설정
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        date_from = start_date.strftime('%Y-%m-%d')
        date_to = end_date.strftime('%Y-%m-%d')
        
        # 성과 데이터 조회
        insights_df = client.get_adset_insights(adset_ids, date_from, date_to)
        
        if insights_df.empty:
            return None, None, None, []
        
        # 데이터 처리 및 분석
        insights_df = processor.calculate_performance_metrics(insights_df)
        comparison_data = processor.compare_adsets_performance(insights_df)
        trend_data = processor.analyze_daily_trends(insights_df)
        insights = processor.generate_insights_and_recommendations(comparison_data, trend_data)
        
        return insights_df, comparison_data, trend_data, insights
        
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None, None, None, []

def create_performance_overview_charts(comparison_data: Dict):
    """성과 개요 차트 생성"""
    if not comparison_data or 'adset_rankings' not in comparison_data:
        return None, None
    
    df = pd.DataFrame(comparison_data['adset_rankings'])
    
    # 상위 10개 광고세트 ROAS 차트
    top_10 = df.head(10)
    
    fig_roas = px.bar(
        top_10, 
        x='adset_name', 
        y='roas',
        title='상위 10개 광고세트 ROAS',
        color='roas',
        color_continuous_scale='RdYlGn'
    )
    fig_roas.update_layout(xaxis_tickangle=-45, height=400)
    
    # 효율성 점수 vs 광고비 산점도
    fig_efficiency = px.scatter(
        df,
        x='spend',
        y='efficiency_score',
        size='conversions',
        color='roas',
        hover_name='adset_name',
        title='광고세트 효율성 분석 (크기: 전환수, 색상: ROAS)',
        labels={
            'spend': '광고비 (₩)',
            'efficiency_score': '효율성 점수',
            'roas': 'ROAS'
        }
    )
    fig_efficiency.update_layout(height=400)
    
    return fig_roas, fig_efficiency

def create_trend_charts(trend_data: Dict):
    """트렌드 차트 생성"""
    if not trend_data or 'daily_data' not in trend_data:
        return None
    
    df = pd.DataFrame(trend_data['daily_data'])
    df['date'] = pd.to_datetime(df['date'])
    
    # 서브플롯 생성
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('일간 광고비', '일간 ROAS', '일간 클릭수', '일간 전환수'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # 광고비 트렌드
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['spend'], name='광고비', line=dict(color='blue')),
        row=1, col=1
    )
    
    # ROAS 트렌드
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['roas'], name='ROAS', line=dict(color='green')),
        row=1, col=2
    )
    
    # 클릭수 트렌드
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['clicks'], name='클릭수', line=dict(color='orange')),
        row=2, col=1
    )
    
    # 전환수 트렌드
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['conversions'], name='전환수', line=dict(color='red')),
        row=2, col=2
    )
    
    fig.update_layout(height=600, title_text="일간 성과 트렌드", showlegend=False)
    
    return fig

def create_comparison_table(comparison_data: Dict):
    """광고세트 비교 테이블 생성"""
    if not comparison_data or 'adset_rankings' not in comparison_data:
        return None
    
    df = pd.DataFrame(comparison_data['adset_rankings'])
    
    # 표시할 컬럼 선택 및 포맷팅
    display_df = df[['adset_name', 'spend', 'impressions', 'clicks', 'conversions', 
                    'ctr', 'cpc', 'roas', 'efficiency_score']].copy()
    
    # 컬럼명 한글화
    display_df.columns = ['광고세트명', '광고비', '노출수', '클릭수', '전환수', 
                         'CTR(%)', 'CPC(₩)', 'ROAS', '효율성점수']
    
    # 숫자 포맷팅
    display_df['광고비'] = display_df['광고비'].apply(lambda x: f"₩{x:,.0f}")
    display_df['노출수'] = display_df['노출수'].apply(lambda x: f"{x:,}")
    display_df['클릭수'] = display_df['클릭수'].apply(lambda x: f"{x:,}")
    display_df['전환수'] = display_df['전환수'].apply(lambda x: f"{x:,}")
    display_df['CTR(%)'] = display_df['CTR(%)'].apply(lambda x: f"{x:.2f}%")
    display_df['CPC(₩)'] = display_df['CPC(₩)'].apply(lambda x: f"₩{x:,.0f}")
    display_df['ROAS'] = display_df['ROAS'].apply(lambda x: f"{x:.2f}")
    display_df['효율성점수'] = display_df['효율성점수'].apply(lambda x: f"{x:.1f}")
    
    return display_df

def display_insights(insights: List[Dict]):
    """인사이트 및 추천사항 표시"""
    if not insights:
        st.info("분석할 수 있는 인사이트가 없습니다.")
        return
    
    st.subheader("🔍 주요 인사이트 및 추천사항")
    
    for insight in insights:
        priority_color = {
            'high': '🔴',
            'medium': '🟡', 
            'low': '🟢'
        }
        
        with st.expander(f"{priority_color.get(insight['priority'], '⚪')} {insight['title']}"):
            st.write(f"**설명:** {insight['description']}")
            st.write(f"**추천사항:** {insight['recommendation']}")
            st.write(f"**우선순위:** {insight['priority'].upper()}")

def export_to_sheets(comparison_data: Dict, trend_data: Dict, insights: List[Dict]):
    """Google Sheets로 데이터 내보내기"""
    try:
        with st.spinner("Google Sheets에 데이터를 업로드하는 중..."):
            sheets_manager = SheetsManager()
            success = sheets_manager.create_automated_report(comparison_data, trend_data, insights)
            
            if success:
                st.success("✅ Google Sheets에 성공적으로 업로드되었습니다!")
                st.write(f"**스프레드시트 URL:** {sheets_manager.get_spreadsheet_url()}")
                
                # 공유 옵션
                with st.expander("스프레드시트 공유 설정"):
                    email_input = st.text_input("공유할 이메일 주소 (쉼표로 구분)")
                    role = st.selectbox("권한 설정", ["reader", "writer", "owner"])
                    
                    if st.button("공유하기"):
                        if email_input:
                            emails = [email.strip() for email in email_input.split(",")]
                            sheets_manager.share_spreadsheet(emails, role)
                            st.success(f"스프레드시트가 {len(emails)}명에게 공유되었습니다.")
            else:
                st.error("❌ Google Sheets 업로드 중 오류가 발생했습니다.")
                
    except Exception as e:
        st.error(f"Google Sheets 업로드 실패: {e}")

def main():
    """메인 대시보드 함수"""
    
    # 제목
    st.title("📊 Meta 광고 성과 대시보드")
    st.markdown("캠페인 내 광고세트 성과 비교 및 일간 트렌드 분석")
    
    # 사이드바 - 설정
    st.sidebar.subheader("⚙️ 설정")
    
    # 캠페인 선택
    campaigns = load_campaigns()
    if not campaigns:
        st.error("캠페인을 로드할 수 없습니다. API 설정을 확인해주세요.")
        return
    
    campaign_options = {f"{camp['campaign_name']} ({camp['campaign_id']})": camp['campaign_id'] 
                       for camp in campaigns}
    
    selected_campaign_display = st.sidebar.selectbox(
        "분석할 캠페인 선택",
        options=list(campaign_options.keys())
    )
    selected_campaign_id = campaign_options[selected_campaign_display]
    
    # 분석 기간 선택
    analysis_days = st.sidebar.slider(
        "분석 기간 (일)",
        min_value=7,
        max_value=90,
        value=30,
        step=7
    )
    
    # 자동 새로고침 설정
    auto_refresh = st.sidebar.checkbox("자동 새로고침 (5분마다)")
    if auto_refresh:
        st.sidebar.write("⏰ 자동 새로고침이 활성화되었습니다.")
        time.sleep(300)  # 5분 대기
        st.rerun()
    
    # 데이터 새로고침 버튼
    if st.sidebar.button("🔄 데이터 새로고침"):
        st.cache_data.clear()
        st.rerun()
    
    # 메인 콘텐츠
    if selected_campaign_id:
        # 데이터 로드
        with st.spinner("데이터를 로드하는 중..."):
            insights_df, comparison_data, trend_data, insights = load_campaign_data(
                selected_campaign_id, analysis_days
            )
        
        if insights_df is None or insights_df.empty:
            st.warning("선택한 캠페인에 대한 데이터가 없습니다.")
            return
        
        # 주요 지표 요약
        st.subheader("📈 주요 성과 지표")
        
        if comparison_data:
            performance_gap = comparison_data.get('performance_gap', {})
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "총 광고세트 수",
                    comparison_data.get('total_adsets', 0)
                )
            
            with col2:
                st.metric(
                    "상위 성과자 평균 ROAS",
                    f"{performance_gap.get('top_avg_roas', 0):.2f}"
                )
            
            with col3:
                st.metric(
                    "하위 성과자 평균 ROAS",
                    f"{performance_gap.get('bottom_avg_roas', 0):.2f}"
                )
            
            with col4:
                improvement_potential = performance_gap.get('roas_improvement_potential', 0)
                st.metric(
                    "ROAS 개선 잠재력",
                    f"{improvement_potential:.2f}",
                    delta=f"+{improvement_potential:.2f}" if improvement_potential > 0 else None
                )
        
        # 차트 섹션
        st.subheader("📊 성과 분석 차트")
        
        # 성과 개요 차트
        fig_roas, fig_efficiency = create_performance_overview_charts(comparison_data)
        
        if fig_roas and fig_efficiency:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig_roas, width='stretch')
            with col2:
                st.plotly_chart(fig_efficiency, width='stretch')
        
        # 트렌드 차트
        fig_trend = create_trend_charts(trend_data)
        if fig_trend:
            st.plotly_chart(fig_trend, width='stretch')
        
        # 광고세트 비교 테이블
        st.subheader("📋 광고세트 성과 비교")
        
        comparison_table = create_comparison_table(comparison_data)
        if comparison_table is not None:
            st.dataframe(
                comparison_table,
                width='stretch',
                height=400
            )
        
        # 인사이트 섹션
        display_insights(insights)
        
        # Google Sheets 내보내기
        st.subheader("📤 Google Sheets 내보내기")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("분석 결과를 Google Sheets로 내보내어 팀과 공유하고 추가 분석을 수행할 수 있습니다.")
        
        with col2:
            if st.button("📊 Sheets로 내보내기", type="primary"):
                export_to_sheets(comparison_data, trend_data, insights)
        
        # 데이터 다운로드 옵션
        with st.expander("💾 데이터 다운로드"):
            if comparison_data and 'adset_rankings' in comparison_data:
                csv_data = pd.DataFrame(comparison_data['adset_rankings']).to_csv(index=False)
                st.download_button(
                    label="📥 CSV 다운로드",
                    data=csv_data,
                    file_name=f"meta_adset_performance_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    # 푸터
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        Meta 광고 성과 대시보드 | 2025년 8월 기준 최신 API 사용
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main() 