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
        st.tabs(
        ["📋 기초 통계", "📈 연도별 추이", "📍 지역별 분석", "🔄 변화량 분석", "🎨 시각화"]
        )

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
        st.title("📈 인구 동향 전처리 & 요약 분석")
        uploaded = st.file_uploader("population_trends.csv 파일을 업로드하세요", type=["csv"])
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded)

        tabs = st.tabs([
            "1. 목적 & 절차",
            "2. 기초 통계",
            "3. 연도별 추이",
            "4. 지역별분석",
            "5. 변화량분석",
            "6. 시각화"
        ])

        # 1. 목적 & 분석 절차
        with tabs[0]:
            st.header("🔭 목적 & 분석 절차")
            st.markdown("""
            **절차**:
            1. 기초 통계
            2. 연도별 추이
            3. 지역별분석
            4. 변화량분석
            5. 시각화
            """)

        # 2. 기초 통계
        with tabs["📋 기초 통계"]:
            sejong_mask = df["지역"] == "세종"
            df.loc[sejong_mask] = df.loc[sejong_mask].replace("-", 0)

            # 숫자형 컬럼 변환
            num_cols = ["인구", "출생아수(명)", "사망자수(명)"]
            for col in num_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            # 데이터 미리보기
            st.subheader("🗂️ 데이터프레임 프리뷰")
            st.write(df.head())

            # 요약 통계
            st.subheader("📊 요약 통계 (df.describe())")
            st.write(df.describe())

            # DataFrame 구조(info) 출력
            st.subheader("🔍 데이터프레임 구조 (df.info())")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

        # 3. 연도별 추이
        with tabs["📈 연도별 추이"]:
            # --- 2) 전국(population) 필터링 -------------------------------------------------
            nation = df.query("지역 == '전국'").copy()
            nation = nation.sort_values("연도")          # 정렬(혹시 모를 뒤죽박죽 방지)

            # --- 3) 최근 3년 자연증가(출생-사망) 평균 ---------------------------------------
            last_year = nation["연도"].max()
            recent3   = df.query("연도 >= @last_year - 2")

            # 자연증가 = 출생 - 사망
            recent3["net_inc"] = recent3["출생아수"] - recent3["사망자수"]
            avg_net_inc = recent3["net_inc"].mean()

            # --- 4) 2035년 인구 예측 --------------------------------------------------------
            years_forward        = 2035 - last_year
            base_population      = nation.loc[nation["연도"] == last_year, "인구"].iloc[0]
            predicted_population = base_population + avg_net_inc * years_forward

            # --- 5) 그래프 그리기 ----------------------------------------------------------
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(nation["연도"], nation["인구"], marker="o", label="Actual")
            ax.scatter(2035, predicted_population, color="red", zorder=5,
                    label="Predicted 2035")
            ax.set_title("Population Trend (Nationwide)")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()
            ax.tick_params(axis="x", rotation=45)

            # --- 6) Streamlit 출력 ---------------------------------------------------------
            st.header("Korea Nationwide Population Trend & 2035 Forecast")
            st.pyplot(fig)
            st.markdown(
                f"**Predicted population in 2035:** "
                f"{predicted_population:,.0f} people\n\n"
                f"*Assumes average natural increase "  # 코멘트도 영어!
                f"({avg_net_inc:,.0f}/yr) stays constant from {last_year+1} to 2035.*"
            )

        # 4. 지역별분석
        with tabs["📍 지역별 분석"]:
            df = df[df["region"] != "전국"]
            latest_year = df["year"].max()
            prev_year   = latest_year - 5

            latest_pop  = df[df["year"] == latest_year].set_index("region")["population"]
            prev_pop    = df[df["year"] == prev_year ].set_index("region")["population"]

            change      = (latest_pop - prev_pop).dropna()
            pct_change  = (change / prev_pop.loc[change.index] * 100).round(2)

            # 천 명 단위 변환
            change_k    = (change / 1000).round(1)

            # ---------- 3. 지역 이름 영어 변환 ----------
            kor2eng = {
            "서울": "Seoul", "부산": "Busan", "대구": "Daegu", "인천": "Incheon",
            "광주": "Gwangju", "대전": "Daejeon", "울산": "Ulsan",
            "세종": "Sejong", "경기": "Gyeonggi", "강원": "Gangwon",
            "충북": "Chungbuk", "충남": "Chungnam", "전북": "Jeonbuk",
            "전남": "Jeonnam", "경북": "Gyeongbuk", "경남": "Gyeongnam",
            "제주": "Jeju"
            }
            change_k.index  = change_k.index.map(lambda x: kor2eng.get(x, x))
            pct_change.index = pct_change.index.map(lambda x: kor2eng.get(x, x))

            # 정렬
            change_k = change_k.sort_values(ascending=False)
            pct_change = pct_change.loc[change_k.index]   # 같은 순서로

            # ---------- 4. Streamlit 화면 ----------
            st.set_page_config(page_title="Population Trend", layout="wide")
            sns.set_theme(style="whitegrid")

            st.title("Population Change by Region (Last 5 Years)")

            # 4-1. 절대 변화량(bar, 천 명)
            fig1, ax1 = plt.subplots(figsize=(10, 8))
            sns.barplot(x=change_k.values, y=change_k.index, ax=ax1, orient="h")
            ax1.set_xlabel("Change (thousands)")
            ax1.set_ylabel("")
            ax1.set_title(f"{prev_year}-{latest_year} Change")

            # 값 라벨
            for bar in ax1.patches:
                ax1.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                        f"{bar.get_width():,.1f}", va='center')

            st.pyplot(fig1)

            # 4-2. 변화율(bar, %)
            fig2, ax2 = plt.subplots(figsize=(10, 8))
            sns.barplot(x=pct_change.values, y=pct_change.index, ax=ax2, orient="h", color="skyblue")
            ax2.set_xlabel("Change (%)")
            ax2.set_ylabel("")
            ax2.set_title(f"{prev_year}-{latest_year} Change Rate")

            for bar in ax2.patches:
                ax2.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2,
                        f"{bar.get_width():,.2f}%", va='center')

            st.pyplot(fig2)

            # ---------- 5. 해설 ----------
            top_region   = change_k.index[0]
            bottom_region = change_k.index[-1]
            st.markdown(
                f"""
            **Quick take**  
            - **{top_region}** shows the biggest uptick, adding **{change_k.iloc[0]:,.1f} k** people (+{pct_change.iloc[0]:.2f}%).  
            - **{bottom_region}** shrank the most, losing **{abs(change_k.iloc[-1]):,.1f} k** (-{abs(pct_change.iloc[-1]):.2f}%).  
            - The gap hints at continued urban-centric migration and the aging headwinds hitting rural provinces harder.
            """
            )

        # 5. 변화량분석
        with tabs["🔄 변화량 분석"]:
            df_reg = df[df["지역"] != "전국"].copy()
            df_reg = df_reg.sort_values(["지역", "연도"])

            # 2) 연속 연도 간 증감(diff) 계산
            df_reg["증감"] = df_reg.groupby("지역")["인구"].diff()

            # 3) NaN(첫 해) 드랍 + 변화 폭 큰 순서로 TOP 100 뽑기
            df_change = df_reg.dropna(subset=["증감"])
            top100_idx = df_change["증감"].abs().sort_values(ascending=False).index
            df_top = df_change.loc[top100_idx].head(100)

            # 4) 숫자 포맷(천 단위 콤마)
            df_top[["인구", "증감"]] = df_top[["인구", "증감"]].astype(int)

            # 5) 컬러 스케일 계산 (파랑=증가, 빨강=감소)
            abs_max = df_top["증감"].abs().max()

            styler = (
                df_top
                .style
                .format({"인구": "{:,}", "증감": "{:,}"})
                .background_gradient(
                    cmap="RdBu",            # red↔blue diverging
                    subset=["증감"],
                    vmin=-abs_max, vmax=abs_max
                )
            )

            # 6) Streamlit 화면에 뽑아주기
            st.title("Top 100 YoY Population Changes by Region")
            st.caption("Blue = increase, Red = decrease. Bigger, bolder colors → wilder swings!")
            st.dataframe(styler, use_container_width=True)

        # 6. 시각화
        with tabs["🎨 시각화"]:
            k2e = {
                "서울": "Seoul",
                "부산": "Busan",
                "대구": "Daegu",
                "인천": "Incheon",
                "광주": "Gwangju",
                "대전": "Daejeon",
                "울산": "Ulsan",
                "세종": "Sejong",
                "경기": "Gyeonggi",
                "강원": "Gangwon",
                "충북": "Chungbuk",
                "충남": "Chungnam",
                "전북": "Jeonbuk",
                "전남": "Jeonnam",
                "경북": "Gyeongbuk",
                "경남": "Gyeongnam",
                "제주": "Jeju",
            }

            # 👉 이름 바꿔줘
            df['Region'] = df['지역'].map(k2e).fillna(df['지역'])

            # ──────────────────────────────────────────────────────────────
            # 1) 피벗 테이블 (행=지역, 열=연도)
            pivot = (
                df.pivot_table(
                    index="Region",
                    columns="연도",
                    values="인구",
                    aggfunc="sum"
                )
                .fillna(0)
                .astype(int)
            )

            # 2) 그래프 그리기 (누적 영역)
            sns.set_style("whitegrid")
            palette = sns.color_palette("tab20", n_colors=len(pivot))  # 색상 20개까지 보장

            fig, ax = plt.subplots(figsize=(14, 7))
            pivot.T.plot.area(
                ax=ax,
                color=palette,
                linewidth=0,
            )

            ax.set_title("Population Trend by Region", fontsize=18, pad=10)
            ax.set_xlabel("Year", fontsize=12)
            ax.set_ylabel("Population", fontsize=12)
            ax.legend(title="Region", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)

            st.pyplot(fig)

            # 3) 보너스: 피벗 테이블도 같이 보여주기 (숫자 천 단위 콤마)
            st.markdown("### Pivot Table")
            st.dataframe(pivot.style.format("{:,}"))

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