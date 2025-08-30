# app/core/interview.py
from __future__ import annotations
from typing import Dict, List, Tuple, Optional
import re
from datetime import datetime

"""
SQUIN 고정 면담:
Q1(서사/감정: 주관식) → Q2(분량: 라디오) → Q3(발간연도: 다중선택) → Q4(맥락/매력: 주관식)
→ Q5(장르: 다중선택) → Q7(제외요소: 주관식) → Q8(핵심키워드: 주관식)
※ Q6(국내/해외/포맷)은 삭제
"""

QUESTIONS: List[Dict] = [
    {"id": "Q1_SQUIN", "type": "text", "text": "최근 읽었던 책이나, 없다면 TV 프로그램, 유튜브 등 미디어에서 어떤 이야기(감정/분위기)가 마음에 남았나요?"},
    {"id": "Q2_LENGTH", "type": "radio", "text": "분량은 어느 정도가 좋아요?", "options": ["짧음(~200쪽)", "중간(~500쪽)", "장편(500쪽 이상)"]},
    {"id": "Q3_RECENCY", "type": "multiselect", "text": "발간연도/신간 여부는 중요할까요?", "options": ["비교적 최근(3년 이내)", "최신 선호(5년 이내)", "무관"]},
    {"id": "Q4_CONTEXT", "type": "multiselect", "text": "책을 선택할 때 어떤 요소를 중요하게 여기나요요? (복수 선택)", "options": [
        "속도감(내용의 진행 속도)",
        "성격 묘사(캐릭터가 서술되는 방식)",
        "설정(작품의 세계관)",
        "정보 전달성(유익한 정보 제공)",
        "문체(문장 구성)",
    ]},
    {"id": "Q5_GENRE", "type": "multiselect", "text": "장르 선호가 있나요? (복수 선택 가능)"},
    {"id": "Q7_NEG", "type": "text", "text": "피하고 싶은 요소가 있나요? (예: 철학적 주제 제외, 잔혹 장면 X 등)"},
    {"id": "Q8_END", "type": "text", "text": "마지막으로 꼭 담겼으면 하는 키워드가 있을까요? (예: 위로, 일상, 따뜻함)"},
]

def _normalize_length_choice(choice: Optional[str]) -> Optional[int]:
    if not choice:
        return None
    if "짧" in choice:
        return 200
    if "중간" in choice or "500" in choice:
        return 500
    if "장편" in choice:
        return 10000  # 사실상 무제한(규칙 점수에서 패널티 없음)
    return None

def _normalize_recency_choices(choices: List[str]) -> Optional[int]:
    """선택값을 바탕으로 min_pubyear 계산. 3년/5년/무관 동시 선택 시 더 완화된 기준(무관) 우선."""
    now_year = datetime.now().year
    if "무관" in choices or not choices:
        return None
    min_years = []
    if "비교적 최근(3년 이내)" in choices:
        min_years.append(now_year - 3)
    if "최신 선호(5년 이내)" in choices:
        min_years.append(now_year - 5)
    if not min_years:
        return None
    # 가장 완화된(가장 과거) 값을 사용
    return min(min_years)

def _extract_negatives(answer: str) -> List[str]:
    neg = []
    if re.search(r"(철학|형이상학)", answer):
        neg.append("철학적")
    if re.search(r"(잔혹|폭력|고어)", answer):
        neg.append("잔혹")
    if re.search(r"(로맨스\s*X|연애\s*X|로맨스\s*싫|연애\s*싫|로맨스\s*빼)", answer):
        neg.append("로맨스 제외")
    return neg

def parse_answer(
    answer: str,
    constraints: Dict,
    narrative: str,
    *,
    qid: Optional[str] = None,
    structured: Optional[Dict] = None,
    genre_selector: Optional[List[str]] = None,
) -> Tuple[Dict, str, List[str]]:
    """
    - answer: 사용자가 입력한 텍스트(주관식일 때)
    - structured: 객관식 선택값(예: {"length": "짧음(~200쪽)"} 또는 {"recency": ["3y","5y"]} 등)
    - genre_selector: 장르 다중선택 결과(장르명 리스트)
    """
    cons = dict(constraints or {})
    negs: List[str] = []
    new_narr = narrative

    # Q1, Q8: 주관식 -> 내러티브 강화 (Q4는 멀티셀렉트로 변경)
    if qid in {"Q1_SQUIN", "Q8_END"} and answer:
        new_narr = (narrative + " " + answer).strip()

    # Q2: 라디오(분량)
    if qid == "Q2_LENGTH" and structured and "length" in structured:
        mp = _normalize_length_choice(structured["length"])
        if mp:
            cons["max_pages"] = mp

    # Q3: 다중선택(발간연도)
    if qid == "Q3_RECENCY" and structured and "recency" in structured:
        my = _normalize_recency_choices(structured["recency"])
        if my:
            cons["min_pubyear"] = my
        else:
            cons.pop("min_pubyear", None)  # 무관 선택 시 해제

    # Q4: 다중선택(책의 매력 요소)
    if qid == "Q4_CONTEXT" and structured and "context_traits" in structured:
        selected = structured["context_traits"] or []
        if selected:
            cons["preferred_context_traits"] = selected

    # Q5: 장르 다중선택(대분류)
    if qid == "Q5_GENRE" and genre_selector:
        if genre_selector:
            cons["genre_candidates"] = genre_selector

    # Q7: 제외요소(주관식)
    if qid == "Q7_NEG" and answer:
        negs = _extract_negatives(answer)
        if negs:
            cons["exclude_terms"] = list(set(cons.get("exclude_terms", []) + negs))

    return cons, new_narr, negs
