import os
import sys
import re
import streamlit as st
import requests


# 안전한 import 경로
THIS_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(THIS_DIR, os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from app.services.categories import list_genre_options

# 면담 고정 순서 및 기본 문항 정의 
DEFAULT_QUESTIONS = [
    {"id": "Q1_SQUIN", "type": "text", "text": "요즘 어떤 이야기가 마음에 남았나요?"},
    {"id": "Q2_LENGTH", "type": "single", "text": "읽고 싶은 분량은 어느 정도인가요?", "options": ["짧게", "보통", "길게"]},
    {"id": "Q3_RECENCY", "type": "multi", "text": "도서의 발간일시는 어느 정도가 좋은가요?", "options": ["최근", "과거", "무관"]},
    {"id": "Q4_CONTEXT", "type": "text", "text": "원하시는 분위기나 문체를 적어주세요."},
    {"id": "Q5_GENRE", "type": "multi", "text": "관심 있는 장르(대분류)를 선택해주세요."},
    {"id": "Q6_MISC", "type": "text", "text": "추가로 전하고 싶은 선호나 제약이 있나요?"},
    {"id": "Q7_NEG", "type": "text", "text": "피하고 싶은 요소가 있다면 알려주세요."},
    {"id": "Q8_END", "type": "text", "text": "핵심 키워드가 있다면 적어주세요."},
]

def _get_api_base() -> str:
    if os.getenv("API_BASE"):
        return os.getenv("API_BASE")
    try:
        return st.secrets["API_BASE"]
    except Exception:
        return "http://localhost:8000"

API = _get_api_base()
st.set_page_config(page_title="SQUIN Book Agent", page_icon="📚")
# 결과 설명 선택 및 요약 함수
def _pick_description(item: dict, *, min_sentences: int = 3, max_sentences: int = 5) -> str:
    candidates_keys = [
        "description", "overview", "fullDescription", "subDescription", "sub_desc",
        "intro", "summary", "explain",
    ]
    text = ""
    for key in candidates_keys:
        val = item.get(key)
        if isinstance(val, str) and val.strip():
            text = val.strip()
            break
    if not text:
        # 마지막 보루: 제목·저자·카테고리로 간단 구성
        title = item.get("title", "")
        author = item.get("author", "")
        category = item.get("category", "")
        parts = [p for p in [title, author, category] if p]
        return " · ".join(parts)

    # 문장 단위로 3~5문장 추려 표시
    # 한국어/영문을 단순하게 다루기 위해 마침표, 물음표, 느낌표, 종결어미 '다.' 기준 분할
    sentences = re.split(r"(?<=[\.\!\?])\s+|(?<=다\.)\s+", text)
    sentences = [s.strip() for s in sentences if s and not s.isspace()]
    if len(sentences) <= max_sentences:
        return " ".join(sentences)
    # 최소 3문장은 유지
    take = max(min_sentences, min(max_sentences, len(sentences)))
    clipped = " ".join(sentences[:take]).rstrip()
    return clipped + " …"

# 세션 상태
if "constraints" not in st.session_state:
    st.session_state.constraints = {}
if "narrative" not in st.session_state:
    st.session_state.narrative = ""
if "step" not in st.session_state:
    st.session_state.step = 0
if "questions" not in st.session_state:
    desired_order = [q["id"] for q in DEFAULT_QUESTIONS]
    defaults_by_id = {q["id"]: q for q in DEFAULT_QUESTIONS}
    try:
        api_questions = requests.get(f"{API}/interview/questions").json().get("questions", [])
        api_by_id = {q.get("id"): q for q in api_questions if q.get("id")}
        # 고정 순서로 정렬하고 누락은 기본 문항으로 보완
        ordered = [api_by_id.get(qid, defaults_by_id[qid]) for qid in desired_order]
        st.session_state.questions = ordered
    except Exception:
        # API 실패 시 기본 문항 사용
        st.session_state.questions = DEFAULT_QUESTIONS[:]

st.title("📚 SQUIN Book Agent — 면담형")

# Sidebar: 모델/키 설정
with st.sidebar:
    st.subheader("환경 설정")
    # 임베딩 제공자 선택
    provider = st.radio("임베딩 제공자", options=["sbert", "gpt"], index=0, horizontal=True)
    st.session_state.embedding_provider = "openai" if provider == "gpt" else "sbert"

    # GPT(OpenAI) 키 입력
    if provider == "gpt":
        openai_key = st.text_input("OpenAI API Key", value=st.session_state.get("openai_key", ""), type="password")
        if st.button("OpenAI 키 저장"):
            st.session_state.openai_key = openai_key
            st.success("OpenAI 키 저장됨")

    st.divider()
    st.caption("알라딘 TTB 키를 입력하면 더 풍부한 도서 정보를 불러옵니다.")
    user_aladin_key = st.text_input("ALADIN_TTB_KEY", value=st.session_state.get("user_aladin_key", ""), type="password")
    if st.button("알라딘 키 저장"):
        st.session_state.user_aladin_key = user_aladin_key
        st.success("알라딘 키 저장됨")

total = len(st.session_state.questions)
st.progress((st.session_state.step)/max(total,1))

def _parse(qid: str, answer: str = "", structured=None, genres=None):
    payload = {
        "qid": qid,
        "answer": answer,
        "constraints": st.session_state.constraints,
        "narrative": st.session_state.narrative,
        "structured": structured,
        "genres": genres,
    }
    try:
        parsed = requests.post(f"{API}/interview/parse", json=payload, timeout=60).json()
        st.session_state.constraints = parsed.get("constraints", st.session_state.constraints)
        st.session_state.narrative = parsed.get("narrative", st.session_state.narrative)
    except Exception:
        # 오프라인/백엔드 오류 시 최소한의 로컬 업데이트로 계속 진행
        if answer:
            sep = "\n\n" if st.session_state.narrative else ""
            st.session_state.narrative = f"{st.session_state.narrative}{sep}{answer}"
        st.warning("백엔드 연결이 원활하지 않아 로컬로 진행합니다.")

if st.session_state.step < total:
    q = st.session_state.questions[st.session_state.step]
    st.info(q["text"])

    if q["id"] == "Q1_SQUIN":
        ans = st.chat_input("여기에 답변을 입력하세요…")
        if ans:
            _parse(q["id"], answer=ans)
            st.session_state.step += 1
            st.rerun()

    elif q["id"] == "Q2_LENGTH":
        choice = st.radio("선택해주세요", q["options"], horizontal=False, index=1)
        if st.button("다음"):
            _parse(q["id"], structured={"length": choice})
            st.session_state.step += 1
            st.rerun()

    elif q["id"] == "Q3_RECENCY":
        sel = st.multiselect("해당하는 항목을 모두 선택", q["options"], default=["무관"])
        if st.button("다음"):
            _parse(q["id"], structured={"recency": sel})
            st.session_state.step += 1
            st.rerun()

    elif q["id"] == "Q4_CONTEXT":
        # 멀티셀렉트로 변경된 문항 처리
        options = q.get("options") or [
            "속도감(내용의 진행 속도)",
            "성격 묘사(캐릭터가 서술되는 방식)",
            "설정(작품의 세계관)",
            "정보 전달성(유익한 정보 제공)",
        ]
        sel = st.multiselect("매력적으로 느껴지는 요소를 선택하세요", options)
        if st.button("다음", type="primary"):
            _parse(q["id"], structured={"context_traits": sel})
            st.session_state.step += 1
            st.rerun()

    elif q["id"] == "Q5_GENRE":
        genres = st.multiselect("장르(대분류) 선택", list_genre_options())
        st.caption("복수 선택 가능합니다. 비워두면 장르 제약 없이 검색합니다.")
        if st.button("다음"):
            _parse(q["id"], genres=genres)
            st.session_state.step += 1
            st.rerun()

    elif q["id"] == "Q6_MISC":
        ans = st.text_area("추가 선호나 제약을 자유롭게 적어주세요", height=100)
        if st.button("다음"):
            _parse(q["id"], answer=ans)
            st.session_state.step += 1
            st.rerun()

    elif q["id"] == "Q7_NEG":
        ans = st.text_area("예: 철학적 주제 제외, 잔혹 장면 X, 로맨스 제외", height=100)
        if st.button("다음"):
            _parse(q["id"], answer=ans)
            st.session_state.step += 1
            st.rerun()

    elif q["id"] == "Q8_END":
        ans = st.text_input("핵심 키워드(쉼표로 구분 가능)", value="")
        if st.button("추천 받기 🎯"):
            _parse(q["id"], answer=ans)
            st.session_state.step += 1
            st.rerun()

    else:
        # 기본 처리: 알 수 없는 질문 ID이거나 fallback일 때 텍스트 입력 제공
        input_label = "여기에 답변을 입력하세요…" if q.get("type") == "text" else "입력을 진행하세요"
        # fallback의 경우 chat_input이 더 자연스러우므로 우선 사용
        if q.get("type") == "text":
            ans = st.chat_input(input_label)
        else:
            ans = st.text_input(input_label, value="")

        if ans:
            # fallback이면 파서 호출 없이 바로 내러티브에 반영
            if q.get("id") == "fallback":
                st.session_state.narrative = ans
            else:
                _parse(q["id"], answer=ans)
            st.session_state.step += 1
            st.rerun()

else:
    st.success("면담이 끝났어요. 조금만 기다려주세요!")
    # 추천 실행
    if st.button("취향 맞는 책 추천받기"):
        payload = {
            "message": st.session_state.narrative,
            "constraints": st.session_state.constraints,
            "aladin_key": st.session_state.get("user_aladin_key", None),
            "embedding_provider": st.session_state.get("embedding_provider", None),
            "openai_key": st.session_state.get("openai_key", None),
        }
        with st.spinner("추천 생성 중…"):
            try:
                resp = requests.post(f"{API}/recommend", json=payload, timeout=90).json()
            except Exception:
                st.error("추천 서버에 연결할 수 없습니다. 나중에 다시 시도해주세요.")
                resp = {"items": []}
        items = resp.get("items", [])
        if not items:
            st.warning("조건에 맞는 결과가 없어요. 제약을 더 완화해 보세요.")
        for it in items:
            with st.container(border=True):
                cols = st.columns([1,3])
                with cols[0]:
                    if it.get("cover"): st.image(it["cover"], use_column_width=True)
                with cols[1]:
                    st.markdown(f"**{it['title']}**")
                    st.caption(f"{it.get('author','')} · {it.get('category','')} · {it.get('pubdate','')} · {it.get('isbn13','')}")
                    st.write(_pick_description(it))
                    if it.get("link"): st.link_button("알라딘에서 보기", it["link"])
    if st.button("다시 면담하기"):
        st.session_state.step = 0
        st.session_state.constraints = {}
        st.session_state.narrative = ""
        st.rerun()
