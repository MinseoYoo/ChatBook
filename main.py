# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional

from core import nlp
from core.ranker import rerank
from core.interview import QUESTIONS, parse_answer
from services.aladin import get_client, AladinError, AladinClient
from services.categories import get_category_id

app = FastAPI(title="SQUIN Book Agent")

# ---------- Interview API ----------
class InterviewQuestionsOut(BaseModel):
    questions: List[Dict]

@app.get("/interview/questions", response_model=InterviewQuestionsOut)
async def interview_questions():
    return {"questions": QUESTIONS}

class ParseIn(BaseModel):
    qid: str
    answer: str = ""
    constraints: Dict = {}
    narrative: str = ""
    structured: Optional[Dict] = None       # {"length": "..."} or {"recency": [...]} 등
    genres: Optional[List[str]] = None       # Q5 다중선택 값

class ParseOut(BaseModel):
    constraints: Dict
    narrative: str
    negatives: List[str]

@app.post("/interview/parse", response_model=ParseOut)
async def interview_parse(payload: ParseIn):
    cons, narr, negs = parse_answer(
        payload.answer,
        payload.constraints,
        payload.narrative,
        qid=payload.qid,
        structured=payload.structured,
        genre_selector=payload.genres,
    )
    return {"constraints": cons, "narrative": narr, "negatives": negs}

# ---------- Recommend API ----------
class RecommendIn(BaseModel):
    message: str
    constraints: Dict = {}
    query_type: Optional[str] = None
    category: Optional[str] = None
    category_id: Optional[int] = None
    start: int = 1
    max_results: int = 40
    isbn: Optional[str] = None
    aladin_key: Optional[str] = None
    embedding_provider: Optional[str] = None  # "sbert" or "openai"
    openai_key: Optional[str] = None

class RecommendOut(BaseModel):
    items: List[Dict]

def _book_text(b: Dict) -> str:
    sub = b.get("subInfo", {})
    return b.get("description") or sub.get("description") or b.get("title") or ""

async def _collect_books(cli, payload: RecommendIn, cat_id: Optional[int]):
    # 설명/요약을 포함하도록 OptResult 지정
    opt = "FullDescription,SubDescription,Description,Story,AuthorIntro,SubInfo"
    if payload.isbn:
        return await cli.item_lookup(item_id=payload.isbn, item_id_type="ISBN13", opt_result=opt)
    if payload.query_type:
        return await cli.item_list(
            query_type=payload.query_type, start=payload.start,
            max_results=max(payload.max_results, 10), category_id=cat_id,
            opt_result=opt,
        )
    return await cli.item_search(
        query=payload.message, start=payload.start,
        max_results=payload.max_results, category_id=cat_id,
        opt_result=opt,
    )

@app.post("/recommend", response_model=RecommendOut)
async def recommend(payload: RecommendIn):
    try:
        cli = AladinClient(api_key=payload.aladin_key) if payload.aladin_key else get_client()

        # Category 처리: 명시적 > 장르 후보
        cat_id = payload.category_id
        if not cat_id and payload.category:
            cat_id = get_category_id(payload.category)
        if not cat_id and isinstance(payload.constraints, dict):
            cand = payload.constraints.get("genre_candidates")
            if isinstance(cand, list) and cand:
                cat_id = get_category_id(cand[0])

        # 1차 시도
        books = await _collect_books(cli, payload, cat_id)
        # 결과 없음 → 완화(카테고리 제거) → 그래도 없음 → 베스트셀러 fallback
        if not books:
            books = await _collect_books(cli, payload, None)
        if not books:
            books = await cli.item_list(query_type="Bestseller", max_results=50, category_id=None)

        if not books:
            return {"items": []}

        texts = [_book_text(b) for b in books]
        bvecs = nlp.embed_texts(texts, provider=payload.embedding_provider, openai_key=payload.openai_key)
        narr_vec = nlp.embed_texts([payload.message], provider=payload.embedding_provider, openai_key=payload.openai_key)[0]

        top = rerank(narr_vec, books, bvecs, payload.constraints, topk=5)

        out = []
        for b in top:
            subinfo = b.get("subInfo", {}) or {}
            out.append({
                "title": b.get("title"),
                "author": b.get("author"),
                "isbn13": b.get("isbn13"),
                "category": b.get("categoryName"),
                "pubdate": b.get("pubDate"),
                "cover": b.get("cover"),
                "link": b.get("link"),
                "scores": b.get("_scores"),
                # 설명 계열 필드 그대로 전달하여 프런트에서 3~5문장으로 요약 노출
                "description": b.get("description") or subinfo.get("description"),
                "overview": b.get("overview") or subinfo.get("overview"),
                "fullDescription": b.get("fullDescription") or subinfo.get("fullDescription"),
                "subDescription": subinfo.get("subDescription"),
                # 여전히 제공하되 UI는 사용하지 않음
            })
        return {"items": out}

    except AladinError as e:
        raise HTTPException(status_code=502, detail=f"Aladin API error: {e}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {e}")
