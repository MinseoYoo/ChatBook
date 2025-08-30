import numpy as np
from typing import List, Optional
from app.config import settings

# SBERT
from sentence_transformers import SentenceTransformer
_sbert_model = None

def _get_sbert():
    global _sbert_model
    if _sbert_model is None:
        try:
            _sbert_model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS")
        except Exception as e:
            raise RuntimeError(f"SBERT model load failed: {e}. "
                               f"Check internet or switch EMBEDDING_PROVIDER=openai") from e
    return _sbert_model

# OpenAI
from openai import OpenAI
_openai_client = None

def _get_openai(api_key: Optional[str] = None):
    global _openai_client
    # 우선 요청별 키를 우선 사용
    if api_key:
        return OpenAI(api_key=api_key)
    if _openai_client is None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY missing while EMBEDDING_PROVIDER=openai")
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client

def embed_texts(texts: List[str], *, provider: Optional[str] = None, openai_key: Optional[str] = None) -> np.ndarray:
    prov = (provider or settings.EMBEDDING_PROVIDER).lower()
    if prov == "openai":
        client = _get_openai(openai_key)
        try:
            resp = client.embeddings.create(model="text-embedding-3-large", input=texts)
            vecs = [d.embedding for d in resp.data]
            return np.array(vecs, dtype=np.float32)
        except Exception as e:
            raise RuntimeError(f"OpenAI embedding failed: {e}") from e
    # default sbert
    model = _get_sbert()
    try:
        return np.array(model.encode(texts, normalize_embeddings=True), dtype=np.float32)
    except Exception as e:
        raise RuntimeError(f"SBERT encode failed: {e}") from e
