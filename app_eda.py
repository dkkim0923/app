import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # 기존 Bike Sharing 데이터 설명
        st.markdown("""
        ---
        **Bike Sharing Demand 데이터셋**  
        - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
        - 설명: 2011–2012년 워싱턴 D.C.의 시간별 자전거 대여량 기록  
        """)

        # 추가: Population Trends 데이터 설명
        st.markdown("""
        ---
        **Population Trends 데이터셋**  
        - 출처: 통계청  
        - 설명: 전국 및 지역별 연도별 인구, 출생아수, 사망자수 데이터  
        - 주요 변수:
          - `연도`: 기준 연도  
          - `지역`: 시·도 단위 지역명  
          - `인구`, `출생아수(명)`, `사망자수(명)`: 연도별 인구 및 변동 정보
        """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 EDA 분석 페이지")

        uploaded = st.file_uploader("Bike 데이터셋 업로드 (train.csv)", type="csv", key="bike")
        pop_file = st.file_uploader("Population 데이터셋 업로드 (population_trends.csv)", type="csv", key="pop")

        if not uploaded and not pop_file:
            st.info("분석할 CSV 파일을 업로드하세요.")
            return

        tabs = st.tabs(["Bike Sharing EDA", "Population Trends EDA"])

        # -------------------------
        # Bike 데이터 EDA (기존 유지)
        # -------------------------
        with tabs[0]:
            if not uploaded:
                st.info("Bike 데이터(train.csv)를 업로드 해주세요.")
            else:
                df = pd.read_csv(uploaded, parse_dates=['datetime'])

                st.subheader("1) 데이터 구조 및 요약")
                buf = io.StringIO()
                df.info(buf=buf)
                st.text(buf.getvalue())
                st.dataframe(df.describe())

                st.subheader("2) Datetime 파생")
                df['year'] = df['datetime'].dt.year
                df['month'] = df['datetime'].dt.month
                df['hour'] = df['datetime'].dt.hour
                df['dayofweek'] = df['datetime'].dt.dayofweek
                st.dataframe(df[['datetime', 'year', 'month', 'hour', 'dayofweek']].head())

                st.subheader("3) 시각화 예시")
                fig1, ax1 = plt.subplots()
                sns.pointplot(x='hour', y='count', hue='workingday', data=df, ax=ax1)
                ax1.set_title("Hourly Usage by Working Day")
                st.pyplot(fig1)

        # -------------------------
        # Population Trends 분석
        # -------------------------
        with tabs[1]:
            if not pop_file:
                st.info("population_trends.csv 파일을 업로드 해주세요.")
                return

            df = pd.read_csv(pop_file)
            df.replace("-", 0, inplace=True)
            df[['인구', '출생아수(명)', '사망자수(명)']] = df[['인구', '출생아수(명)', '사망자수(명)']].astype(int)

            tab1, tab2, tab3, tab4, tab5 = st.tabs(["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

            with tab1:
                st.subheader("📄 데이터 구조 정보")
                buf = io.StringIO()
                df.info(buf=buf)
                st.text(buf.getvalue())
                st.subheader("📊 요약 통계")
                st.dataframe(df.describe())
                st.subheader("🧾 샘플")
                st.dataframe(df.head())

            with tab2:
                st.subheader("📈 전국 인구 연도별 추이")
                nat = df[df['지역'] == '전국']
                fig, ax = plt.subplots()
                sns.lineplot(x='연도', y='인구', data=nat, marker='o', ax=ax)
                ax.set_title("Population Trend by Year")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")

                # 단순 예측
                recent = nat.sort_values('연도').tail(3)
                avg_delta = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
                est_2035 = nat['인구'].iloc[-1] + (2035 - nat['연도'].iloc[-1]) * avg_delta
                ax.axvline(2035, linestyle="--", color="gray")
                ax.annotate(f"Est. 2035: {int(est_2035):,}", xy=(2035, est_2035), textcoords="offset points", xytext=(-40,10))
                ax.plot(2035, est_2035, marker='o', color='red')
                st.pyplot(fig)

            with tab3:
                st.subheader("📉 최근 5년간 지역별 인구 변화량")
                years = sorted(df['연도'].unique())[-5:]
                pivot = df[df['연도'].isin(years) & (df['지역'] != '전국')].pivot(index='지역', columns='연도', values='인구')
                pivot['변화량'] = pivot[years[-1]] - pivot[years[0]]
                pivot['변화율(%)'] = ((pivot[years[-1]] - pivot[years[0]]) / pivot[years[0]]) * 100
                pivot = pivot.sort_values('변화량', ascending=False)

                fig, ax = plt.subplots(figsize=(8, 10))
                sns.barplot(x='변화량', y=pivot.index, ax=ax)
                ax.set_title("Top Regional Change")
                st.pyplot(fig)

                fig2, ax2 = plt.subplots(figsize=(8, 10))
                sns.barplot(x='변화율(%)', y=pivot.index, ax=ax2)
                ax2.set_title("Top Regional Change Rate (%)")
                st.pyplot(fig2)

            with tab4:
                st.subheader("📌 인구 증감 상위 100개 사례")
                df_sorted = df.sort_values(['지역', '연도'])
                df_sorted['증감'] = df_sorted.groupby('지역')['인구'].diff()
                top100 = df_sorted[df_sorted['지역'] != '전국'].sort_values('증감', ascending=False).head(100)
                styled = top100.style.background_gradient(subset=['증감'], cmap='bwr').format({'증감': '{:,}'})
                st.dataframe(styled)

            with tab5:
                st.subheader("🌈 인구 히트맵")
                pivot_heat = df.pivot(index='지역', columns='연도', values='인구')
                fig, ax = plt.subplots(figsize=(12, 8))
                sns.heatmap(pivot_heat, cmap='YlGnBu', ax=ax)
                st.pyplot(fig)

                st.subheader("📊 누적 영역그래프")
                pivot_area = pivot_heat.T
                fig2, ax2 = plt.subplots(figsize=(12, 6))
                pivot_area.plot.area(ax=ax2, stacked=True)
                ax2.set_title("Stacked Area by Region")
                st.pyplot(fig2)



# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()