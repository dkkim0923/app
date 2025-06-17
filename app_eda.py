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
        
        # 페이지 이동 버튼 추가
        st.markdown("[지역별 인구 분석 페이지로 이동](?page=eda)")  # Streamlit navigation query param
        
        # Population Trends 데이터셋 출처 및 소개
        st.markdown("""
        ---
        **Population Trends 데이터셋**  
        - 제공처: 통계청 KOSIS  
        - 설명: 전국 및 시·도별 연도별 인구, 출생아 수, 사망자 수 데이터를 포함합니다.  
        - 주요 변수:  
          - `연도`: 기준 연도  
          - `지역`: 전국 또는 17개 시·도  
          - `인구`: 해당 연도의 총 인구 수  
          - `출생아수(명)`: 해당 연도 출생아 수  
          - `사망자수(명)`: 해당 연도 사망자 수  
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
        st.title("📊 지역별 인구 분석")

        pop_file = st.file_uploader("population_trends.csv 파일 업로드", type="csv")
        if not pop_file:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        # 파일 읽기 및 전처리
        df = pd.read_csv(pop_file)

        # 결측치, 중복 확인
        st.subheader("🔍 결측치 및 중복 데이터 확인")
        missing = df.isin(["-", None]).sum().sum()
        duplicates = df.duplicated().sum()
        st.write(f"결측치 항목 수: {missing}")
        st.write(f"중복 행 수: {duplicates}")

        # '-'를 0으로, 숫자형 변환
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df[col] = pd.to_numeric(df[col].replace('-', np.nan), errors='coerce').fillna(0).astype(int)

        # 탭 구조
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"
        ])

        with tab1:
            st.subheader("📄 데이터 구조 및 기초 통계")
            buf = io.StringIO()
            df.info(buf=buf)
            st.text(buf.getvalue())
            st.dataframe(df.describe())
            st.subheader("🧾 샘플 데이터")
            st.dataframe(df.head())

        with tab2:
            st.subheader("📈 전국 인구 연도별 추이 및 2035 예측")
            nat = df[df['지역'] == '전국']
            fig, ax = plt.subplots()
            sns.lineplot(x='연도', y='인구', data=nat, marker='o', ax=ax)
            ax.set_title("Population Trend by Year")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")

            recent = nat.sort_values('연도').tail(3)
            avg_delta = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
            est_2035 = nat['인구'].iloc[-1] + (2035 - nat['연도'].iloc[-1]) * avg_delta
            ax.axvline(2035, linestyle="--", color="gray")
            ax.annotate(f"Est. 2035: {int(est_2035):,}", xy=(2035, est_2035), textcoords="offset points", xytext=(-40,10))
            ax.plot(2035, est_2035, marker='o', color='red')
            st.pyplot(fig)

        with tab3:
            st.subheader("📉 최근 5년간 지역별 인구 변화량 순위")
            years = sorted(df['연도'].unique())[-5:]
            pivot = df[df['연도'].isin(years) & (df['지역'] != '전국')].pivot(index='지역', columns='연도', values='인구')
            pivot['Change'] = (pivot[years[-1]] - pivot[years[0]]) // 1000
            pivot['ChangeRate'] = ((pivot[years[-1]] - pivot[years[0]]) / pivot[years[0]]) * 100
            pivot = pivot.sort_values('Change', ascending=False)

            fig, ax = plt.subplots(figsize=(8, 10))
            sns.barplot(x='Change', y=pivot.index, data=pivot.reset_index(), ax=ax)
            ax.set_title("Population Change (Last 5 Years)")
            ax.set_xlabel("Change (Thousands)")
            for p in ax.patches:
                ax.annotate(f"{int(p.get_width()):,}", (p.get_width(), p.get_y() + p.get_height()/2), va='center')
            st.pyplot(fig)

            fig2, ax2 = plt.subplots(figsize=(8, 10))
            sns.barplot(x='ChangeRate', y=pivot.index, data=pivot.reset_index(), ax=ax2)
            ax2.set_title("Population Growth Rate (%)")
            ax2.set_xlabel("Change Rate (%)")
            for p in ax2.patches:
                ax2.annotate(f"{p.get_width():.2f}%", (p.get_width(), p.get_y() + p.get_height()/2), va='center')
            st.pyplot(fig2)

        with tab4:
            st.subheader("📌 인구 증감 상위 100 사례")
            df_sorted = df.sort_values(['지역', '연도'])
            df_sorted['증감'] = df_sorted.groupby('지역')['인구'].diff()
            top100 = df_sorted[df_sorted['지역'] != '전국'].nlargest(100, '증감')
            styled = top100.style.background_gradient(subset=['증감'], cmap='bwr').format({'증감': '{:,}'})
            st.dataframe(styled)

        with tab5:
            st.subheader("🌈 지역별 인구 히트맵 & 누적 영역그래프")
            pivot_heat = df.pivot(index='지역', columns='연도', values='인구')
            fig, ax = plt.subplots(figsize=(12, 8))
            sns.heatmap(pivot_heat, cmap='YlGnBu', ax=ax)
            st.pyplot(fig)

            pivot_area = pivot_heat.T
            fig2, ax2 = plt.subplots(figsize=(12, 6))
            pivot_area.plot.area(ax=ax2, stacked=True)
            ax2.set_title("Population Stacked Area")
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