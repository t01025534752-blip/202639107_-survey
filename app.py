import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter
import re

# 1. 페이지 기본 설정 및 메인 제목
st.set_page_config(page_title="학생 생활 습관 및 만족도 분석 대시보드", layout="wide")
st.title("📊 학생 생활 습관 및 학교생활 만족도 대시보드")
st.caption("학생회 데이터 담당자용 - CSV 데이터를 업로드하여 학과별 분석 결과를 확인하세요.")

# 2. CSV 파일 업로드 섹션
st.header("1. 데이터 파일 업로드")
uploaded_file = st.file_uploader("설문조사 CSV 파일을 업로드해주세요.", type=["csv"])

if uploaded_file is not None:
    # 데이터 로드
    df_raw = pd.read_csv(uploaded_file)

    # 3. 원본 데이터 미리보기
    st.header("2. 원본 데이터 미리보기")
    st.dataframe(df_raw.head())

    # 4. 데이터 전처리
    st.header("3. 데이터 전처리 결과")

    # '모름', 결측치(NaN) 제거 대상 컬럼 지정
    # 실제 파일의 컬럼명에 맞게 활용할 수 있도록 정제 작업을 진행합니다.
    df_clean = df_raw.copy()

    initial_count = len(df_clean)

    # '모름' 문자열 및 결측치 제거
    df_clean = df_clean.replace("모름", None)
    df_clean = df_clean.dropna()

    # 수치형 데이터 변환 (분석에 필요한 컬럼들을 숫자 타입으로 변경)
    numeric_cols = ['공부시간', '수면시간', '스마트폰사용시간', '만족도']
    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

    df_clean = df_clean.dropna()
    final_count = len(df_clean)
    removed_count = initial_count - final_count

    # 전처리 결과 안내 표시
    col1, col2, col3 = st.columns(3)
    col1.metric("전체 데이터 수", f"{initial_count} 건")
    col2.metric("정제/제외된 데이터", f"{removed_count} 건", delta_color="inverse")
    col3.metric("최종 분석 데이터", f"{final_count} 건")

    st.divider()

    # 필수 컬럼 존재 여부 확인 후 시각화 진행
    required_cols = ['학과', '공부시간', '수면시간', '스마트폰사용시간', '만족도', '한줄의견']
    missing_cols = [c for c in required_cols if c not in df_clean.columns]

    if missing_cols:
        st.error(f"CSV 파일에 다음 필수 컬럼이 부족합니다: {missing_cols}")
        st.info("CSV 파일 컬럼명을 확인해주세요: 학과, 공부시간, 수면시간, 스마트폰사용시간, 만족도, 한줄의견")
    else:
        # 5. 학과 선택 필터 (드롭다운)
        st.header("4. 학과별 분석")
        department_list = ["전체"] + list(df_clean['학과'].unique())
        selected_dept = st.selectbox("조회할 학과를 선택하세요:", department_list)

        # 필터링된 데이터셋 생성
        if selected_dept == "전체":
            filtered_df = df_clean
        else:
            filtered_df = df_clean[df_clean['학과'] == selected_dept]

        # 평균 만족도 지표 표시
        avg_satisfaction = filtered_df['만족도'].mean()
        st.subheader(f"📌 {selected_dept} 평균 학교생활 만족도: {avg_satisfaction:.2f}점 / 5.0점")

        # 6. 학과별 분석 그래프 및 세부 결과 섹션
        st.subheader("📊 세부 분석 그래프")

        tab1, tab2 = st.tabs(["생활습관 vs 만족도 관계", "한 줄 의견 키워드 분석"])

        # -------------------------------------------------------------
        # 그래프 1: 주요 생활습관과 학교생활 만족도 간의 관계 (Plotly 산점도)
        # Plotly를 사용하면 한글 폰트 설정 없이 인터랙티브 차트가 깔끔하게 구현됩니다.
        # -------------------------------------------------------------
        with tab1:
            st.markdown("##### 💡 공부시간과 만족도 간의 관계 (원 크기: 스마트폰 사용시간)")

            fig1 = px.scatter(
                filtered_df,
                x='공부시간',
                y='만족도',
                size='스마트폰사용시간',
                color='수면시간',
                hover_data=['학과', '한줄의견'],
                title=f"[{selected_dept}] 생활습관(공부/수면/스마트폰)과 학교생활 만족도 관계",
                labels={
                    '공부시간': '일일 공부시간 (시간)',
                    '만족도': '학교생활 만족도 (점)',
                    '스마트폰사용시간': '스마트폰 사용시간 (시간)',
                    '수면시간': '수면시간 (시간)'
                },
                template='plotly_white'
            )
            # 축 및 레이아웃 디테일 설정
            fig1.update_layout(
                xaxis_title="일일 공부시간 (시간)",
                yaxis_title="학교생활 만족도 (점수, 1~5점)",
                font=dict(size=13)
            )
            st.plotly_chart(fig1, use_container_width=True)

        # -------------------------------------------------------------
        # 그래프 2: 한 줄 의견 주요 단어 출현 빈도 (막대그래프)
        # -------------------------------------------------------------
        with tab2:
            st.markdown("##### 💬 학생 한 줄 의견 자주 나온 단어 Top 10")

            # 모든 한 줄 의견을 텍스트 하나로 병합
            all_text = " ".join(filtered_df['한줄의견'].astype(str))

            # 한글 및 공백을 제외한 특수문자 제거 후 단어 추출 (2글자 이상)
            words = re.findall(r'\b[가-힣]{2,}\b', all_text)

            # 제외할 불용어 설정 (필요 시 추가)
            stopwords = ['너무', '정말', '많이', '그리고', '해서', '좋습니다', '있어서']
            meaningful_words = [w for w in words if w not in stopwords]

            # 단어 빈도수 계산
            word_counts = Counter(meaningful_words).most_common(10)

            if word_counts:
                # 데이터프레임 변환
                df_words = pd.DataFrame(word_counts, columns=['단어', '빈도수'])

                # Plotly 막대그래프 시각화
                fig2 = px.bar(
                    df_words,
                    x='단어',
                    y='빈도수',
                    text='빈도수',
                    color='빈도수',
                    color_continuous_scale='Blues',
                    title=f"[{selected_dept}] 학생 한 줄 의견 주요 키워드 빈도 (Top 10)",
                    labels={'단어': '주요 키워드', '빈도수': '출현 빈도 (회)'},
                    template='plotly_white'
                )

                fig2.update_layout(
                    xaxis_title="키워드 (단어)",
                    yaxis_title="출현 빈도 (회)",
                    font=dict(size=13)
                )
                fig2.update_traces(textposition='outside')
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("분석할 한 줄 의견 텍스트 데이터가 부족합니다.")

else:
    st.info("👆 위 섹션에서 설문조사 CSV 파일을 업로드해 주세요.")