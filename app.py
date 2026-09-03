# -*- coding: utf-8 -*-
"""
PT Account — 김준수 트레이너 전용 1인 PT 회원 관리 & AI 3-STEP 바이오 프로파일 시스템
================================================================================
"""

import os
import json
import calendar
import base64
import re
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components
from supabase import create_client, Client

# =========================================================
# 0. 대한민국 표준시(KST) 구하기 헬퍼 함수
# =========================================================
def get_kst_now():
    """서버 환경과 상관없이 항상 한국 표준시(UTC+9) 반환"""
    return datetime.now(timezone(timedelta(hours=9)))

# =========================================================
# 0-1. Supabase DB 연결 설정
# =========================================================
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_supabase()

# =========================================================
# 0-2. 페이지 설정 & 블루톤 UI Design System
# =========================================================
st.set_page_config(
    page_title="PT Account — 김준수 트레이너",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

MY_NAME = "김준수"
COLOR_NAVY = "#1E293B"
COLOR_BLUE = "#2563EB"
COLOR_ICE = "#EFF6FF"
COLOR_TEXT = "#0F172A"

CUSTOM_CSS = f"""
<style>
    html, body, [class*="css"] {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}
    .stApp {{ background-color: {COLOR_ICE}; }}

    section[data-testid="stSidebar"] {{ background-color: {COLOR_NAVY}; }}
    section[data-testid="stSidebar"] * {{ color: #E2E8F0 !important; }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label {{
        background: rgba(255,255,255,0.04);
        border-radius: 10px; padding: 12px 14px; margin-bottom: 6px;
        font-weight: 700; transition: background .15s ease;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
        background: rgba(37,99,235,0.35);
    }}

    .pt-card {{
        background: #FFFFFF; border: 1px solid #DCE6F5; border-radius: 16px;
        padding: 20px; box-shadow: 0 8px 22px rgba(15,23,42,0.06); margin-bottom: 16px;
    }}
    .pt-metric {{
        background: #FFFFFF; border: 1px solid #DCE6F5; border-radius: 16px;
        padding: 18px 20px; box-shadow: 0 8px 22px rgba(15,23,42,0.06);
    }}
    .pt-metric .label {{ font-size: 12.5px; font-weight: 700; color: #64748B; text-transform: uppercase; }}
    .pt-metric .value {{ font-size: 26px; font-weight: 800; color: {COLOR_TEXT}; margin-top: 4px; }}
    .pt-metric .value.accent {{ color: {COLOR_BLUE}; }}

    div.stButton > button {{ border-radius: 10px; font-weight: 700; }}

    .slot-booked {{ background:{COLOR_ICE}; border-radius:8px; padding:12px; font-size:15px; border-left: 4px solid {COLOR_BLUE}; }}
    .cal-weekday {{ text-align:center; font-weight:800; color:#64748B; font-size:14px; padding-bottom:8px; }}

    .custom-item-card {{
        background: #FFFFFF;
        border-left: 5px solid {COLOR_BLUE};
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 8px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .gender-badge-female {{
        background-color: #FFE4E6; color: #E11D48; padding: 3px 10px;
        border-radius: 12px; font-weight: 800; font-size: 12px; border: 1px solid #FECDD3; display: inline-block;
    }}
    .gender-badge-male {{
        background-color: #DCFCE7; color: #15803D; padding: 3px 10px;
        border-radius: 12px; font-weight: 800; font-size: 12px; border: 1px solid #BBF7D0; display: inline-block;
    }}

    .rem-badge {{
        background-color: #EFF6FF; color: {COLOR_BLUE}; padding: 3px 10px;
        border-radius: 12px; font-weight: 800; font-size: 12px; border: 1px solid #BFDBFE; display: inline-block;
    }}

    .status-attend {{
        background-color: #DCFCE7; color: #15803D; padding: 4px 12px;
        border-radius: 12px; font-weight: 800; font-size: 13px; border: 1px solid #BBF7D0; display: inline-block;
    }}
    .status-absent {{
        background-color: #FFE4E6; color: #E11D48; padding: 4px 12px;
        border-radius: 12px; font-weight: 800; font-size: 13px; border: 1px solid #FECDD3; display: inline-block;
    }}
    .status-pending {{
        background-color: #F1F5F9; color: #64748B; padding: 4px 12px;
        border-radius: 12px; font-weight: 800; font-size: 13px; border: 1px solid #E2E8F0; display: inline-block;
    }}

    .tr-high {{ background-color: #DCFCE7; color: #166534; padding: 4px 8px; border-radius: 6px; font-weight: 800; }}
    .tr-mid {{ background-color: #FEF08A; color: #854D0E; padding: 4px 8px; border-radius: 6px; font-weight: 800; }}
    .tr-low {{ background-color: #FEE2E2; color: #991B1B; padding: 4px 8px; border-radius: 6px; font-weight: 800; }}
    .tr-check {{ background-color: #F1F5F9; color: #475569; padding: 4px 8px; border-radius: 6px; font-weight: 800; }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def rerun():
    if hasattr(st, "rerun"): st.rerun()
    else: st.experimental_rerun()


# =========================================================
# 1. 컬럼 정의 & 템플릿
# =========================================================
MEMBERS_COLUMNS = [
    "member_id", "name", "contact", "birth_date", "reg_date",
    "total_sessions", "remaining_sessions", "trainer", "status",
    "goal", "session_price", "branch", "gender", "age",
    "tr_expect", "re_status", "week_group", "memo", "survey_json",
    "exp_re_sessions", "exp_re_price", "is_exp_configured"
]
LOGS_COLUMNS = ["log_id", "member_id", "date", "start_time", "end_time", "exercises_json", "good_points", "improve_points", "sent", "attendance"]
INBODY_COLUMNS = ["record_id", "member_id", "date", "weight", "skeletal_muscle", "body_fat_pct"]
SALES_COLUMNS = ["sale_id", "member_id", "date", "product_name", "amount", "pay_type"]
REPORTS_COLUMNS = [
    "report_id", "member_id", "date", "goal_text", "analysis_text", "posture_eval",
    "func_eval", "phase1_text", "phase2_text", "phase3_text", "trainer_comment", "status", "delivered"
]
BOOKINGS_COLUMNS = ["booking_id", "member_id", "date", "time_slot", "status"]
CONSULTATIONS_COLUMNS = ["consult_id", "date", "name", "contact", "gender", "goal", "source", "expect_status", "memo", "converted", "exp_sessions", "exp_price"]

STATUS_OPTIONS = ["Active", "Hold", "Expired"]
TR_EXPECT_OPTIONS = ["높음", "중간", "낮음", "이탈", "확인중"]
RE_STATUS_OPTIONS = ["결제완료", "결제예정", "이월", "이탈", "전월이탈", "미지정"]

TIME_SLOTS = [f"{h:02d}:00" for h in range(6, 23)]
WEEKDAY_LABELS_KR = ["일", "월", "화", "수", "목", "금", "토"]

PRESET_ROUTINES_DF = {
    "가슴": pd.DataFrame([
        {"종목": "바벨 벤치프레스", "중량(kg)": 40.0, "횟수": 10, "세트": 4},
        {"종목": "인클라인 덤벨프레스", "중량(kg)": 12.0, "횟수": 12, "세트": 3},
        {"종목": "딥스 (체중/보조)", "중량(kg)": 0.0, "횟수": 10, "세트": 3},
        {"종목": "체스트 프레스 머신", "중량(kg)": 30.0, "횟수": 12, "세트": 3},
        {"종목": "케이블 크로스오버", "중량(kg)": 10.0, "횟수": 15, "세트": 3},
    ]),
    "등": pd.DataFrame([
        {"종목": "랫풀다운", "중량(kg)": 35.0, "횟수": 12, "세트": 4},
        {"종목": "시티드 케이블 로우", "중량(kg)": 35.0, "횟수": 12, "세트": 3},
        {"종목": "바벨 벤트오버 로우", "중량(kg)": 30.0, "횟수": 10, "세트": 3},
        {"종목": "원암 덤벨 로우", "중량(kg)": 14.0, "횟수": 12, "세트": 3},
        {"종목": "루마니안 데드리프트", "중량(kg)": 50.0, "횟수": 8, "세트": 3},
    ]),
    "어깨": pd.DataFrame([
        {"종목": "오버헤드 바벨 숄더프레스", "중량(kg)": 20.0, "횟수": 10, "세트": 4},
        {"종목": "덤벨 숄더프레스", "중량(kg)": 10.0, "횟수": 12, "세트": 3},
        {"종목": "사이드 레터럴 레이즈", "중량(kg)": 5.0, "횟수": 15, "세트": 4},
        {"종목": "벤트오버 레터럴 레이즈", "중량(kg)": 4.0, "횟수": 15, "세트": 3},
        {"종목": "페이스풀 (케이블)", "중량(kg)": 15.0, "횟수": 15, "세트": 3},
    ]),
    "하체": pd.DataFrame([
        {"종목": "바벨 스쿼트", "중량(kg)": 40.0, "횟수": 10, "세트": 4},
        {"종목": "레그 프레스", "중량(kg)": 80.0, "횟수": 12, "세트": 3},
        {"종목": "덤벨 런지", "중량(kg)": 8.0, "횟수": 10, "세트": 3},
        {"종목": "레그 익스텐션", "중량(kg)": 25.0, "횟수": 15, "세트": 3},
        {"종목": "라잉 레그 컬", "중량(kg)": 20.0, "횟수": 15, "세트": 3},
    ]),
    "전신": pd.DataFrame([
        {"종목": "고블릿 스쿼트", "중량(kg)": 12.0, "횟수": 12, "세트": 3},
        {"종목": "푸시업", "중량(kg)": 0.0, "횟수": 12, "세트": 3},
        {"종목": "케이블 로우", "중량(kg)": 25.0, "횟수": 12, "세트": 3},
        {"종목": "덤벨 숄더프레스", "중량(kg)": 8.0, "횟수": 12, "세트": 3},
        {"종목": "플랭크", "중량(kg)": 0.0, "횟수": 60, "세트": 3},
    ]),
}


def safe_index(lst, val, default_idx=0):
    if pd.isna(val) or val is None: return default_idx
    val_str = str(val).strip()
    return lst.index(val_str) if val_str in lst else default_idx


def safe_float(val, default_val=0.0):
    try:
        if pd.isna(val) or val is None:
            return default_val
        f = float(val)
        return default_val if pd.isna(f) else f
    except Exception:
        return default_val


def safe_int(val, default_val=0):
    try:
        if pd.isna(val) or val is None:
            return default_val
        return int(float(val))
    except Exception:
        return default_val


def get_week_of_month(target_date):
    year, month, day = target_date.year, target_date.month, target_date.day
    cal = calendar.monthcalendar(year, month)
    for week_idx, week in enumerate(cal):
        if day in week:
            return f"{week_idx + 1}주차"
    return "1주차"


def get_month_weeks_list(year, month):
    cal = calendar.monthcalendar(year, month)
    return [f"{w}주차" for w in range(1, len(cal) + 1)]


def refine_journal_feedback(text, is_good=True):
    if not text or not str(text).strip():
        if is_good:
            return "목표 주동근의 자극점에 정확히 집중하여 수축감을 매우 효율적으로 형성하셨습니다."
        else:
            return "동작 수행 시 코어 지지력과 관절 가동 범위를 지속 체크하여 움직임의 안정성을 극대화하겠습니다."
            
    t = str(text).strip()
    clean_t = re.sub(r"(이\s*)?(약하심|약함|부족함|약|하심|함|임|음|있음|있으심|보임|같음)$", "", t).strip()
    
    if is_good:
        if re.search(r"^가슴$", clean_t):
            return "가슴 부위 주동근(대흉근) 자극 전달에 집중하여 수축감과 견갑골 정렬을 매우 안정적으로 유지하셨습니다."
        elif re.search(r"^등$", clean_t):
            return "등 부위 주동근(광배근 및 승모근) 신전 시 타겟 자극을 효율적으로 집중시키며 수행하셨습니다."
        elif re.search(r"^어깨$", clean_t):
            return "삼각근 고립 자극 및 관절 궤적을 안정적으로 제어하며 완성도 높은 훈련을 수행하셨습니다."
        elif re.search(r"^하체$", clean_t):
            return "고관절 및 대퇴사두근 수축 타이밍을 정확히 맞추어 하중 분산을 안정적으로 가져가셨습니다."

        if re.search(r"운동신경|신경|센스|이해|빠름|좋", clean_t):
            return "새로운 운동 동작 패턴임에도 불구하고 우수한 운동신경과 고유수용성 감각을 바탕으로 목표 주동근 자극을 효율적으로 형성하셨습니다."
        elif re.search(r"자극|타겟", clean_t):
            return "목표 주동근의 정확한 타겟점을 인지하고 고립 수축 자극을 매우 효율적으로 전달하셨습니다."
        elif re.search(r"자세|궤적", clean_t):
            return "관절 정렬 및 동작 궤적이 매우 안정적으로 제어되어 완성도 높은 운동을 수행하셨습니다."
        elif re.search(r"복압|코어|중심", clean_t):
            return "호흡 패턴을 통한 코어 복압을 견고하게 유지하여 운동 수행 시 신체 하중을 안정적으로 분산하셨습니다."

        return f"오늘 진행한 {clean_t} 수행 시 정확한 관절 정렬과 목표 주동근 자극 전달력이 매우 양호하게 관찰되었습니다."
    else:
        if re.search(r"접지|지면|발바닥", clean_t):
            return "하체 및 전신 동작 수행 시 발바닥 지면 접지력(Foot 삼각점 접지)과 아치 안정성을 보완하여 하중을 견고하게 지지해 드리겠습니다."
        elif re.search(r"흔들|불안정", clean_t):
            return "동작 수행 시 코어 복압 유지와 요·휘두 관절 복합체(LSC)의 동적 안정성을 보완하여 움직임의 흔들림을 최소화해 드리겠습니다."
        elif re.search(r"근력|힘", clean_t):
            return "점진적 과부하 트레이닝을 위해 주요 관절 주변부 지지 근력 및 코어 안정성을 지속적으로 보완해 나가겠습니다."
        elif re.search(r"가동성|범위|타이트", clean_t):
            return "타이트해진 주요 관절 주변 근막을 원활히 이완하여 정상 가동 범위(ROM)를 확보해 나가겠습니다."

        return f"다음 수업 시 {clean_t} 요소를 생체역학적으로 디테일하게 케어하여 더욱 부상 없이 완벽한 자세 정렬을 만들어 드리겠습니다."


def refine_raw_text(text, category="general"):
    if not text or not str(text).strip():
        return "미입력 (기본 평가 데이터 없음)"
    
    t = str(text).strip()
    clean_t = re.sub(r"(이|가)?\s*(닫혀있으심|닫힘|약하심|약함|부족함|약|하심|있으심|있음|보임|같음|패턴가|패턴이)$", "", t).strip()
    clean_t = re.sub(r"\s+", " ", clean_t)

    if category == "goal":
        if re.search(r"벌크업|근육증량|근성장", clean_t):
            return "점진적 과부하 트레이닝을 통한 근육량 증대 및 체격 확장(벌크업)"
        elif re.search(r"다이어트|체지방|감량", clean_t):
            return "체지방 순감량 및 골격근량 보존을 통한 신체 밸런스 라인 형성"
        return f"{clean_t} 및 신체 전반의 기능적 밸런스 회복"

    elif category == "posture":
        p_text = clean_t
        if re.search(r"전방\s*경사", p_text):
            p_text = "골반 전방 경사(Pelvic Anterior Tilt) 양상의 요추 전만 상태"
        elif re.search(r"후방\s*경사", p_text):
            p_text = "골반 후방 경사(Pelvic Posterior Tilt) 양상의 요·흉추 후만 상태"
        elif re.search(r"라운드\s*숄더|굽은\s*어깨", p_text):
            p_text = "상지교차증후군(Upper Crossed Syndrome)에 따른 라운드 숄더"
        return p_text

    elif category == "func":
        f_text = clean_t
        if re.search(r"견갑|견갑골|닫혀", f_text):
            f_text = "렛풀다운 수행 시 우측 견갑골의 불균형적 하향 회전(Depression) 및 상방 회전 가동성 제한"
        elif re.search(r"내전근|허벅지\s*안쪽", f_text):
            f_text = "고관절 내전근(Adductor Complex)의 활성도 저하 및 근력 약화"
        elif re.search(r"벗윙크|스쿼트", f_text):
            f_text = "딥 스쿼트 수행 시 굴곡 제한에 따른 벗윙크(Butt Wink) 보상 작용"
        return f_text

    elif category == "journal":
        return f"{clean_t} 중심의 맞춤형 코어 및 정렬 지도"

    return clean_t


def get_expect_badge_html(status_str):
    st_val = str(status_str).strip()
    if st_val == "높음":
        return '<span class="tr-high">🟢 높음</span>'
    elif st_val == "중간":
        return '<span class="tr-mid">🟡 중간</span>'
    elif st_val == "낮음":
        return '<span class="tr-low">🔴 낮음</span>'
    return '<span class="tr-check">❔ 확인중</span>'


# =========================================================
# 2. Supabase DB 세분화 캐싱 & 예외 처리 강화
# =========================================================
def fetch_table(table_name, columns):
    try:
        res = supabase.table(table_name).select("*").execute()
        df = pd.DataFrame(res.data)
        if df.empty:
            return pd.DataFrame(columns=columns)
        for col in columns:
            if col not in df.columns: df[col] = None
        return df[columns]
    except Exception as e:
        st.error(f"DB Fetch 에러 ({table_name}): {e}")
        return pd.DataFrame(columns=columns)

def get_cached_data():
    if "members_df" not in st.session_state: st.session_state["members_df"] = fetch_table("members", MEMBERS_COLUMNS)
    if "logs_df" not in st.session_state: st.session_state["logs_df"] = fetch_table("logs", LOGS_COLUMNS)
    if "inbody_df" not in st.session_state: st.session_state["inbody_df"] = fetch_table("inbody", INBODY_COLUMNS)
    if "sales_df" not in st.session_state: st.session_state["sales_df"] = fetch_table("sales", SALES_COLUMNS)
    if "reports_df" not in st.session_state: st.session_state["reports_df"] = fetch_table("reports", REPORTS_COLUMNS)
    if "bookings_df" not in st.session_state: st.session_state["bookings_df"] = fetch_table("bookings", BOOKINGS_COLUMNS)
    if "consultations_df" not in st.session_state: st.session_state["consultations_df"] = fetch_table("consultations", CONSULTATIONS_COLUMNS)

    return (
        st.session_state["members_df"],
        st.session_state["logs_df"],
        st.session_state["inbody_df"],
        st.session_state["sales_df"],
        st.session_state["reports_df"],
        st.session_state["bookings_df"],
        st.session_state["consultations_df"]
    )

def save_data_safe(table_name, df):
    if df.empty: return True
    data = df.to_dict(orient="records")
    int_fields = ["member_id", "log_id", "record_id", "sale_id", "report_id", "booking_id", "consult_id", "total_sessions", "remaining_sessions", "session_price", "age", "exp_re_sessions", "exp_re_price", "is_exp_configured", "amount", "exp_sessions", "exp_price"]
    float_fields = ["weight", "skeletal_muscle", "body_fat_pct"]
    bool_fields = ["sent", "delivered", "converted"]

    clean_batch = []
    for row in data:
        clean_row = {}
        for k, v in row.items():
            if pd.isna(v) or v is None: clean_row[k] = None
            elif k in int_fields: clean_row[k] = int(float(v))
            elif k in float_fields: clean_row[k] = float(v)
            elif k in bool_fields: clean_row[k] = bool(v)
            else: clean_row[k] = str(v)
        clean_batch.append(clean_row)

    try:
        supabase.table(table_name).upsert(clean_batch).execute()
        return True
    except Exception as e:
        st.error(f"🚨 DB 저장 중 오류가 발생했습니다 ({table_name}): {e}")
        return False

def save_members(df): 
    st.session_state["members_df"] = df
    return save_data_safe("members", df)

def save_logs(df): 
    st.session_state["logs_df"] = df
    return save_data_safe("logs", df)

def save_inbody(df): 
    st.session_state["inbody_df"] = df
    return save_data_safe("inbody", df)

def save_sales(df): 
    st.session_state["sales_df"] = df
    return save_data_safe("sales", df)

def save_reports(df): 
    st.session_state["reports_df"] = df
    return save_data_safe("reports", df)

def save_bookings(df): 
    st.session_state["bookings_df"] = df
    return save_data_safe("bookings", df)

def save_consultations(df):
    st.session_state["consultations_df"] = df
    return save_data_safe("consultations", df)

def update_attendance_log_and_session(member_id, date_str, start_time_str, end_time_str, new_att_val):
    try:
        logs_df = st.session_state.get("logs_df", fetch_table("logs", LOGS_COLUMNS))
        members_df = st.session_state.get("members_df", fetch_table("members", MEMBERS_COLUMNS))
        
        mask = (logs_df["member_id"].astype(str) == str(member_id)) & (logs_df["date"] == date_str) & (logs_df["start_time"] == start_time_str)
        prev_att_val = "미체크"
        
        if mask.any():
            prev_att_val = str(logs_df.loc[mask, "attendance"].values[0]).strip()
            logs_df.loc[mask, "attendance"] = new_att_val
        else:
            new_id = next_id(logs_df, "log_id")
            new_row = {
                "log_id": new_id, "member_id": member_id, "date": date_str,
                "start_time": start_time_str, "end_time": end_time_str, "exercises_json": "[]",
                "good_points": f"수업 {new_att_val} 처리", "improve_points": "",
                "sent": False, "attendance": new_att_val
            }
            logs_df = pd.concat([logs_df, pd.DataFrame([new_row])], ignore_index=True)

        save_logs(logs_df)

        m_mask = members_df["member_id"].astype(str) == str(member_id)
        if m_mask.any():
            cur_rem = safe_int(members_df.loc[m_mask, "remaining_sessions"].values[0], 0)
            
            if prev_att_val in ["미체크", ""] and new_att_val in ["출석", "결석", "노쇼"]:
                if cur_rem > 0:
                    members_df.loc[m_mask, "remaining_sessions"] = cur_rem - 1
                    save_members(members_df)
            
            elif prev_att_val in ["출석", "결석", "노쇼"] and new_att_val == "미체크":
                members_df.loc[m_mask, "remaining_sessions"] = cur_rem + 1
                save_members(members_df)

    except Exception as e:
        st.error(f"출결 동기화 및 세션 차감 오류: {e}")

def init_all_files(): pass

def next_id(df, id_col):
    if df.empty: return 1
    return int(pd.to_numeric(df[id_col], errors="coerce").fillna(0).max()) + 1


def generate_friendly_message_from_data(member_id, member_name, rem_sessions, exercises_df, good, improve):
    ex_summary = []
    weight_increases = []

    logs_df = st.session_state.get("logs_df", fetch_table("logs", LOGS_COLUMNS))
    m_past_logs = logs_df[pd.to_numeric(logs_df["member_id"], errors="coerce") == int(member_id)]

    past_max_weights = {}
    if not m_past_logs.empty:
        for _, plog in m_past_logs.iterrows():
            try:
                plist = json.loads(plog.get("exercises_json") or "[]")
                for pex in plist:
                    pitem = pex.get("종목", "").strip()
                    pw = safe_float(pex.get("중량(kg)", 0))
                    if pitem and pw > 0:
                        if pitem not in past_max_weights or pw > past_max_weights[pitem]:
                            past_max_weights[pitem] = pw
            except Exception:
                pass

    if isinstance(exercises_df, pd.DataFrame) and not exercises_df.empty:
        for _, row in exercises_df.iterrows():
            item = str(row.get("종목", "")).strip()
            if item:
                w = safe_float(row.get("중량(kg)", 0))
                c = int(safe_float(row.get("횟수", 0)))
                s = int(safe_float(row.get("세트", 0)))
                ex_summary.append(f"  • {item}: {w}kg x {c}회 x {s}세트")

                if item in past_max_weights:
                    prev_w = past_max_weights[item]
                    if w > prev_w:
                        diff = round(w - prev_w, 1)
                        weight_increases.append(f"🔥 {item} ({prev_w}kg ➡️ {w}kg, +{diff}kg 상승!)")

    ex_text = "\n".join(ex_summary) if ex_summary else "  • 전신 기초 가동성 및 코어 훈련"
    g_text = good if good else "오늘도 설정한 운동 목표 루틴을 깔끔하게 완수하셨습니다!"
    i_text = improve if improve else "다음 수업 때는 자세 정렬에 조금 더 신경 써볼게요."

    overload_text = ""
    if weight_increases:
        overload_text = "\n\n[💪 점진적 과부하 갱신!]\n" + "\n".join(weight_increases)

    next_class_text = ""
    try:
        bookings_df = st.session_state.get("bookings_df", fetch_table("bookings", BOOKINGS_COLUMNS))
        today_str = get_kst_now().date().isoformat()
        
        user_future_bookings = bookings_df[
            (bookings_df["member_id"].astype(str) == str(member_id)) &
            (bookings_df["status"] != "취소") &
            (bookings_df["date"] >= today_str)
        ].sort_values(by=["date", "time_slot"])

        if not user_future_bookings.empty:
            next_b = user_future_bookings.iloc[0]
            next_date_str = str(next_b["date"])
            next_time_str = str(next_b["time_slot"])
            next_class_text = f"\n🗓️ 다음 수업 일정: {next_date_str} ({next_time_str})"
    except Exception:
        next_class_text = ""

    return f"""안녕하세요 {member_name} 회원님! 오늘 PT 수업도 고생 많으셨습니다. 💪

[오늘 진행한 운동 루틴]
{ex_text}{overload_text}

[트레이너 피드백]
✔ 잘하신 점: {g_text}
✔ 보완할 점: {i_text}

⏳ 남은 세션: {rem_sessions}회{next_class_text}

오늘도 고생하셨습니다! 다음 수업 때도 화이팅입니다! 🔥
- 담당 트레이너 {MY_NAME} 올림 -"""


def get_gender_badge_html(gender):
    if gender == "여성":
        return '<span class="gender-badge-female">👩 여성</span>'
    elif gender == "남성":
        return '<span class="gender-badge-male">👨 남성</span>'
    return '<span style="color:#64748B;">성별미기재</span>'


def get_attendance_badge_html(status):
    st_str = str(status).strip() if pd.notna(status) else ""
    if st_str in ["출석", "출석 완료"]:
        return '<span class="status-attend">🟢 출석 완료</span>'
    elif st_str in ["결석", "노쇼", "🔴 결석(노쇼)"]:
        return '<span class="status-absent">🔴 노쇼 / 결석</span>'
    return '<span class="status-pending">⏳ 미체크</span>'


# =========================================================
# 3. Streamlit @st.dialog 기반 팝업 모달 정의
# =========================================================

# A. 상담 고객 상세 모달 팝업
if hasattr(st, "dialog"):
    @st.dialog("👤 신규 상담 고객 상세 정보 & 이관 케어")
    def show_consultation_dialog(c, consultations, members, sales):
        c_id = int(c["consult_id"])
        is_conv = bool(c.get("converted", False))
        g_badge = get_gender_badge_html(c.get("gender"))
        expect_badge = get_expect_badge_html(c.get("expect_status"))

        st.markdown(f"### **{c['name']}** 고객님")
        st.markdown(f"{g_badge} &nbsp;&nbsp; 현 상태: {expect_badge}", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:13.5px; color:#64748B;'>상담일자: {c['date']} | 연락처: {c['contact']} | 유입: {c.get('source','-')}</span>", unsafe_allow_html=True)
        st.markdown("---")

        d_tab1, d_tab2, d_tab3 = st.tabs(["📝 상담 메모 & 인테이크", "⚙️ 예상가 설정", "💳 회원 전환 & 결제 이관"])

        with d_tab1:
            edit_memo = st.text_area("💬 자세한 상담 내역 및 특이사항 메모", value=str(c.get("memo") or ""), height=120, key=f"dlg_cmemo_{c_id}")
            if st.button("💾 상담 메모 저장", type="primary", use_container_width=True, key=f"dlg_save_cmemo_{c_id}"):
                consultations.loc[consultations["consult_id"] == c_id, "memo"] = str(edit_memo)
                save_consultations(consultations)
                st.toast("상담 메모가 즉시 저장되었습니다.")
                rerun()

        with d_tab2:
            st.markdown("##### ⚙️ 신규 상담 예상 등록 금액 세팅")
            curr_c_s = safe_int(c.get("exp_sessions"), 10)
            if curr_c_s <= 0: curr_c_s = 10
            curr_c_p = safe_int(c.get("exp_price"), 70000)
            if curr_c_p <= 0: curr_c_p = 70000

            col_cs, col_cp = st.columns(2)
            n_c_s = col_cs.selectbox("예상 등록 세션", [10, 20, 30, 40, 50], index=[10, 20, 30, 40, 50].index(curr_c_s) if curr_c_s in [10, 20, 30, 40, 50] else 0, key=f"dlg_cfg_cs_{c_id}")
            n_c_p = col_cp.number_input("예상 1회 단가(원)", min_value=10000, value=curr_c_p, step=5000, key=f"dlg_cfg_cp_{c_id}")

            calc_c_tot = n_c_s * n_c_p
            st.markdown(f"<h4 style='color:{COLOR_BLUE}; text-align:right;'>예상 매출액: {calc_c_tot:,.0f}원</h4>", unsafe_allow_html=True)

            if st.button("💾 예상가 설정 저장", type="primary", use_container_width=True, key=f"dlg_save_cexp_{c_id}"):
                consultations.loc[consultations["consult_id"] == c_id, "exp_sessions"] = n_c_s
                consultations.loc[consultations["consult_id"] == c_id, "exp_price"] = n_c_p
                save_consultations(consultations)
                st.toast("신규 상담 예상 금액 설정이 저장되었습니다!")
                rerun()

        with d_tab3:
            if not is_conv:
                st.markdown("##### 💳 결제 세션/단가 지정 후 실제 회원 등록")
                col_s, col_p = st.columns(2)
                exp_sess = col_s.selectbox("실제 등록 세션(회)", [10, 20, 30, 40, 50], index=[10, 20, 30, 40, 50].index(curr_c_s) if curr_c_s in [10, 20, 30, 40, 50] else 0, key=f"dlg_csess_{c_id}")
                exp_price = col_p.number_input("실제 1회 단가(원)", min_value=10000, value=curr_c_p, step=5000, key=f"dlg_cprice_{c_id}")
                tot_amt = exp_sess * exp_price

                st.markdown(f"<h4 style='color:{COLOR_BLUE}; text-align:right;'>총 결제 확정액: {tot_amt:,.0f}원</h4>", unsafe_allow_html=True)
                
                if st.button("👥 정식 회원으로 확정 이관 등록", type="primary", use_container_width=True, key=f"dlg_btn_conv_{c_id}"):
                    new_m_id = next_id(members, "member_id")
                    today_obj = get_kst_now().date()
                    auto_week = get_week_of_month(today_obj)

                    new_m = {
                        "member_id": new_m_id, "name": c["name"], "contact": c["contact"],
                        "birth_date": "1995-01-01", "reg_date": today_obj.isoformat(),
                        "total_sessions": int(exp_sess), "remaining_sessions": int(exp_sess),
                        "trainer": MY_NAME, "status": "Active", "goal": c.get("goal") or "다이어트 및 체형교정",
                        "session_price": int(exp_price), "branch": "개인 PT", "gender": c.get("gender", "여성"), "age": 28,
                        "tr_expect": "확인중", "re_status": "미지정", "week_group": auto_week,
                        "memo": f"[신규상담 이관 메모]\n{edit_memo}", 
                        "survey_json": json.dumps({"pain": edit_memo, "exp": "신규 상담 후 전환 등록"}, ensure_ascii=False),
                        "exp_re_sessions": 10, "exp_re_price": int(exp_price), "is_exp_configured": 0
                    }
                    members = pd.concat([members, pd.DataFrame([new_m])], ignore_index=True)
                    save_members(members)

                    db_sales = fetch_table("sales", SALES_COLUMNS)
                    new_s = {
                        "sale_id": next_id(db_sales, "sale_id"), "member_id": new_m_id,
                        "date": today_obj.isoformat(), "product_name": f"PT {exp_sess}회 신규등록 (상담전환)",
                        "amount": tot_amt, "pay_type": "카드"
                    }
                    updated_sales = pd.concat([db_sales, pd.DataFrame([new_s])], ignore_index=True)
                    save_sales(updated_sales)

                    consultations.loc[consultations["consult_id"] == c_id, "converted"] = True
                    save_consultations(consultations)

                    st.toast(f"🎉 '{c['name']}' 고객이 {exp_sess}회({tot_amt:,.0f}원)로 성공적으로 이관 등록되었습니다!")
                    rerun()
            else:
                st.success("🟢 이미 정식 회원으로 등록 이관이 완료된 고객입니다.")
                if st.button("🔄 이관 상태 취소 및 상담 진행중으로 초기화", key=f"dlg_reset_conv_{c_id}"):
                    consultations.loc[consultations["consult_id"] == c_id, "converted"] = False
                    save_consultations(consultations)
                    st.toast("상담 상태가 '상담 진행중'으로 초기화되었습니다.")
                    rerun()

# B. 기존 회원 상세 모달 팝업 (회원관리 및 재등록 통합 뷰어)
if hasattr(st, "dialog"):
    @st.dialog("👤 회원통합 상세 모달 & 1:1 케어")
    def show_member_dialog(m, members, logs, inbody_df, logs_df):
        m_id = int(m["member_id"])
        total = int(pd.to_numeric(m.get("total_sessions", 0), errors="coerce"))
        rem = int(pd.to_numeric(m.get("remaining_sessions", 0), errors="coerce"))
        done = max(0, total - rem)
        gender_badge = get_gender_badge_html(m.get("gender"))
        expect_badge = get_expect_badge_html(m.get("tr_expect"))

        st.markdown(f"### **{m['name']}** 회원님")
        st.markdown(f"{gender_badge} &nbsp;&nbsp; 현 상태: {expect_badge}", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:13px; color:#64748B;'>연락처: {m['contact']} | 등록일: {m['reg_date']} | 잔여: <b>{rem}회</b> / 총 {total}회</span>", unsafe_allow_html=True)
        st.markdown("---")

        m_tab1, m_tab2, m_tab3 = st.tabs(["📝 특이사항 메모 & 사전설문", "📜 수업 진행 이력", "⚙️ 재등록 예상가 & AI 상담 스크립트"])

        with m_tab1:
            try: survey_dict = json.loads(m.get("survey_json") or "{}")
            except Exception: survey_dict = {}

            edit_memo = st.text_area("💬 회원 개별 특이사항 메모", value=str(m.get("memo") or ""), height=90, key=f"dlg_mmemo_{m_id}")
            
            st.markdown("##### 🩺 PT 사전 인테이크 설문")
            sur_c1, sur_c2 = st.columns(2)
            s_med = sur_c1.text_input("병력 이력", value=survey_dict.get("medical", ""), key=f"dlg_smed_{m_id}")
            s_pain = sur_c2.text_input("통증/불편 부위", value=survey_dict.get("pain", ""), key=f"dlg_spain_{m_id}")

            if st.button("💾 메모 및 설문 저장", type="primary", use_container_width=True, key=f"dlg_save_mmemo_{m_id}"):
                new_sur = json.dumps({"medical": s_med, "pain": s_pain, "exp": survey_dict.get("exp",""), "habit": survey_dict.get("habit","")}, ensure_ascii=False)
                members.loc[pd.to_numeric(members["member_id"], errors="coerce") == m_id, "memo"] = str(edit_memo)
                members.loc[pd.to_numeric(members["member_id"], errors="coerce") == m_id, "survey_json"] = str(new_sur)
                save_members(members)
                st.toast("회원 메모 및 설문 정보가 저장되었습니다.")
                rerun()

        with m_tab2:
            m_logs = logs[pd.to_numeric(logs["member_id"], errors="coerce") == m_id].sort_values("date", ascending=False)
            if m_logs.empty:
                st.caption("기록된 과거 수업일지가 없습니다.")
            else:
                for _, l_row in m_logs.iterrows():
                    st.markdown(f"""
                    <div style="background:#F8FAFC; border-left:4px solid {COLOR_BLUE}; border-radius:8px; padding:10px 14px; margin-bottom:6px;">
                        <b>📅 {l_row['date']} ({l_row.get('start_time','-')} ~ {l_row.get('end_time','-')})</b><br/>
                        <span style="font-size:13px; color:#334155;">✔ 잘한점: {l_row.get('good_points','-')}</span><br/>
                        <span style="font-size:13px; color:#334155;">✔ 보완점: {l_row.get('improve_points','-')}</span>
                    </div>
                    """, unsafe_allow_html=True)

        with m_tab3:
            curr_exp_sess = safe_int(m.get("exp_re_sessions"), 10)
            curr_exp_price = safe_int(m.get("exp_re_price"), safe_int(m.get("session_price"), 70000))

            ec1, ec2 = st.columns(2)
            n_exp_s = ec1.selectbox("예상 재등록 세션", [10, 20, 30, 40, 50], index=[10, 20, 30, 40, 50].index(curr_exp_sess) if curr_exp_sess in [10, 20, 30, 40, 50] else 0, key=f"dlg_cfg_s_{m_id}")
            n_exp_p = ec2.number_input("예상 1회 단가(원)", min_value=10000, value=curr_exp_price, step=5000, key=f"dlg_cfg_p_{m_id}")

            if st.button("예상 재등록 금액 저장", key=f"dlg_save_exp_{m_id}"):
                members.loc[pd.to_numeric(members["member_id"], errors="coerce") == m_id, "exp_re_sessions"] = n_exp_s
                members.loc[pd.to_numeric(members["member_id"], errors="coerce") == m_id, "exp_re_price"] = n_exp_p
                members.loc[pd.to_numeric(members["member_id"], errors="coerce") == m_id, "is_exp_configured"] = 1
                save_members(members)
                st.toast("예상 재등록 금액 설정이 저장되었습니다.")
                rerun()


# =========================================================
# 4. 페이지 1: 센터 대시보드
# =========================================================
def page_dashboard(members, logs, sales, reports, bookings):
    st.title("📊 PT Account 통합 대시보드")

    kst_now = get_kst_now()
    today = kst_now.date()
    today_str = today.isoformat()
    total_m = len(members)
    rem_sum = int(pd.to_numeric(members["remaining_sessions"], errors="coerce").fillna(0).sum())

    this_month = pd.Period(today, "M")
    
    logs_copy = logs.copy()
    logs_copy["month_p"] = pd.to_datetime(logs_copy["date"], errors="coerce").dt.to_period("M")
    m_logs = logs_copy[logs_copy["month_p"] == this_month]
    m_logs_count = len(m_logs)

    current_sales = st.session_state.get("sales_df", sales)
    sales_copy = current_sales.copy()
    sales_copy["month_p"] = pd.to_datetime(sales_copy["date"], errors="coerce").dt.to_period("M")
    m_sales = sales_copy[sales_copy["month_p"] == this_month]
    real_revenue = pd.to_numeric(m_sales["amount"], errors="coerce").fillna(0).sum()

    if "dash_selected_metric" not in st.session_state:
        st.session_state["dash_selected_metric"] = None

    cols = st.columns(5)
    
    with cols[0]:
        st.markdown(f'<div class="pt-metric"><div class="label">총 관리 회원 수</div><div class="value">{total_m}명</div></div>', unsafe_allow_html=True)
        if st.button("📋 회원 목록 보기", key="btn_view_members", use_container_width=True):
            st.session_state["dash_selected_metric"] = "members" if st.session_state["dash_selected_metric"] != "members" else None
            rerun()

    with cols[1]:
        st.markdown(f'<div class="pt-metric"><div class="label">전체 남은 세션 총합</div><div class="value accent">{rem_sum}회</div></div>', unsafe_allow_html=True)
        if st.button("🔍 세션 현황 보기", key="btn_view_sessions", use_container_width=True):
            st.session_state["dash_selected_metric"] = "sessions" if st.session_state["dash_selected_metric"] != "sessions" else None
            rerun()

    with cols[2]:
        st.markdown(f'<div class="pt-metric"><div class="label">이달의 진행 수업 수</div><div class="value accent">{m_logs_count}회</div></div>', unsafe_allow_html=True)
        if st.button("📝 이달 수업일지 보기", key="btn_view_logs", use_container_width=True):
            st.session_state["dash_selected_metric"] = "logs" if st.session_state["dash_selected_metric"] != "logs" else None
            rerun()

    with cols[3]:
        st.markdown(f'<div class="pt-metric"><div class="label">작성된 바이오 프로파일</div><div class="value accent">{len(reports)}건</div></div>', unsafe_allow_html=True)
        if st.button("📑 리포트 목록 보기", key="btn_view_reports", use_container_width=True):
            st.session_state["dash_selected_metric"] = "reports" if st.session_state["dash_selected_metric"] != "reports" else None
            rerun()

    with cols[4]:
        st.markdown(f'<div class="pt-metric"><div class="label">이달의 누적 매출액</div><div class="value accent">{real_revenue:,.0f}원</div></div>', unsafe_allow_html=True)
        if st.button("💰 이달 매출 내역 보기", key="btn_view_sales", use_container_width=True):
            st.session_state["dash_selected_metric"] = "sales" if st.session_state["dash_selected_metric"] != "sales" else None
            rerun()

    sel_metric = st.session_state.get("dash_selected_metric")
    if sel_metric:
        st.write("")
        st.markdown('<div class="pt-card" style="border: 2px solid #2563EB;">', unsafe_allow_html=True)
        
        if sel_metric == "members":
            st.subheader("👥 전체 관리 회원 상세 리스트")
            for _, m in members.iterrows():
                g_badge = get_gender_badge_html(m.get("gender"))
                st.markdown(f"""
                <div class="custom-item-card">
                    <div>
                        <span style="font-size:16px; font-weight:800; color:{COLOR_NAVY};">👤 {m['name']} 회원님</span> {g_badge}
                        <span style="font-size:13px; color:#64748B; margin-left:10px;">📞 {m['contact']} | 🗓️ 등록일: {m['reg_date']}</span>
                    </div>
                    <div style="font-size:13.5px; font-weight:700; color:{COLOR_BLUE};">
                        🎯 목표: {m.get('goal','-')} | 잔여 세션: <b>{int(m['remaining_sessions'])}회</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        elif sel_metric == "sessions":
            st.subheader("📊 회원별 잔여 PT 세션 현황 리스트")
            for _, m in members.sort_values("remaining_sessions").iterrows():
                tot = int(m['total_sessions'])
                rem = int(m['remaining_sessions'])
                done = tot - rem
                g_badge = get_gender_badge_html(m.get("gender"))
                st.markdown(f"""
                <div class="custom-item-card">
                    <div>
                        <span style="font-size:16px; font-weight:800; color:{COLOR_NAVY};">👤 {m['name']} 회원님</span> {g_badge}
                        <span style="font-size:13px; color:#64748B; margin-left:10px;">진행 완료: {done}회 / 총 {tot}회</span>
                    </div>
                    <div style="font-size:16px; font-weight:800; color:#E11D48;">
                        ⏳ 남은 세션 : {rem}회
                    </div>
                </div>
                """, unsafe_allow_html=True)

        elif sel_metric == "logs":
            st.subheader(f"📝 {today.year}년 {today.month}월 진행된 수업일지 리스트")
            if m_logs.empty:
                st.info("이번 달 진행된 수업일지 내역이 없습니다.")
            else:
                merged_l = m_logs.merge(members[["member_id", "name", "gender"]], on="member_id", how="left")
                for _, l in merged_l.sort_values("date", ascending=False).iterrows():
                    g_badge = get_gender_badge_html(l.get("gender"))
                    att_badge = get_attendance_badge_html(l.get("attendance"))
                    st.markdown(f"""
                    <div class="custom-item-card">
                        <div>
                            <span style="font-size:16px; font-weight:800; color:{COLOR_NAVY};">👤 {l.get('name','회원')} 회원님</span> {g_badge} {att_badge}
                            <div style="font-size:12.5px; color:#64748B; margin-top:4px;">✔ 피드백: {l.get('good_points','-')}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-weight:800; color:{COLOR_BLUE};">⏰ {l['date']} ({l['start_time']} ~ {l['end_time']})</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        elif sel_metric == "reports":
            st.subheader("📑 작성 완료된 3-STEP 바이오 프로파일 목록")
            if reports.empty:
                st.info("작성된 리포트가 없습니다.")
            else:
                merged_r = reports.merge(members[["member_id", "name", "gender"]], on="member_id", how="left")
                for _, r in merged_r.sort_values("date", ascending=False).iterrows():
                    g_badge = get_gender_badge_html(r.get("gender"))
                    deliv_text = '<span style="background:#DCFCE7; color:#15803D; padding:2px 8px; border-radius:10px; font-size:12px; font-weight:800;">✅ 전달완료</span>' if r.get("delivered") else '<span style="background:#F1F5F9; color:#64748B; padding:2px 8px; border-radius:10px; font-size:12px; font-weight:800;">⏳ 미전달</span>'
                    st.markdown(f"""
                    <div class="custom-item-card">
                        <div>
                            <span style="font-size:16px; font-weight:800; color:{COLOR_NAVY};">📄 {r.get('name','회원')} 회원의 바이오 프로파일</span> {g_badge} {deliv_text}
                            <div style="font-size:13px; color:#64748B; margin-top:4px;">🎯 운동목적: {r.get('goal_text','-')}</div>
                        </div>
                        <div style="font-weight:800; color:#64748B;">
                            🗓️ 발행일: {r['date']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        elif sel_metric == "sales":
            st.subheader(f"💰 {today.year}년 {today.month}월 결제 매출 상세 내역")
            if m_sales.empty:
                st.info("이번 달 집계된 매출 내역이 없습니다.")
            else:
                merged_sal = m_sales.merge(members[["member_id", "name", "gender"]], on="member_id", how="left")
                for _, s in merged_sal.sort_values("date", ascending=False).iterrows():
                    g_badge = get_gender_badge_html(s.get("gender")) if pd.notna(s.get("gender")) else ""
                    pay_amt = safe_float(s.get("amount", 0))
                    st.markdown(f"""
                    <div class="custom-item-card">
                        <div>
                            <span style="font-size:16px; font-weight:800; color:{COLOR_NAVY};">👤 {s.get('name','회원')} 회원님</span> {g_badge}
                            <span style="font-size:13px; color:#64748B; margin-left:10px;">💳 상품명: {s.get('product_name','-')} ({s.get('pay_type','카드')})</span>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:18px; font-weight:900; color:{COLOR_BLUE};">{pay_amt:,.0f}원</div>
                            <div style="font-size:12px; color:#64748B;">🗓️ 결제일: {s['date']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        st.write("")
        if st.button("❌ 상세 리스트 닫기", key="btn_close_metric_detail"):
            st.session_state["dash_selected_metric"] = None
            rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")

    expiring_members = members[pd.to_numeric(members["remaining_sessions"], errors="coerce").fillna(0) <= 3]
    if not expiring_members.empty:
        st.markdown('<div class="pt-card" style="border-left: 5px solid #E11D48; background-color:#FFF1F2;">', unsafe_allow_html=True)
        st.markdown("##### 🚨 **세션 만료 임박 회원 알림 (재등록 상담 필요)**")
        exp_names = [f"<b>{m['name']}</b> ({get_gender_badge_html(m.get('gender'))}, 잔여 <b>{int(m['remaining_sessions'])}회</b>)" for _, m in expiring_members.iterrows()]
        st.markdown(f"현재 세션이 3회 이하로 남은 회원: &nbsp;&nbsp; {' &nbsp; | &nbsp; '.join(exp_names)}", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 대형 달력 레이아웃
    st.markdown('<div class="pt-card">', unsafe_allow_html=True)
    st.markdown("#### 📅 수업 일정 달력")

    if "dash_selected_date" not in st.session_state:
        st.session_state["dash_selected_date"] = today.isoformat()
    if "dash_cal_year" not in st.session_state:
        st.session_state["dash_cal_year"] = today.year
    if "dash_cal_month" not in st.session_state:
        st.session_state["dash_cal_month"] = today.month

    active_bookings = bookings[bookings["status"] != "취소"]

    d_year = st.session_state["dash_cal_year"]
    d_month = st.session_state["dash_cal_month"]

    nav1, nav2, nav3 = st.columns([1, 4, 1])
    if nav1.button("◀ 이전 달", key="dash_prev_m", use_container_width=True):
        d_month -= 1
        if d_month == 0: d_month = 12; d_year -= 1
        st.session_state["dash_cal_year"], st.session_state["dash_cal_month"] = d_year, d_month
        rerun()
    nav2.markdown(f"<h3 style='text-align:center;margin:0;color:{COLOR_NAVY};'>{d_year}년 {d_month}월</h3>", unsafe_allow_html=True)
    if nav3.button("다음 달 ▶", key="dash_next_m", use_container_width=True):
        d_month += 1
        if d_month == 13: d_month = 1; d_year += 1
        st.session_state["dash_cal_year"], st.session_state["dash_cal_month"] = d_year, d_month
        rerun()

    st.write("")
    weekday_cols = st.columns(7)
    for wc, label in zip(weekday_cols, WEEKDAY_LABELS_KR):
        wc.markdown(f"<div class='cal-weekday'>{label}</div>", unsafe_allow_html=True)

    cal_obj = calendar.Calendar(firstweekday=6)
    month_weeks = cal_obj.monthdayscalendar(d_year, d_month)

    for week in month_weeks:
        week_cols = st.columns(7)
        for wc, day_num in zip(week_cols, week):
            if day_num == 0:
                wc.write("")
                continue
            this_date = date(d_year, d_month, day_num).isoformat()
            day_b_cnt = len(active_bookings[active_bookings["date"] == this_date])
            is_selected = (this_date == st.session_state["dash_selected_date"])
            is_today = (this_date == today.isoformat())

            if day_b_cnt > 0:
                label = f"🟢 {day_num}일 ({day_b_cnt}건)"
            else:
                label = f"{day_num}"

            btn_type = "primary" if is_selected else "secondary"
            if wc.button(label, key=f"dash_cal_day_{this_date}", use_container_width=True, type=btn_type):
                st.session_state["dash_selected_date"] = this_date
                rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    sel_date_str = st.session_state["dash_selected_date"]
    st.markdown('<div class="pt-card" style="border-top: 4px solid #2563EB;">', unsafe_allow_html=True)
    st.markdown(f"#### 📌 **{sel_date_str}** 상세 수업 스케줄")

    day_bookings = active_bookings[active_bookings["date"] == sel_date_str]

    if day_bookings.empty:
        st.info(f"{sel_date_str}에 예정된 수업 예약이 없습니다.")
    else:
        merged_day_b = day_bookings.merge(members[["member_id", "name", "gender", "total_sessions", "remaining_sessions", "memo", "survey_json"]], on="member_id", how="inner")
        
        if merged_day_b.empty:
            st.info(f"{sel_date_str}에 예정된 수업 예약이 없습니다.")
        else:
            st.success(f"총 **{len(merged_day_b)}개**의 수업이 예약되어 있습니다.")

            is_today_kst = (sel_date_str == today_str)

            for idx, b_row in merged_day_b.sort_values("time_slot").iterrows():
                b_id = b_row["booking_id"]
                s_time = str(b_row.get("time_slot") or "10:00").strip()
                sh, sm = map(int, s_time.split(":"))
                e_time = (datetime(2026, 1, 1, sh, sm) + timedelta(minutes=50)).strftime("%H:%M")
                
                m_id = int(b_row["member_id"])
                m_name = b_row.get("name") or "회원"
                m_gender = b_row.get("gender") or "남성"
                rem_s = int(b_row.get("remaining_sessions", 0))
                
                m_memo = str(b_row.get("memo") or "").strip()
                try:
                    s_dict = json.loads(b_row.get("survey_json") or "{}")
                    s_pain = s_dict.get("pain", "").strip()
                except Exception:
                    s_pain = ""
                
                caution_text = ""
                if s_pain: caution_text = f"🩺 통증: {s_pain}"
                elif m_memo: caution_text = f"💬 메모: {m_memo[:15]}..."

                caution_html = f'<span style="background:#FEF2F2; color:#DC2626; padding:2px 8px; border-radius:10px; font-size:12px; font-weight:800; border:1px solid #FECDD3; margin-left:6px;">{caution_text}</span>' if caution_text else ""
                
                m_log = logs[
                    (logs["date"].astype(str) == sel_date_str) & 
                    (pd.to_numeric(logs["member_id"], errors="coerce") == m_id) & 
                    (logs["start_time"].astype(str) == s_time)
                ]
                
                att_status = "미체크"
                if not m_log.empty:
                    cur_att = str(m_log.iloc[0].get("attendance") or "").strip()
                    if cur_att in ["출석", "결석", "노쇼"]:
                        att_status = cur_att

                g_badge = get_gender_badge_html(m_gender)
                att_badge = get_attendance_badge_html(att_status)
                rem_badge = f'<span class="rem-badge">⏳ 잔여 {rem_s}회</span>'

                st.markdown(f"""
                <div style="background:#F8FAFC; border-left:4px solid {COLOR_BLUE}; border-radius:10px; padding:14px 20px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-size:17px; font-weight:800; color:{COLOR_NAVY};">👤 {m_name} 회원님</span> {g_badge} {rem_badge} {att_badge} {caution_html}
                        </div>
                        <div style="font-weight:800; font-size:15px; color:{COLOR_BLUE};">
                            ⏰ {s_time} ~ {e_time}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if is_today_kst:
                    btn_c1, btn_c2, btn_c3, btn_c4 = st.columns([1, 1, 1, 1])
                    if btn_c1.button("🟢 출석 (-1회)", key=f"dash_att_btn_{m_id}_{idx}_{s_time}", use_container_width=True):
                        update_attendance_log_and_session(m_id, sel_date_str, s_time, e_time, "출석")
                        st.toast(f"🎉 {m_name} 회원 출석 처리 완료 (잔여 세션 -1 차감)")
                        rerun()

                    if btn_c2.button("🔴 결석/노쇼 (-1회)", key=f"dash_abs_btn_{m_id}_{idx}_{s_time}", use_container_width=True):
                        update_attendance_log_and_session(m_id, sel_date_str, s_time, e_time, "결석")
                        st.toast(f"🔴 {m_name} 회원 노쇼/결석 처리 완료 (잔여 세션 -1 차감)")
                        rerun()

                    if btn_c3.button("🔄 출결 초기화", key=f"dash_reset_btn_{m_id}_{idx}_{s_time}", use_container_width=True):
                        update_attendance_log_and_session(m_id, sel_date_str, s_time, e_time, "미체크")
                        st.toast(f"🔄 {m_name} 회원 출결 초기화 완료 (잔여 세션 +1 복구)")
                        rerun()

                    if btn_c4.button("❌ 예약 취소", key=f"dash_cancel_btn_{b_id}_{idx}_{s_time}", use_container_width=True):
                        bookings.loc[bookings["booking_id"] == b_id, "status"] = "취소"
                        save_bookings(bookings)
                        st.toast(f"{m_name} 회원의 {s_time} 예약이 취소되었습니다.")
                        rerun()
                else:
                    col_canc, _ = st.columns([1.2, 5])
                    if col_canc.button("❌ 예약 취소", key=f"dash_cancel_btn_past_{b_id}_{idx}_{s_time}"):
                        bookings.loc[bookings["booking_id"] == b_id, "status"] = "취소"
                        save_bookings(bookings)
                        st.toast(f"{m_name} 회원의 {s_time} 예약이 취소되었습니다.")
                        rerun()

    st.markdown("---")
    st.markdown(f"##### ➕ **{sel_date_str}** 신규 수업 예약 등록")

    if members.empty:
        st.info("예약을 등록하려면 먼저 '회원 관리'에서 회원을 등록해 주세요.")
    else:
        valid_slots = []
        for slot in TIME_SLOTS:
            sh, sm = map(int, slot.split(":"))
            if sel_date_str == today_str:
                if sh > kst_now.hour:
                    valid_slots.append(slot)
            elif sel_date_str > today_str:
                valid_slots.append(slot)

        if not valid_slots:
            st.warning(f"⚠️ {sel_date_str}의 예약 가능한 남은 운영 시간대가 없습니다.")
        else:
            col_p1, col_p2 = st.columns([1.5, 3])

            with col_p1:
                sel_slot = st.selectbox("시간대 선택", valid_slots, index=0, key="dash_time_selector")

            with col_p2:
                search_q = st.text_input("회원 검색", placeholder="이름을 입력하세요", key="dash_search_input")
                candidates = members[members["name"].astype(str).str.contains(search_q, na=False)] if search_q else members

                if not candidates.empty:
                    cand_options = candidates.apply(lambda m: f"{m['name']} ({m.get('gender','남성')}, 잔여 {int(pd.to_numeric(m['remaining_sessions'], errors='coerce') or 0)}회)", axis=1).tolist()
                    cand_idx = st.selectbox("예약할 회원 선택", range(len(cand_options)), format_func=lambda i: cand_options[i], key="dash_cand_select")

                    if st.button("✅ 선택한 시간으로 수업 예약 확정", type="primary", use_container_width=True, key="dash_btn_confirm_booking"):
                        chosen = candidates.iloc[cand_idx]
                        chosen_rem_s = safe_int(chosen.get("remaining_sessions"), 0)

                        if chosen_rem_s <= 0:
                            st.error(f"⚠️ {chosen['name']} 회원의 잔여 세션이 0회입니다! 세션 재등록 후 예약을 진행해 주세요.")
                        else:
                            dup_check = active_bookings[(active_bookings["date"] == sel_date_str) & (active_bookings["time_slot"] == sel_slot)]
                            if not dup_check.empty:
                                st.error("⚠️ 예약할 수 없습니다! 해당 날짜와 시간대에 이미 등록된 수업이 있습니다.")
                            else:
                                new_booking = {
                                    "booking_id": next_id(bookings, "booking_id"),
                                    "member_id": int(chosen["member_id"]), "date": sel_date_str,
                                    "time_slot": sel_slot, "status": "예약됨",
                                }
                                bookings = pd.concat([bookings, pd.DataFrame([new_booking])], ignore_index=True)
                                save_bookings(bookings)
                                st.toast(f"{chosen['name']} 회원이 {sel_date_str} {sel_slot}에 예약되었습니다.")
                                rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="pt-card">', unsafe_allow_html=True)
    st.markdown("#### 🎯 당월 수업 출결 및 소진 이행률")
    if logs.empty:
        st.caption("기록된 수업 일지가 없습니다.")
    else:
        m_logs_chart = logs[pd.to_datetime(logs["date"], errors="coerce").dt.to_period("M") == this_month]
        if m_logs_chart.empty:
            st.caption("이번 달 진행된 수업 기록이 아직 없습니다.")
        else:
            att_counts = m_logs_chart["attendance"].value_counts()
            attend_c = att_counts.get("출석", 0) + att_counts.get("출석 완료", 0)
            absent_c = att_counts.get("결석", 0) + att_counts.get("노쇼", 0)
            pending_c = len(m_logs_chart) - (attend_c + absent_c)

            labels = ["🟢 출석 완료", "🔴 결석/노쇼", "⏳ 미체크"]
            values = [attend_c, absent_c, max(0, pending_c)]
            colors = ["#22C55E", "#EF4444", "#94A3B8"]

            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker_colors=colors)])
            fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 5. 페이지: 통합 신규 상담 & 재등록 파이프라인 관리 탭 (NameError 보완 및 logs 인자 전달)
# =========================================================
def page_consultations(consultations, members, sales, logs):
    st.title("💡 신규 상담 & 재등록 파이프라인 관리")

    today = get_kst_now().date()
    curr_weeks = get_month_weeks_list(today.year, today.month)

    # 1. 신규 상담 수동 세팅 기반 예상 매출 단순 합계 (미전환건 대상)
    unconverted_consults = consultations[consultations["converted"] != True]
    
    consult_pipeline_amount = 0
    for _, uc in unconverted_consults.iterrows():
        c_exp_s = safe_int(uc.get("exp_sessions"), 10)
        if c_exp_s <= 0: c_exp_s = 10
        c_exp_p = safe_int(uc.get("exp_price"), 70000)
        if c_exp_p <= 0: c_exp_p = 70000
        
        c_st = str(uc.get("expect_status", "")).strip()
        if c_st in ["높음", "중간", "확인중"]:
            consult_pipeline_amount += (c_exp_s * c_exp_p)

    # 2. 기존 회원 재등록 예상 매출 단순 합계 (가중치 제거 100% 원금 합산)
    re_pipeline_amount = 0
    re_high_amount = 0
    re_mid_amount = 0

    chart_data_tr = []
    for r in curr_weeks:
        sub = members[members["week_group"] == r]
        sub_exp_amounts = []
        for _, sm in sub.iterrows():
            tr_exp = str(sm.get("tr_expect", "")).strip()
            re_st = str(sm.get("re_status", "")).strip()
            is_cfg = bool(safe_int(sm.get("is_exp_configured"), 0) == 1)

            if tr_exp in ["이탈", "낮음"] or re_st in ["이탈", "전월이탈"] or not is_cfg:
                calc_amt = 0
            else:
                e_sess = safe_int(sm.get("exp_re_sessions"), 10)
                e_price = safe_int(sm.get("exp_re_price"), safe_int(sm.get("session_price"), 70000))
                calc_amt = e_sess * e_price
            sub_exp_amounts.append(calc_amt)
        
        sub["calc_exp_amt"] = sub_exp_amounts
        c_tr_high = len(sub[sub["tr_expect"] == "높음"])
        c_tr_mid = len(sub[sub["tr_expect"] == "중간"])
        c_tr_low = len(sub[(sub["tr_expect"] == "낮음") | (sub["tr_expect"] == "이탈")])
        c_tr_check = len(sub[sub["tr_expect"] == "확인중"])

        week_tr_sum_amount = sub["calc_exp_amt"].sum() if not sub.empty else 0
        re_pipeline_amount += week_tr_sum_amount

        high_sum = sub[sub["tr_expect"] == "높음"]["calc_exp_amt"].sum() if not sub.empty else 0
        mid_sum = sub[sub["tr_expect"] == "중간"]["calc_exp_amt"].sum() if not sub.empty else 0
        re_high_amount += high_sum
        re_mid_amount += mid_sum

        chart_data_tr.append({
            "주차": r, "🟢 높음": c_tr_high, "🟡 중간": c_tr_mid, "🔴 낮음/이탈": c_tr_low, "❔ 확인중": c_tr_check, "예상 매출액(원)": week_tr_sum_amount
        })

    df_tr = pd.DataFrame(chart_data_tr)
    tot_exp_grand = consult_pipeline_amount + re_pipeline_amount

    st.markdown("##### 💡 당월 파이프라인 통합 예상 매출액 단순 합계")
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    p_col1.metric("🔥 총 예상합계 (신규+재등록)", f"{tot_exp_grand:,.0f}원")
    p_col2.metric("💡 신규 상담 예상 합계", f"{consult_pipeline_amount:,.0f}원")
    p_col3.metric("🎯 재등록 예상 합계", f"{re_pipeline_amount:,.0f}원")
    p_col4.metric("🟢 재등록 확정형 (높음)", f"{re_high_amount:,.0f}원")

    st.write("")

    # 상단 분석 차트 탭
    st.markdown('<div class="pt-card">', unsafe_allow_html=True)
    st.subheader(f"📊 {today.year}년 {today.month}월 상담 & 재등록 파이프라인 동향")
    
    chart_tab1, chart_tab2, chart_tab3 = st.tabs([
        "💡 신규 상담 가능성 & 전환율 차트", 
        "🎯 기존 회원 주차별 재등록 차트", 
        "📋 주차별 금액 상세 집계표"
    ])

    with chart_tab1:
        if consultations.empty:
            st.info("등록된 신규 상담 데이터가 없습니다.")
        else:
            c_high = len(consultations[consultations["expect_status"] == "높음"])
            c_mid = len(consultations[consultations["expect_status"] == "중간"])
            c_low = len(consultations[consultations["expect_status"] == "낮음"])
            c_check = len(consultations[(consultations["expect_status"] == "확인중") | (consultations["expect_status"].isna())])
            c_converted = len(consultations[consultations["converted"] == True])

            fig_c = go.Figure()
            fig_c.add_trace(go.Bar(x=["상담 모수"], y=[c_high], name="🟢 높음", marker_color="#22C55E"))
            fig_c.add_trace(go.Bar(x=["상담 모수"], y=[c_mid], name="🟡 중간", marker_color="#EAB308"))
            fig_c.add_trace(go.Bar(x=["상담 모수"], y=[c_low], name="🔴 낮음", marker_color="#EF4444"))
            fig_c.add_trace(go.Bar(x=["상담 모수"], y=[c_check], name="❔ 확인중", marker_color="#94A3B8"))

            fig_c.update_layout(
                barmode="stack", height=280, margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", yaxis=dict(title="고객 수 (명)", dtick=1)
            )
            
            cc_c1, cc_c2 = st.columns([2.5, 1])
            with cc_c1: st.plotly_chart(fig_c, use_container_width=True)
            with cc_c2:
                st.markdown("<div style='padding-top:20px;'></div>", unsafe_allow_html=True)
                st.metric("총 상담 누적 모수", f"{len(consultations)}명")
                st.metric("🟢 회원 등록 전환 완료", f"{c_converted}명")

    with chart_tab2:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(x=df_tr["주차"], y=df_tr["🟢 높음"], name="🟢 높음", marker_color="#22C55E"))
        fig1.add_trace(go.Bar(x=df_tr["주차"], y=df_tr["🟡 중간"], name="🟡 중간", marker_color="#EAB308"))
        fig1.add_trace(go.Bar(x=df_tr["주차"], y=df_tr["🔴 낮음/이탈"], name="🔴 낮음/이탈", marker_color="#EF4444"))
        fig1.add_trace(go.Bar(x=df_tr["주차"], y=df_tr["❔ 확인중"], name="❔ 확인중", marker_color="#94A3B8"))

        fig1.update_layout(
            barmode="stack", height=280, margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", yaxis=dict(title="회원 수 (명)", dtick=1)
        )
        st.plotly_chart(fig1, use_container_width=True)

    with chart_tab3:
        df_tr_disp = df_tr.copy()
        total_row = {
            "주차": "합계 (Total)", "🟢 높음": df_tr_disp["🟢 높음"].sum(), "🟡 중간": df_tr_disp["🟡 중간"].sum(),
            "🔴 낮음/이탈": df_tr_disp["🔴 낮음/이탈"].sum(), "❔ 확인중": df_tr_disp["❔ 확인중"].sum(), "예상 매출액(원)": df_tr_disp["예상 매출액(원)"].sum()
        }
        df_tr_disp = pd.concat([df_tr_disp, pd.DataFrame([total_row])], ignore_index=True)
        df_tr_disp["예상 매출액(원)"] = df_tr_disp["예상 매출액(원)"].apply(lambda v: f"{v:,.0f}원")
        st.dataframe(df_tr_disp, use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 메인 관리 서브 탭
    main_m_tab1, main_m_tab2 = st.tabs(["💡 신규 상담 고객 관리", "🎯 기존 회원 재등록 주차별 관리"])

    # === [서브 탭 1: 신규 상담 고객 관리] ===
    with main_m_tab1:
        st.markdown("##### ➕ 신규 오프라인/온라인 상담 고객 등록")
        with st.expander("📝 신규 상담 등록 폼 열기", expanded=True):
            with st.form("consult_form", clear_on_submit=True):
                cc1, cc2, cc3 = st.columns(3)
                c_name = cc1.text_input("상담 고객 이름 *", placeholder="예: 홍길동")
                c_contact = cc2.text_input("연락처 * (숫자만)", placeholder="01012345678")
                c_gender = cc3.selectbox("성별 *", ["여성", "남성"])

                cc4, cc5, cc6 = st.columns(3)
                c_goal = cc4.text_input("희망 운동 목적", placeholder="예: 다이어트, 체형교정, 바디프로필")
                c_source = cc5.selectbox("유입 경로", ["네이버/인스타그램", "지인 추천", "길거리/간판", "기타"])
                c_expect = cc6.selectbox("등록 가능성 (전환 예측)", ["높음", "중간", "낮음", "확인중"])

                c_memo = st.text_area("💬 자세한 상담 내역 및 특이사항 (통증, 과거 운동경험 등)", placeholder="예: 우측 어깨 집힘 증상 있음. 과거 PT 20회 경험 있으나 자극 못 느껴 이탈.", height=90)

                if st.form_submit_button("💡 상담 기록 저장", type="primary", use_container_width=True):
                    clean_contact = re.sub(r"[^0-9]", "", c_contact)
                    if not c_name.strip():
                        st.error("⚠️ 고객 이름을 입력해 주세요.")
                    elif len(clean_contact) < 10:
                        st.error("⚠️ 올바른 연락처 번호를 입력해 주세요.")
                    else:
                        if len(clean_contact) == 11: formatted_contact = f"{clean_contact[:3]}-{clean_contact[3:7]}-{clean_contact[7:]}"
                        else: formatted_contact = clean_contact

                        new_c_id = next_id(consultations, "consult_id")
                        today_str = get_kst_now().strftime("%Y-%m-%d")

                        new_c = {
                            "consult_id": new_c_id, "date": today_str,
                            "name": c_name.strip(), "contact": formatted_contact,
                            "gender": c_gender, "goal": c_goal, "source": c_source,
                            "expect_status": c_expect, "memo": c_memo, "converted": False,
                            "exp_sessions": 10, "exp_price": 70000
                        }
                        consultations = pd.concat([consultations, pd.DataFrame([new_c])], ignore_index=True)
                        if save_consultations(consultations):
                            st.toast(f"'{c_name}' 고객의 상담 기록이 저장되었습니다!")
                            rerun()

        st.write("")
        st.markdown("##### 📋 신규 상담 리스트 및 회원 전환 케어")
        consult_search = st.text_input("🔍 상담 고객 이름 / 연락처 검색", "", key="consult_search_input")

        view_consults = consultations.copy()
        if consult_search.strip():
            c_mask = view_consults["name"].astype(str).str.contains(consult_search, na=False) | view_consults["contact"].astype(str).str.contains(consult_search, na=False)
            view_consults = view_consults[c_mask]

        if view_consults.empty:
            st.info("조회되거나 등록된 신규 상담 기록이 없습니다.")
        else:
            st.caption(f"총 {len(view_consults)}건의 상담 기록이 표시됩니다. (고객 이름을 클릭하면 팝업 창이 표시됩니다)")
            for idx, c in view_consults.sort_values("date", ascending=False).iterrows():
                c_id = int(c["consult_id"])
                is_conv = bool(c.get("converted", False))
                conv_tag = '<b style="color:#166534;">🟢 회원 등록 완료</b>' if is_conv else '<b style="color:#2563EB;">⏳ 상담 진행중</b>'
                g_badge = get_gender_badge_html(c.get("gender"))
                expect_badge = get_expect_badge_html(c.get("expect_status"))

                c_exp_s = safe_int(c.get("exp_sessions"), 10)
                if c_exp_s <= 0: c_exp_s = 10
                c_exp_p = safe_int(c.get("exp_price"), 70000)
                if c_exp_p <= 0: c_exp_p = 70000
                calc_c_exp_amt = c_exp_s * c_exp_p

                st.markdown('<div class="pt-card">', unsafe_allow_html=True)
                col_cs1, col_cs2, col_cs3 = st.columns([1.5, 2.5, 0.5])

                with col_cs1:
                    if st.button(f"👤 {c['name']}", key=f"btn_c_dlg_{c_id}_{idx}", use_container_width=True):
                        if hasattr(st, "dialog"):
                            show_consultation_dialog(c, consultations, members, sales)
                        else:
                            st.session_state["selected_consult_detail_id"] = c_id
                            rerun()
                    st.markdown(f"{g_badge} &nbsp; {expect_badge}", unsafe_allow_html=True)

                with col_cs2:
                    st.markdown(f"<b>상태:</b> {conv_tag} &nbsp;|&nbsp; <b>예상 매출: {calc_c_exp_amt:,.0f}원</b> ({c_exp_s}회 x {c_exp_p:,.0f}원)", unsafe_allow_html=True)
                    st.caption(f"상담일: {c['date']} | 연락처: {c['contact']} | 목적: {c.get('goal','-')}")

                with col_cs3:
                    st.write("")
                    if st.button("🗑️", key=f"btn_del_consult_{c_id}_{idx}", use_container_width=True):
                        try:
                            supabase.table("consultations").delete().eq("consult_id", c_id).execute()
                            supabase.table("consultations").delete().eq("consult_id", str(c_id)).execute()
                        except Exception: pass
                        consultations = consultations[consultations["consult_id"].astype(str) != str(c_id)]
                        save_consultations(consultations)
                        st.toast("상담 기록이 삭제되었습니다.")
                        rerun()

                st.markdown('</div>', unsafe_allow_html=True)

    # === [서브 탭 2: 기존 회원 재등록 주차별 관리] ===
    with main_m_tab2:
        st.subheader("✏️ 기존 회원 주차별 재등록 예상가 및 1:1 메모/상담 케어")
        week_options_dynamic = ["전월이월"] + curr_weeks + ["노카테고리", "전월이탈"]

        inbody_df = st.session_state.get("inbody_df", fetch_table("inbody", INBODY_COLUMNS))
        logs_df = st.session_state.get("logs_df", fetch_table("logs", LOGS_COLUMNS))

        for idx, m in members.iterrows():
            m_id = int(m["member_id"])
            rem = safe_int(m.get("remaining_sessions"), 0)
            
            tr_exp_val = str(m.get("tr_expect", "")).strip()
            re_st_val = str(m.get("re_status", "")).strip()
            is_cfg = bool(safe_int(m.get("is_exp_configured"), 0) == 1)

            curr_exp_sess = safe_int(m.get("exp_re_sessions"), 10)
            if curr_exp_sess <= 0: curr_exp_sess = 10
            
            curr_exp_price = safe_int(m.get("exp_re_price"), safe_int(m.get("session_price"), 70000))
            if curr_exp_price <= 0: curr_exp_price = 70000

            if tr_exp_val in ["이탈", "낮음"] or re_st_val in ["이탈", "전월이탈"] or not is_cfg:
                calc_exp_amount = 0
                exp_text_disp = "<span style='color:#94A3B8;'>(예상가 수동 미설정 또는 이탈)</span>"
            else:
                calc_exp_amount = curr_exp_sess * curr_exp_price
                exp_text_disp = f"➡️ <b>예상 매출액: {calc_exp_amount:,.0f}원</b> ({curr_exp_sess}회 x {curr_exp_price:,.0f}원)"

            gender_badge = get_gender_badge_html(m.get("gender"))

            idx_exp = safe_index(TR_EXPECT_OPTIONS, m.get('tr_expect'), 4)
            idx_re = safe_index(RE_STATUS_OPTIONS, m.get('re_status'), 5)
            idx_wk = safe_index(week_options_dynamic, m.get('week_group'), 1)

            exp_badge_html = get_expect_badge_html(m.get('tr_expect'))

            st.markdown('<div class="pt-card">', unsafe_allow_html=True)
            col_info, col_exp, col_re, col_wk = st.columns([2.2, 1.1, 1, 1])

            with col_info:
                if st.button(f"👤 {m['name']}", key=f"btn_re_mname_dlg_{m_id}_{idx}"):
                    if hasattr(st, "dialog"):
                        show_member_dialog(m, members, logs, inbody_df, logs_df)
                    else:
                        st.session_state["selected_detail_member_id"] = m_id
                        rerun()
                st.markdown(f"{gender_badge} &nbsp;&nbsp; 현 상태: {exp_badge_html}", unsafe_allow_html=True)
                st.markdown(f"<span style='font-size:13px; color:#64748B;'>연락처: {m['contact']} | 잔여: <b>{rem}회</b> {exp_text_disp}</span>", unsafe_allow_html=True)

            with col_exp:
                n_exp = st.selectbox("TR 예상", TR_EXPECT_OPTIONS, index=idx_exp, key=f"re_exp_{m_id}")
            with col_re:
                n_re = st.selectbox("전환 상태", RE_STATUS_OPTIONS, index=idx_re, key=f"re_st_{m_id}")
            with col_wk:
                n_wk = st.selectbox("주차 이동", week_options_dynamic, index=idx_wk, key=f"re_wk_{m_id}")

            if n_exp != TR_EXPECT_OPTIONS[idx_exp] or n_re != RE_STATUS_OPTIONS[idx_re] or n_wk != week_options_dynamic[idx_wk]:
                members.loc[pd.to_numeric(members["member_id"], errors="coerce") == m_id, ["tr_expect", "re_status", "week_group"]] = [n_exp, n_re, n_wk]
                save_members(members)
                st.toast(f"'{m['name']}' 회원의 재등록 상태가 수정되었습니다.")
                rerun()

            st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 7. 페이지: 3-STEP 바이오 프로파일
# =========================================================
def page_bodyplan(members, reports):
    st.title("📋 PT 3-STEP 바이오 프로파일 (AI 고도화 처방)")

    if members.empty:
        st.info("등록된 회원이 없습니다.")
        return

    st.subheader("회원 리스트 및 리포트 작성")

    for idx, m in members.iterrows():
        m_id = int(m["member_id"])
        target_r = reports[pd.to_numeric(reports["member_id"], errors="coerce") == m_id]
        
        has_report = not target_r.empty and str(target_r.iloc[0].get("status")) == "작성완료"
        
        if has_report:
            rep_status_html = '<b style="color:#166534;">🟢 작성완료</b>'
        else:
            rep_status_html = '<b style="color:#DC2626;">🔴 미작성</b>'

        g_badge = get_gender_badge_html(m.get("gender"))

        st.markdown('<div class="pt-card" style="margin-bottom:12px;">', unsafe_allow_html=True)
        col_deliv, col_a, col_b, col_c = st.columns([0.8, 2.5, 1.2, 1])

        with col_deliv:
            if has_report:
                is_deliv_curr = bool(target_r.iloc[0].get("delivered", False))
                cb_deliv = st.checkbox("✅ 전달 완료", value=is_deliv_curr, key=f"cb_card_deliv_{m_id}_{idx}")
                if cb_deliv != is_deliv_curr:
                    reports.loc[pd.to_numeric(reports["member_id"], errors="coerce") == m_id, "delivered"] = cb_deliv
                    save_reports(reports)
                    st.toast(f"'{m['name']}' 회원의 리포트 전달 상태가 변경되었습니다.")
                    rerun()
            else:
                st.caption("⏳ 미작성")

        with col_a:
            st.markdown(f"**{m['name']} 회원님** &nbsp; {g_badge}", unsafe_allow_html=True)
            st.markdown(f"<span style='font-size:13px; color:#64748B;'>연락처: {m['contact']} | 담당: {MY_NAME} | 목표: {m.get('goal','-')} | 리포트: {rep_status_html}</span>", unsafe_allow_html=True)

        with col_b:
            btn_label = "✍️ 리포트 수정" if has_report else "➕ 리포트 작성하기"
            if st.button(btn_label, key=f"btn_write_{m_id}_{idx}", use_container_width=True):
                st.session_state["editing_member_id"] = m_id
                st.session_state["show_modal"] = False
                rerun()

        with col_c:
            if has_report:
                if st.button("📄 리포트 보기", key=f"btn_view_{m_id}_{idx}", use_container_width=True):
                    st.session_state["selected_member_id"] = m_id
                    st.session_state["show_modal"] = True
                    st.session_state["editing_member_id"] = None
                    rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # 미리보기 모달
    if st.session_state.get("show_modal", False) and st.session_state.get("selected_member_id"):
        m_id = int(st.session_state.get("selected_member_id"))
        target_m = members[pd.to_numeric(members["member_id"], errors="coerce") == m_id].iloc[0]
        target_r = reports[pd.to_numeric(reports["member_id"], errors="coerce") == m_id]
        r_dict = target_r.iloc[0].to_dict() if not target_r.empty else {}

        st.markdown("---")
        st.subheader(f"📄 '{target_m['name']}' 회원의 3-STEP 바이오 프로파일 미리보기")

        preview_html = build_4step_report_html(target_m, r_dict)

        btn_c1, btn_c2, btn_c3 = st.columns([1, 1, 1])

        if btn_c1.button("✏️ 내용 수정하기", use_container_width=True):
            st.session_state["editing_member_id"] = m_id
            st.session_state["show_modal"] = False
            rerun()
        if btn_c2.button("🔄 다시 작성하기", use_container_width=True):
            supabase.table("reports").delete().eq("member_id", m_id).execute()
            st.session_state["editing_member_id"] = m_id
            st.session_state["show_modal"] = False
            rerun()
        if btn_c3.button("❌ 창 닫기", use_container_width=True):
            st.session_state["show_modal"] = False
            st.session_state["selected_member_id"] = None
            rerun()

        components.html(preview_html, height=850, scrolling=True)

    if st.session_state.get("editing_member_id"):
        e_id = int(st.session_state.get("editing_member_id"))
        selected_m = members[pd.to_numeric(members["member_id"], errors="coerce") == e_id].iloc[0]
        target_r = reports[pd.to_numeric(reports["member_id"], errors="coerce") == e_id]
        has_existing = not target_r.empty and str(target_r.iloc[0].get("status")) == "작성완료"
        r_row = target_r.iloc[0] if has_existing else {}

        st.markdown("---")
        st.markdown("<div id='report-editor-anchor'></div>", unsafe_allow_html=True)
        components.html("<script>var el = window.parent.document.getElementById('report-editor-anchor'); if (el) { el.scrollIntoView({behavior: 'smooth'}); }</script>", height=0)

        st.subheader(f"💡 '{selected_m['name']}' 회원 맞춤 전문 가이드 생성 및 작성")

        st.markdown('<div class="pt-card">', unsafe_allow_html=True)

        goal_input = st.text_input(
            "🎯 회원 운동 목적", 
            value=r_row.get("goal_text") if has_existing else (selected_m.get("goal") or ""),
            placeholder="예시: 벌크업, 다이어트 및 체형교정",
            key=f"input_goal_{e_id}"
        )
        raw_journal = st.text_input(
            "1. 1회차 수업 진행 내용 (운동일지 메모)", 
            placeholder="예시: 할로우테스트 및 스쿼트 정렬 지도",
            key=f"input_journal_{e_id}"
        )
        raw_posture = st.text_input(
            "2. 자세 체크 결과", 
            placeholder="예시: 골반 전방경사 패턴 관찰",
            key=f"input_posture_{e_id}"
        )
        raw_func = st.text_input(
            "3. 움직임 체크 결과", 
            placeholder="예시: 렛풀다운 시 오른쪽 견갑만 닫혀있으심",
            key=f"input_func_{e_id}"
        )

        if st.button("🤖 전문 톤앤매너 맞춤 가이드 & 장문 코멘트 자동 생성", type="primary", key=f"btn_ai_gen_{e_id}"):
            refined_goal = refine_raw_text(goal_input, "goal")
            refined_journal = refine_raw_text(raw_journal, "journal")
            refined_posture = refine_raw_text(raw_posture, "posture")
            refined_func = refine_raw_text(raw_func, "func")

            details_list = []
            if raw_posture.strip(): 
                details_list.append(f"자세 정밀 평가 결과 {refined_posture}가 관찰되었습니다.")
            if raw_func.strip(): 
                details_list.append(f"움직임 기능 검사에서는 {refined_func} 소견이 확인되었습니다.")
            if raw_journal.strip(): 
                details_list.append(f"이러한 신체 보상 패턴을 개선하기 위해 진행된 1회차 훈련({refined_journal}) 성과를 바탕으로 단계별 로드맵을 적용합니다.")

            analysis_body = " ".join(details_list) if details_list else "입력된 세부 평가 데이터를 기반으로 맞춤형 개선 플랜을 수립합니다."

            st.session_state[f"ta_analysis_{e_id}"] = f"""[신체 정밀 종합 분석]
{selected_m['name']} 회원님의 정밀 신체 평가 결과, 핵심 개선 과제는 '{refined_goal}'입니다.

{analysis_body}"""

            st.session_state[f"ai_posture_text_{e_id}"] = f"체형 정렬 평가: {refined_posture}"
            st.session_state[f"ai_func_text_{e_id}"] = f"동작 가동성 평가: {refined_func}"

            st.session_state[f"ta_p1_{e_id}"] = f"STEP 1 [1-4주차: 관절 이완 & 호흡 정렬 익히기]\n• 타이트해진 근막 이완 및 호흡 정렬\n• 훈련 성과 반영: {refined_journal}"
            st.session_state[f"ta_p2_{e_id}"] = f"STEP 2 [5-8주차: 타겟 근육 고립 & 차근차근 부하 적용]\n• 보상 작용 없이 주동근 고립 자극 전달\n• 개선 과제 반영: {refined_posture} 케어"
            st.session_state[f"ta_p3_{e_id}"] = f"STEP 3 [9-12주차: 체력 극대화 & 자율 독립 루틴 완성]\n• 맞춤형 자율 운동 프로그램 체득 및 운동 자립 완성\n• 개선 과제 반영: {refined_func} 예방"

            st.session_state[f"ta_comment_{e_id}"] = f""""{selected_m['name']} 님을 위한 {MY_NAME} 트레이너의 진심 어린 한마디"

{selected_m['name']} 회원님, 담당 트레이너 {MY_NAME}입니다.
현재 회원님께서 고민하시는 신체 목표나 움직임의 제한은 정확한 생체역학적 원인 분석과 체계적인 로드맵을 통해 충분히 개선할 수 있습니다. 

준비해 드린 12주 간의 STEP 플랜을 따라 차근차근 나아간다면, 불균형했던 관절 정렬이 제자리를 찾고 한층 새로워진 몸의 변화를 직접 경험하시게 될 것입니다. 저를 믿고 편안한 마음으로 따라와 주세요! 화이팅! 🔥"""

            st.toast("RAW 데이터가 순수하고 전문적으로 정제되어 항목별로 분할 기입되었습니다!")
            rerun()

        default_analysis = r_row.get("analysis_text") if has_existing else ""
        default_p1 = r_row.get("phase1_text") if has_existing else ""
        default_p2 = r_row.get("phase2_text") if has_existing else ""
        default_p3 = r_row.get("phase3_text") if has_existing else ""
        default_comment = r_row.get("trainer_comment") if has_existing else ""

        if f"ta_analysis_{e_id}" not in st.session_state: st.session_state[f"ta_analysis_{e_id}"] = default_analysis
        if f"ta_p1_{e_id}" not in st.session_state: st.session_state[f"ta_p1_{e_id}"] = default_p1
        if f"ta_p2_{e_id}" not in st.session_state: st.session_state[f"ta_p2_{e_id}"] = default_p2
        if f"ta_p3_{e_id}" not in st.session_state: st.session_state[f"ta_p3_{e_id}"] = default_p3
        if f"ta_comment_{e_id}" not in st.session_state: st.session_state[f"ta_comment_{e_id}"] = default_comment

        analysis = st.text_area("1. 신체 정밀 종합 분석", height=130, key=f"ta_analysis_{e_id}")
        p1 = st.text_area("STEP 1 로드맵 (1~4주차)", height=80, key=f"ta_p1_{e_id}")
        p2 = st.text_area("STEP 2 로드맵 (5~8주차)", height=80, key=f"ta_p2_{e_id}")
        p3 = st.text_area("STEP 3 로드맵 (9~12주차)", height=80, key=f"ta_p3_{e_id}")
        comment = st.text_area("김준수 트레이너 마스터 응원 코멘트", height=120, key=f"ta_comment_{e_id}")

        col_save, col_cancel = st.columns([1, 1])
        if col_save.button("🚀 최종 바이오 프로파일 저장 및 완성", type="primary", use_container_width=True, key=f"btn_save_rep_{e_id}"):
            existing_mask = pd.to_numeric(reports["member_id"], errors="coerce") == e_id

            posture_text = st.session_state.get(f"ai_posture_text_{e_id}", f"자세 평가: {refine_raw_text(raw_posture, 'posture')}")
            func_text = st.session_state.get(f"ai_func_text_{e_id}", f"움직임 평가: {refine_raw_text(raw_func, 'func')}")

            if existing_mask.any():
                reports.loc[existing_mask, ["date", "goal_text", "analysis_text", "posture_eval", "func_eval", "phase1_text", "phase2_text", "phase3_text", "trainer_comment", "status"]] = [
                    get_kst_now().strftime("%Y-%m-%d"), goal_input, analysis,
                    json.dumps([{"title": "자세 정밀 체크", "result": posture_text}], ensure_ascii=False),
                    json.dumps([{"title": "움직임 가동성 체크", "result": func_text}], ensure_ascii=False),
                    p1, p2, p3, comment, "작성완료"
                ]
            else:
                new_r_id = next_id(reports, "report_id")
                new_rep = {
                    "report_id": new_r_id, "member_id": e_id,
                    "date": get_kst_now().strftime("%Y-%m-%d"),
                    "goal_text": goal_input,
                    "analysis_text": analysis,
                    "posture_eval": json.dumps([{"title": "자세 정밀 체크", "result": posture_text}], ensure_ascii=False),
                    "func_eval": json.dumps([{"title": "움직임 가동성 체크", "result": func_text}], ensure_ascii=False),
                    "phase1_text": p1, "phase2_text": p2, "phase3_text": p3,
                    "trainer_comment": comment, "status": "작성완료", "delivered": False
                }
                reports = pd.concat([reports, pd.DataFrame([new_rep])], ignore_index=True)

            if save_reports(reports):
                st.session_state["report_saved_toast"] = True
                st.session_state["selected_member_id"] = e_id
                st.session_state["show_modal"] = True
                st.session_state["editing_member_id"] = None
                rerun()

        if col_cancel.button("취소", use_container_width=True, key=f"btn_cancel_rep_{e_id}"):
            st.session_state["editing_member_id"] = None
            rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.get("report_saved_toast", False):
        st.toast("🎉 바이오 프로파일 저장이 완료되었습니다!", icon="✅")
        st.session_state["report_saved_toast"] = False


# =========================================================
# 8. 페이지: 수업일지 작성
# =========================================================
def page_journal(members, logs):
    st.title("📝 수업일지 작성 & 카톡 전송")
    if members.empty:
        st.info("회원을 먼저 등록해 주세요.")
        return

    options = members.apply(lambda m: f"{m['name']} ({m.get('gender','남성')}, 잔여 {int(m['remaining_sessions'])}회)", axis=1).tolist()
    default_sel = st.session_state.get("current_journal_member_idx", 0)
    if default_sel >= len(options): default_sel = 0

    idx = st.selectbox("회원 선택", range(len(options)), index=default_sel, format_func=lambda i: options[i])
    st.session_state["current_journal_member_idx"] = idx
    member = members.iloc[idx]
    m_id = int(member["member_id"])
    rem_sessions_val = int(member["remaining_sessions"])

    c1, c2, c3 = st.columns(3)
    c1.metric("총 세션", int(member["total_sessions"]))
    c2.metric("잔여 세션", rem_sessions_val)
    c3.metric("진행 완료", int(member["total_sessions"]) - rem_sessions_val)

    st.markdown("#### 오늘 수업 일정 및 운동 진행 내용")

    col_date, col_st, col_et = st.columns([1.2, 1, 1])
    log_date = col_date.date_input("수업 날짜", value=get_kst_now().date())

    start_time_sel = col_st.selectbox("수업 시작 시간", TIME_SLOTS, index=4)
    
    try:
        sh, sm = map(int, start_time_sel.split(":"))
        end_dt = datetime(2026, 1, 1, sh, sm) + timedelta(minutes=50)
        auto_end_time = end_dt.strftime("%H:%M")
    except Exception:
        auto_end_time = "10:50"

    end_time_sel = col_et.text_input("수업 종료 시간 (자동계산)", value=auto_end_time)

    sel_part = st.selectbox(
        "운동 루틴 템플릿 선택 (선택 시 아래 표에 즉시 불러오기)", 
        ["선택 안 함", "가슴", "등", "어깨", "하체", "전신"],
        key="journal_routine_selector"
    )

    if sel_part != "선택 안 함":
        if st.session_state.get("last_selected_preset") != sel_part:
            st.session_state["exercise_rows_df"] = PRESET_ROUTINES_DF.get(sel_part).copy()
            st.session_state["last_selected_preset"] = sel_part
            rerun()

    if "exercise_rows_df" not in st.session_state:
        st.session_state["exercise_rows_df"] = pd.DataFrame([{"종목": "바벨 스쿼트", "중량(kg)": 40.0, "횟수": 10, "세트": 4}])

    edited_df = st.data_editor(st.session_state["exercise_rows_df"], num_rows="dynamic", use_container_width=True)
    st.session_state["exercise_rows_df"] = edited_df

    st.markdown('<div class="pt-card">', unsafe_allow_html=True)
    st.markdown("##### ✏️ 피드백 메모 기입")

    good_raw = st.text_input("오늘 잘한 점 (메모)", placeholder="예시: 운동신경이 좋으심 또는 가슴 자극 좋음")
    improve_raw = st.text_input("보완할 점 (메모)", placeholder="예시: 지면 접지력이 약하심 또는 몸통 흔들림")

    if st.button("🤖 AI 수업 피드백 문장 고도화 완성", type="primary"):
        g_ref = refine_journal_feedback(good_raw, is_good=True)
        i_ref = refine_journal_feedback(improve_raw, is_good=False)

        st.session_state["journal_good_ai"] = g_ref
        st.session_state["journal_improve_ai"] = i_ref
        st.toast("AI 수업 피드백 문장이 전문가 수준으로 정제되었습니다!")

    good_points = st.text_area("✔ 잘하신 점 (AI 전문 정제 결과)", value=st.session_state.get("journal_good_ai", good_raw), height=85)
    improve_points = st.text_area("✔ 보완할 점 (AI 전문 정제 결과)", value=st.session_state.get("journal_improve_ai", improve_raw), height=85)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"#### 📱 '{member['name']}' 회원 전송용 실시간 통합 메시지")

    live_msg = generate_friendly_message_from_data(m_id, member["name"], rem_sessions_val, edited_df, good_points, improve_points)

    st.code(live_msg, language=None)

    encoded_msg = base64.b64encode(live_msg.encode('utf-8')).decode('utf-8')
    copy_html = f"""
    <div style="margin-top:-8px; margin-bottom:16px;">
        <button onclick="navigator.clipboard.writeText(atob('{encoded_msg}')); alert('카카오톡 피드백 문구가 클립보드에 복사되었습니다! 카톡에 바로 붙여넣기(Ctrl+V) 하세요.');" 
                style="background-color:#2563EB; color:white; border:none; padding:10px 18px; border-radius:8px; font-weight:800; cursor:pointer;">
            📋 카카오톡 전송 문구 복사하기
        </button>
    </div>
    """
    components.html(copy_html, height=50)

    if st.button("✅ 일지 저장", type="primary", use_container_width=True):
        valid_rows = edited_df[edited_df["종목"].astype(str).str.strip() != ""]

        new_log = {
            "log_id": next_id(logs, "log_id"), "member_id": m_id, "date": log_date.isoformat(),
            "start_time": start_time_sel, "end_time": end_time_sel,
            "exercises_json": valid_rows.to_json(orient="records", force_ascii=False),
            "good_points": good_points, "improve_points": improve_points,
            "sent": False, "attendance": "출석"
        }
        logs = pd.concat([logs, pd.DataFrame([new_log])], ignore_index=True)
        
        if save_logs(logs):
            st.session_state["exercise_rows_df"] = pd.DataFrame([{"종목": "", "중량(kg)": 0.0, "횟수": 0, "세트": 0}])
            st.session_state["log_saved_success"] = True
            rerun()

    if st.session_state.get("log_saved_success", False):
        st.toast(f"🎉 '{member['name']}' 회원의 일지가 정상 등록되었습니다!", icon="✅")
        st.session_state["log_saved_success"] = False

    st.write("")
    with st.expander(f"📜 '{member['name']}' 회원의 이전 수업일지 & 피드백 히스토리 복기"):
        m_logs = logs[pd.to_numeric(logs["member_id"], errors="coerce") == m_id].sort_values("date", ascending=False)
        if m_logs.empty:
            st.caption("기록된 과거 수업일지가 없습니다.")
        else:
            for _, l_row in m_logs.iterrows():
                st.markdown(f"""
                <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:12px 16px; margin-bottom:8px;">
                    <div style="font-weight:800; color:{COLOR_BLUE}; font-size:14px;">📅 {l_row['date']} ({l_row.get('start_time','-')} ~ {l_row.get('end_time','-')})</div>
                    <div style="font-size:13px; color:#334155;"><b>✔ 잘한점:</b> {l_row.get('good_points','-')}</div>
                    <div style="font-size:13px; color:#334155;"><b>✔ 보완점:</b> {l_row.get('improve_points','-')}</div>
                </div>
                """, unsafe_allow_html=True)


