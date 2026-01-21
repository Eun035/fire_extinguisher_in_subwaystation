import streamlit as st
import pandas as pd
import platform

# ==============================================================================
# 1. 기본 설정 (폰트 설정 코드 삭제됨 - 필요 없음)
# ==============================================================================
st.set_page_config(layout="wide", page_title="대구 도시철도 소화기 현황 대시보드")

# ==============================================================================
# 2. 데이터 로드 및 전처리 함수
# ==============================================================================
@st.cache_data
def load_data():
    # 파일 경로 설정 (같은 폴더에 위치해야 함)
    file_1 = '국가철도공단_대구1호선_소화기설비_20250630.csv'
    file_3 = '국가철도공단_대구3호선_소화기설비_20250630.csv'
    
    # 인코딩 자동 감지 로직
    encoders = ['euc-kr', 'cp949', 'utf-8']
    
    def read_csv_safe(path):
        for enc in encoders:
            try:
                return pd.read_csv(path, encoding=enc)
            except UnicodeDecodeError:
                continue
        return None

    df1 = read_csv_safe(file_1)
    df3 = read_csv_safe(file_3)
    
    if df1 is None or df3 is None:
        return None

    # 데이터 전처리: 노선 구분 컬럼 추가
    df1['Line'] = '1호선 (지하)'
    df3['Line'] = '3호선 (지상)'
    
    # 위치 카테고리화 함수
    def categorize_loc(text):
        if pd.isna(text): return '기타'
        if '승강장' in text: return '승강장'
        elif '대합실' in text: return '대합실'
        else: return '기타'

    df1['Location_Cat'] = df1['상세위치'].apply(categorize_loc)
    df3['Location_Cat'] = df3['상세위치'].apply(categorize_loc)

    # 데이터 합치기
    df_combined = pd.concat([df1, df3], ignore_index=True)
    
    return df1, df3, df_combined

# ==============================================================================
# 3. 메인 대시보드 UI 구성
# ==============================================================================
st.title("🚇 대구 도시철도 소화기 설비 비교 분석")
st.markdown("### 지하(1호선) vs 지상(3호선) 환경에 따른 소화기 배치 차이")
st.caption("※ 이 대시보드는 Streamlit 내장 차트를 사용하여 배포 시에도 한글이 깨지지 않습니다.")

# 데이터 로드
data = load_data()

if data:
    df1, df3, df_all = data
    
    # --- [Section 1] 핵심 지표 (KPI) ---
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    
    stations_1 = df1['역명'].nunique()
    total_1 = df1['보유대수'].sum()
    avg_1 = total_1 / stations_1 if stations_1 > 0 else 0
    
    stations_3 = df3['역명'].nunique()
    total_3 = df3['보유대수'].sum()
    avg_3 = total_3 / stations_3 if stations_3 > 0 else 0

    col1.metric("1호선(지하) 총 보유대수", f"{total_1}대", delta="가장 많음")
    col2.metric("1호선 역당 평균", f"{avg_1:.1f}대", delta=f"3호선보다 +{avg_1 - avg_3:.1f}")
    col3.metric("3호선(지상) 총 보유대수", f"{total_3}대")
    col4.metric("3호선 역당 평균", f"{avg_3:.1f}대")

    # --- [Section 2] 시각화 차트 (내장 차트 사용) ---
    st.divider()
    st.subheader("📊 시각화 비교 분석")
    
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### 1. 노선별 총 소화기 수량 비교")
        # 데이터 가공: 인덱스를 'Line'으로 설정하면 자동으로 X축이 됨
        chart1_data = df_all.groupby('Line')['보유대수'].sum()
        st.bar_chart(chart1_data, color=["#FF7F0E"]) # 3호선 주황색 계열

    with chart_col2:
        st.markdown("#### 2. 주요 위치별(승강장/대합실) 분포")
        # 데이터 가공: 피벗 테이블처럼 만들어서 범주별 비교
        # index=위치, columns=노선, values=보유대수 합계
        chart2_data = df_all.groupby(['Location_Cat', 'Line'])['보유대수'].sum().unstack()
        st.bar_chart(chart2_data) # 자동으로 색상이 구분되어 나옴

    st.divider()
    
    chart_col3, chart_col4 = st.columns(2)
    
    with chart_col3:
        st.markdown("#### 3. 역별 보유량 산점도 (분포 확인)")
        st.caption("각 점은 하나의 역을 의미합니다. (1호선의 편차가 더 큼)")
        
        # 내장 차트에서는 Box Plot 대신 Scatter Chart가 유용함
        # X축: 역명, Y축: 보유대수, 색상: 노선
        st.scatter_chart(
            df_all,
            x='역명',
            y='보유대수',
            color='Line',
            size='보유대수' # 보유대수가 많을수록 점도 크게
        )

    with chart_col4:
        st.markdown("#### 4. 역별 보유대수 Top 5")
        
        tab1, tab2 = st.tabs(["1호선 Top 5", "3호선 Top 5"])
        
        with tab1:
            top5_1 = df1.groupby('역명')['보유대수'].sum().sort_values(ascending=False).head(5)
            st.dataframe(top5_1, use_container_width=True)
            
        with tab2:
            top5_3 = df3.groupby('역명')['보유대수'].sum().sort_values(ascending=False).head(5)
            st.dataframe(top5_3, use_container_width=True)

    # --- [Section 3] 상세 데이터 보기 ---
    st.divider()
    with st.expander("📂 전체 데이터 원본 보기"):
        st.dataframe(df_all)

else:
    st.error("⚠️ 데이터 파일을 찾을 수 없습니다. 폴더에 csv 파일이 있는지 확인해주세요.")