# =========================================================
# 9. 페이지: 회원 관리 (모달 다이얼로그 연동)
# =========================================================
def page_members(members, sales, bookings, logs, reports):
    st.title("👥 회원 관리 & 성비 분석")

    total_count = len(members)
    female_count = len(members[members["gender"] == "여성"])
    male_count = len(members[members["gender"] == "남성"])

    female_pct = (female_count / total_count * 100) if total_count > 0 else 0
    male_pct = (male_count / total_count * 100) if total_count > 0 else 0

    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("총 등록 회원 수", f"{total_count}명")
    sc2.metric("👩 여성 회원 수 (비율)", f"{female_count}명 ({female_pct:.1f}%)")
    sc3.metric("👨 남성 회원 수 (비율)", f"{male_count}명 ({male_pct:.1f}%)")

    st.write("")

    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
        search = st.text_input("🔍 회원 이름 / 연락처 검색", "")
    with col_head2:
        st.write("")
        st.write("")
        if st.button("➕ 신규 회원 등록", type="primary", use_container_width=True):
            st.session_state["show_reg_modal"] = True

    if st.session_state.get("show_reg_modal", False):
        with st.expander("📝 신규 회원 등록 폼", expanded=True):
            with st.form("reg_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                name = c1.text_input("회원 이름 *")
                contact = c1.text_input("연락처 * (숫자만 입력 가능)")
                gender = c1.selectbox("성별 *", ["남성", "여성"])

                sessions = c2.number_input("등록 세션 수 *", min_value=1, value=10)
                amount = c2.number_input("결제 금액(원) *", min_value=0, value=700000, step=10000)
                pay_type = c2.selectbox("결제 수단", ["카드", "계좌이체", "현금"])

                if st.form_submit_button("등록 완료", type="primary", use_container_width=True):
                    clean_contact = re.sub(r"[^0-9]", "", contact)
                    if not name.strip():
                        st.error("⚠️ 회원 이름을 입력해 주세요.")
                    elif len(clean_contact) < 10:
                        st.error("⚠️ 올바른 연락처 번호를 입력해 주세요.")
                    else:
                        if len(clean_contact) == 11: formatted_contact = f"{clean_contact[:3]}-{clean_contact[3:7]}-{clean_contact[7:]}"
                        else: formatted_contact = clean_contact

                        new_m_id = next_id(members, "member_id")
                        today_obj = get_kst_now().date()
                        auto_week = get_week_of_month(today_obj)

                        consults_df = st.session_state.get("consultations_df", fetch_table("consultations", CONSULTATIONS_COLUMNS))
                        c_match = consults_df[
                            (consults_df["name"].astype(str).str.strip() == name.strip()) &
                            (consults_df["contact"].astype(str).str.strip() == formatted_contact)
                        ]

                        init_memo = ""
                        init_survey = "{}"
                        if not c_match.empty:
                            c_row = c_match.iloc[0]
                            init_memo = f"[신규 상담일지 자동 이관]\n희망목적: {c_row.get('goal','')}\n상담메모: {c_row.get('memo','')}"
                            init_survey = json.dumps({"pain": c_row.get("memo",""), "exp": "신규 상담 자동 연동 이관"}, ensure_ascii=False)
                            
                            consults_df.loc[consults_df["consult_id"] == c_row["consult_id"], "converted"] = True
                            save_consultations(consults_df)

                        new_m = {
                            "member_id": new_m_id, "name": name.strip(), "contact": formatted_contact,
                            "birth_date": "1995-01-01", "reg_date": today_obj.isoformat(),
                            "total_sessions": int(sessions), "remaining_sessions": int(sessions),
                            "trainer": MY_NAME, "status": "Active", "goal": "다이어트 및 체형교정",
                            "session_price": int(amount/sessions) if sessions>0 else 0,
                            "branch": "개인 PT", "gender": gender, "age": 28,
                            "tr_expect": "확인중", "re_status": "미지정", "week_group": auto_week,
                            "memo": init_memo, "survey_json": init_survey, "exp_re_sessions": 10, "exp_re_price": int(amount/sessions) if sessions>0 else 70000, "is_exp_configured": 0
                        }
                        members = pd.concat([members, pd.DataFrame([new_m])], ignore_index=True)
                        
                        if save_members(members):
                            db_sales = fetch_table("sales", SALES_COLUMNS)
                            new_s_id = next_id(db_sales, "sale_id")

                            new_s = {
                                "sale_id": new_s_id, 
                                "member_id": new_m_id, 
                                "date": today_obj.isoformat(), 
                                "product_name": f"PT {sessions}회 신규등록", 
                                "amount": amount, 
                                "pay_type": pay_type
                            }
                            updated_sales = pd.concat([db_sales, pd.DataFrame([new_s])], ignore_index=True)
                            save_sales(updated_sales)

                            st.session_state["show_reg_modal"] = False
                            st.toast(f"'{name}' ({gender}) 회원이 정상 등록되고 결제 매출({amount:,.0f}원)이 계상되었습니다.")
                            rerun()

    tab1, tab2 = st.tabs(["📋 회원 세션 관리 & 메모/사전설문", "💰 월별 매출 통합 분석"])

    with tab1:
        view = members.copy()
        if search:
            mask = view["name"].astype(str).str.contains(search, na=False) | view["contact"].astype(str).str.contains(search, na=False)
            view = view[mask]

        st.caption(f"조회된 회원 수: {len(view)}명 (회원 이름을 클릭하면 팝업 모달에서 상세 메모 및 수업 이력을 확인할 수 있습니다)")

        re_pay_open_id = st.session_state.get("re_pay_open_id")

        inbody_df = st.session_state.get("inbody_df", fetch_table("inbody", INBODY_COLUMNS))
        logs_df = st.session_state.get("logs_df", fetch_table("logs", LOGS_COLUMNS))

        for idx, m in view.iterrows():
            m_id = int(m["member_id"])
            m_name = str(m.get("name","")).strip()
            m_contact = str(m.get("contact","")).strip()

            total = int(pd.to_numeric(m.get("total_sessions", 0), errors="coerce"))
            rem = int(pd.to_numeric(m.get("remaining_sessions", 0), errors="coerce"))
            done = max(0, total - rem)
            has_memo = pd.notna(m.get("memo")) and str(m.get("memo")).strip() != ""
            gender_badge = get_gender_badge_html(m.get("gender"))

            st.markdown('<div class="pt-card" style="padding-bottom:10px;">', unsafe_allow_html=True)

            c_name, c_info, c_re_btn, c_btn1, c_btn2, c_del = st.columns([1.5, 2.2, 0.9, 0.5, 0.5, 0.5])

            with c_name:
                memo_tag = " ⭐" if has_memo else ""
                if st.button(f"👤 {m['name']}{memo_tag}", key=f"btn_name_dlg_{m_id}_{idx}", use_container_width=True):
                    if hasattr(st, "dialog"):
                        show_member_dialog(m, members, logs, inbody_df, logs_df)
                    else:
                        st.session_state["selected_detail_member_id"] = m_id
                        rerun()
                st.markdown(f"{gender_badge} &nbsp; <span style='font-size:12px; color:#64748B;'>{m['contact']}</span>", unsafe_allow_html=True)

            with c_info:
                st.markdown(f"목표: {m['goal']}")
                st.caption(f"진행 {done}회 / 총 {total}회 · 남은 세션 **{rem}회**")

            with c_re_btn:
                st.write("")
                if st.button("🔄 재등록", key=f"btn_re_pay_{m_id}_{idx}", type="primary", use_container_width=True):
                    st.session_state["re_pay_open_id"] = None if re_pay_open_id == m_id else m_id
                    rerun()

            with c_btn1:
                st.write("")
                if st.button("➖1", key=f"btn_minus_{m_id}_{idx}", use_container_width=True):
                    if rem > 0:
                        members.loc[pd.to_numeric(members["member_id"], errors="coerce") == m_id, "remaining_sessions"] = rem - 1
                        save_members(members)
                        st.toast(f"{m['name']} 회원 세션 -1 차감 완료")
                        rerun()
            with c_btn2:
                st.write("")
                if st.button("➕1", key=f"btn_plus_{m_id}_{idx}", use_container_width=True):
                    members.loc[pd.to_numeric(members["member_id"], errors="coerce") == m_id, "remaining_sessions"] = rem + 1
                    members.loc[pd.to_numeric(members["member_id"], errors="coerce") == m_id, "total_sessions"] = total + 1
                    save_members(members)
                    st.toast(f"{m['name']} 회원 잔여 및 총 세션 +1 반영 완료")
                    rerun()
            with c_del:
                st.write("")
                if st.button("🗑️", key=f"btn_del_mem_{m_id}_{idx}", use_container_width=True):
                    for tbl in ["bookings", "logs", "reports", "inbody", "sales", "members"]:
                        supabase.table(tbl).delete().eq("member_id", m_id).execute()
                        supabase.table(tbl).delete().eq("member_id", str(m_id)).execute()

                    consults_df = st.session_state.get("consultations_df", fetch_table("consultations", CONSULTATIONS_COLUMNS))
                    c_mask = (consults_df["name"].astype(str).str.strip() == m_name) & (consults_df["contact"].astype(str).str.strip() == m_contact)
                    if c_mask.any():
                        consults_df.loc[c_mask, "converted"] = False
                        save_consultations(consults_df)

                    if "bookings_df" in st.session_state:
                        st.session_state["bookings_df"] = st.session_state["bookings_df"][st.session_state["bookings_df"]["member_id"].astype(str) != str(m_id)]
                    if "logs_df" in st.session_state:
                        st.session_state["logs_df"] = st.session_state["logs_df"][st.session_state["logs_df"]["member_id"].astype(str) != str(m_id)]
                    if "reports_df" in st.session_state:
                        st.session_state["reports_df"] = st.session_state["reports_df"][st.session_state["reports_df"]["member_id"].astype(str) != str(m_id)]
                    if "sales_df" in st.session_state:
                        st.session_state["sales_df"] = st.session_state["sales_df"][st.session_state["sales_df"]["member_id"].astype(str) != str(m_id)]
                    if "inbody_df" in st.session_state:
                        st.session_state["inbody_df"] = st.session_state["inbody_df"][st.session_state["inbody_df"]["member_id"].astype(str) != str(m_id)]

                    members = members[members["member_id"].astype(str) != str(m_id)]
                    save_members(members)

                    st.toast(f"'{m['name']}' 회원의 모든 데이터가 삭제되고 상담 탭 상태가 초기화되었습니다.")
                    rerun()

            if re_pay_open_id == m_id:
                st.markdown("---")
                st.markdown(f"##### 💳 '{m['name']}' 회원 PT 세션 재등록 (매출 자동 집계)")
                re_col1, re_col2, re_col3, re_col4 = st.columns([1.5, 1.5, 1.5, 1])
                
                re_sess = re_col1.selectbox("재등록 세션 회수", [10, 20, 30, 40, 50], index=0, key=f"re_sess_sel_{m_id}")
                re_unit_price = re_col2.number_input("1회 세션 단가(원)", min_value=10000, value=int(m.get("session_price") or 70000), step=5000, key=f"re_unit_p_{m_id}")
                re_pay_type = re_col3.selectbox("결제 수단", ["카드", "계좌이체", "현금"], key=f"re_ptype_{m_id}")
                
                tot_re_amount = re_sess * re_unit_price
                re_col4.write("")
                re_col4.write("")
                if re_col4.button("💳 결제 저장", key=f"btn_re_confirm_{m_id}", type="primary", use_container_width=True):
                    members.loc[pd.to_numeric(members["member_id"], errors="coerce") == m_id, "total_sessions"] = total + re_sess
                    members.loc[pd.to_numeric(members["member_id"], errors="coerce") == m_id, "remaining_sessions"] = rem + re_sess
                    members.loc[pd.to_numeric(members["member_id"], errors="coerce") == m_id, "session_price"] = re_unit_price
                    members.loc[pd.to_numeric(members["member_id"], errors="coerce") == m_id, "re_status"] = "결제완료"
                    
                    if save_members(members):
                        db_sales = fetch_table("sales", SALES_COLUMNS)
                        new_s = {
                            "sale_id": next_id(db_sales, "sale_id"),
                            "member_id": m_id,
                            "date": get_kst_now().strftime("%Y-%m-%d"),
                            "product_name": f"PT {re_sess}회 재등록",
                            "amount": tot_re_amount,
                            "pay_type": re_pay_type
                        }
                        updated_sales = pd.concat([db_sales, pd.DataFrame([new_s])], ignore_index=True)
                        save_sales(updated_sales)

                        st.session_state["re_pay_open_id"] = None
                        st.toast(f"🎉 '{m['name']}' 회원 {re_sess}회 재등록 ({tot_re_amount:,.0f}원) 결제 집계가 완료되었습니다!")
                        rerun()

            if has_memo:
                st.caption(f"💬 특이사항 메모: {m['memo']}")

            st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.subheader("💰 월별 매출 통합 분석")
        
        current_sales = st.session_state.get("sales_df", sales)
        
        if current_sales.empty:
            st.info("등록된 매출 내역이 없습니다.")
        else:
            current_sales["date_dt"] = pd.to_datetime(current_sales["date"], errors="coerce")
            current_sales["month_str"] = current_sales["date_dt"].dt.strftime("%Y-%m")

            all_months = sorted(list(current_sales["month_str"].dropna().unique()), reverse=True)
            curr_month_str = get_kst_now().strftime("%Y-%m")
            default_idx = all_months.index(curr_month_str) if curr_month_str in all_months else 0

            sel_month = st.selectbox("📅 조회할 월 선택", all_months, index=default_idx)

            filtered_sales = current_sales[current_sales["month_str"] == sel_month].copy()
            filtered_sales["amount_num"] = pd.to_numeric(filtered_sales["amount"], errors="coerce").fillna(0)
            month_tot_val = filtered_sales["amount_num"].sum()

            m_c1, m_c2 = st.columns(2)
            m_c1.metric(f"{sel_month} 당월 (1일~말일) 누적 매출", f"{month_tot_val:,.0f}원")
            m_c2.metric("당월 결제 건수", f"{len(filtered_sales)}건")

            st.write("")
            st.markdown(f"#### {sel_month} 결제 상세 내역 리스트")

            merged_sales = filtered_sales.merge(members[["member_id", "name", "gender"]], on="member_id", how="left")
            
            for idx, s_row in merged_sales.sort_values("date", ascending=False).iterrows():
                sale_id = int(s_row["sale_id"])
                pay_amt = safe_float(s_row['amount_num'])
                
                m_name = s_row.get("name")
                m_name_str = str(m_name) if pd.notna(m_name) else "삭제/미기재 회원"
                g_badge = get_gender_badge_html(s_row.get("gender")) if pd.notna(s_row.get("gender")) else ""

                st.markdown('<div class="pt-card" style="margin-bottom:8px; padding:12px 20px;">', unsafe_allow_html=True)
                
                col_s1, col_s2, col_s3 = st.columns([3.5, 1.5, 0.8])
                
                with col_s1:
                    st.markdown(f"<b>{m_name_str}</b> 회원님 {g_badge} — {s_row.get('product_name','PT 등록')} <span style='font-size:12px; color:#64748B;'>({s_row.get('date','-')})</span>", unsafe_allow_html=True)
                
                with col_s2:
                    st.markdown(f"<div style='font-size:16px; font-weight:800; color:{COLOR_BLUE}; text-align:right;'>{pay_amt:,.0f}원 <span style='font-size:12px; color:#64748B;'>({s_row.get('pay_type','카드')})</span></div>", unsafe_allow_html=True)
                
                with col_s3:
                    if st.button("🗑️ 삭제", key=f"btn_del_sale_{sale_id}_{idx}", use_container_width=True):
                        supabase.table("sales").delete().eq("sale_id", sale_id).execute()
                        updated_sales = current_sales[current_sales["sale_id"].astype(str) != str(sale_id)]
                        save_sales(updated_sales)
                        st.toast("해당 매출 내역이 삭제되었습니다.")
                        rerun()

                st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 10. 인바디 체성분 관리
# =========================================================
def page_inbody(members, inbody):
    st.title("📉 인바디(InBody) 체성분 기록 & 변화 분석")

    if members.empty:
        st.info("회원을 먼저 등록해 주세요.")
        return

    options = members.apply(lambda m: f"{m['name']} ({m.get('gender','남성')})", axis=1).tolist()
    idx = st.selectbox("조회할 회원 선택", range(len(options)), format_func=lambda i: options[i])
    selected_m = members.iloc[idx]
    m_id = int(selected_m["member_id"])

    st.markdown('<div class="pt-card">', unsafe_allow_html=True)
    st.subheader(f"➕ '{selected_m['name']}' 회원 인바디 기록 추가")

    ic1, ic2, ic3, ic4, ic5 = st.columns([1.5, 1.2, 1.2, 1.2, 1])
    in_date = ic1.date_input("측정 날짜", value=get_kst_now().date(), key=f"in_date_{m_id}")
    in_weight = ic2.number_input("체중 (kg)", min_value=30.0, max_value=200.0, value=70.0, step=0.1, key=f"in_w_{m_id}")
    in_muscle = ic3.number_input("골격근량 (kg)", min_value=10.0, max_value=100.0, value=30.0, step=0.1, key=f"in_m_{m_id}")
    in_fat = ic4.number_input("체지방률 (%)", min_value=3.0, max_value=60.0, value=20.0, step=0.1, key=f"in_f_{m_id}")

    ic5.write("")
    ic5.write("")
    if ic5.button("💾 기록 저장", type="primary", use_container_width=True, key=f"in_save_{m_id}"):
        new_rec = {
            "record_id": next_id(inbody, "record_id"),
            "member_id": m_id,
            "date": in_date.isoformat(),
            "weight": in_weight,
            "skeletal_muscle": in_muscle,
            "body_fat_pct": in_fat
        }
        inbody = pd.concat([inbody, pd.DataFrame([new_rec])], ignore_index=True)
        if save_inbody(inbody):
            st.toast(f"'{selected_m['name']}' 회원의 체성분 기록이 추가되었습니다.")
            rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    m_inbody = inbody[pd.to_numeric(inbody["member_id"], errors="coerce") == m_id].sort_values("date")

    if m_inbody.empty:
        st.info(f"'{selected_m['name']}' 회원의 인바디 측정 기록이 없습니다.")
    else:
        first_rec = m_inbody.iloc[0]
        curr_rec = m_inbody.iloc[-1]
        
        tot_w_diff = round(safe_float(curr_rec["weight"]) - safe_float(first_rec["weight"]), 1)
        tot_m_diff = round(safe_float(curr_rec["skeletal_muscle"]) - safe_float(first_rec["skeletal_muscle"]), 1)
        tot_f_diff = round(safe_float(curr_rec["body_fat_pct"]) - safe_float(first_rec["body_fat_pct"]), 1)

        st.markdown('<div class="pt-card" style="border-left: 5px solid #2563EB; background:#EFF6FF;">', unsafe_allow_html=True)
        st.markdown(f"##### 📊 **'{selected_m['name']}' 회원의 체성분 입체 분석 리포트**")

        st.markdown(f"🚩 **최초 측정({first_rec['date']}) 대비 누적 변화 (Total):**")
        tc_w, tc_m, tc_f = st.columns(3)
        tc_w.metric("총 체중 변화", f"{curr_rec['weight']} kg", f"{tot_w_diff:+} kg", delta_color="inverse")
        tc_m.metric("총 골격근량 변화", f"{curr_rec['skeletal_muscle']} kg", f"{tot_m_diff:+} kg")
        tc_f.metric("총 체지방률 변화", f"{curr_rec['body_fat_pct']} %", f"{tot_f_diff:+} %", delta_color="inverse")

        if len(m_inbody) >= 2:
            prev_rec = m_inbody.iloc[-2]
            rec_w_diff = round(safe_float(curr_rec["weight"]) - safe_float(prev_rec["weight"]), 1)
            rec_m_diff = round(safe_float(curr_rec["skeletal_muscle"]) - safe_float(prev_rec["skeletal_muscle"]), 1)
            rec_f_diff = round(safe_float(curr_rec["body_fat_pct"]) - safe_float(prev_rec["body_fat_pct"]), 1)

            st.markdown("---")
            st.markdown(f"⚡ **직전 측정({prev_rec['date']}) 대비 최근 변화 (Recent):**")
            rc_w, rc_m, rc_f = st.columns(3)
            rc_w.metric("최근 체중 변화", f"{curr_rec['weight']} kg", f"{rec_w_diff:+} kg", delta_color="inverse")
            rc_m.metric("최근 골격근량 변화", f"{curr_rec['skeletal_muscle']} kg", f"{rec_m_diff:+} kg")
            rc_f.metric("최근 체지방률 변화", f"{curr_rec['body_fat_pct']} %", f"{rec_f_diff:+} %", delta_color="inverse")

            feedback_comments = []
            if tot_m_diff > 0 and tot_f_diff < 0:
                feedback_comments.append(f"🔥 **누적 우수 성과:** 등록 후 총 골격근량 {tot_m_diff:+}kg 증가, 체지방률 {tot_f_diff:+}% 감량되어 완벽한 신체 리커버리 상태를 보여주고 있습니다!")
            if rec_m_diff > 0 and rec_f_diff < 0:
                feedback_comments.append(f"💪 **최근 가속화:** 직전 대비 근육량 {rec_m_diff:+}kg 상승 및 체지방 {rec_f_diff:+}% 감량으로 최적의 훈련 이행률을 달성 중입니다.")
            elif rec_m_diff < 0:
                feedback_comments.append("⚠️ **최근 근손실 주의 보완점:** 직전 대비 골격근량이 소폭 감소했습니다. 단백질 섭취량과 점진적 부하 훈련 세팅을 강화할 필요가 있습니다.")
            elif rec_f_diff > 0:
                feedback_comments.append("💡 **최근 식단 케어 보완점:** 직전 대비 체지방률이 소폭 상승했습니다. 주말 식습관 및 수면/스트레스 관리를 함께 체크해 드리겠습니다.")

            comment_disp = "\n\n".join(feedback_comments) if feedback_comments else "현재 체성분 수치가 안정적으로 유지되고 있습니다."
            st.markdown(f"<div style='margin-top:12px; font-size:14px; color:#1E293B;'>{comment_disp}</div>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="pt-card">', unsafe_allow_html=True)
        st.subheader(f"📈 '{selected_m['name']}' 회원 체성분 변화 추이 그래프")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=m_inbody["date"], y=m_inbody["weight"], mode='lines+markers', name='체중 (kg)', line=dict(color='#2563EB', width=3)))
        fig.add_trace(go.Scatter(x=m_inbody["date"], y=m_inbody["skeletal_muscle"], mode='lines+markers', name='골격근량 (kg)', line=dict(color='#22C55E', width=3)))
        fig.add_trace(go.Scatter(x=m_inbody["date"], y=m_inbody["body_fat_pct"], mode='lines+markers', name='체지방률 (%)', line=dict(color='#E11D48', width=3)))

        fig.update_layout(
            height=350, margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### 📋 인바디 측정 이력 목록")
        for idx_ib, ib_row in m_inbody.sort_values("date", ascending=False).iterrows():
            rec_id = int(ib_row["record_id"])
            st.markdown(f"""
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:10px 16px; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <b>📅 {ib_row['date']}</b> &nbsp;|&nbsp; 
                    체중: <b>{ib_row['weight']}kg</b> &nbsp;|&nbsp; 
                    골격근량: <b style="color:#22C55E;">{ib_row['skeletal_muscle']}kg</b> &nbsp;|&nbsp; 
                    체지방률: <b style="color:#E11D48;">{ib_row['body_fat_pct']}%</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🗑️ 기록 삭제", key=f"del_ib_{rec_id}_{idx_ib}"):
                supabase.table("inbody").delete().eq("record_id", rec_id).execute()
                inbody = inbody[inbody["record_id"].astype(str) != str(rec_id)]
                save_inbody(inbody)
                st.toast("체성분 기록이 삭제되었습니다.")
                rerun()

        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# 11. 메인 라우팅
# =========================================================
def main():
    init_all_files()
    members, logs, inbody, sales, reports, bookings, consultations = get_cached_data()

    st.sidebar.markdown(f"""
    <div style="padding:10px 4px 18px;">
      <div style="font-size:20px;font-weight:800;color:#fff;">🏋️ PT Account</div>
      <div style="font-size:12px;color:#94A3B8;">담당: {MY_NAME} 트레이너</div>
    </div>
    """, unsafe_allow_html=True)

    menu = st.sidebar.radio(
        "메뉴 선택",
        [
            "📊 센터 대시보드", 
            "💡 신규 상담 & 재등록 관리",
            "📋 3-STEP 바이오 프로파일", 
            "📝 수업일지 작성 & 전송", 
            "📉 인바디 체성분 관리", 
            "👥 회원 관리 & 세션 조절"
        ],
        label_visibility="collapsed",
    )

    if menu == "📊 센터 대시보드":
        page_dashboard(members, logs, sales, reports, bookings)
    elif menu == "💡 신규 상담 & 재등록 관리":
        page_consultations(consultations, members, sales, logs)
    elif menu == "📋 3-STEP 바이오 프로파일":
        page_bodyplan(members, reports)
    elif menu == "📝 수업일지 작성 & 전송":
        page_journal(members, logs)
    elif menu == "📉 인바디 체성분 관리":
        page_inbody(members, inbody)
    elif menu == "👥 회원 관리 & 세션 조절":
        page_members(members, sales, bookings, logs, reports)

if __name__ == "__main__":
    main()
