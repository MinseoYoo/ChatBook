# app/core/ranker.py
import numpy as np
from typing import Dict, List

def rule_score(book: Dict, cons: Dict) -> float:
    s = 0.0
    sub = book.get("subInfo", {})
    # 분량
    if cons.get("max_pages") and sub.get("itemPage"):
        if sub.get("itemPage") <= cons["max_pages"]:
            s += 0.35
        else:
            s -= 0.15
    # 발간연도
    if cons.get("min_pubyear") and book.get("pubDate"):
        yr = int(book["pubDate"][:4])
        if yr >= cons["min_pubyear"]:
            s += 0.3
        else:
            s -= 0.1
    # 장르 제외어(간단 감점)
    if cons.get("exclude_terms"):
        text = (book.get("description") or "") + " " + (book.get("categoryName") or "")
        for term in cons["exclude_terms"]:
            if term and term in text:
                s -= 0.25
    return s

def popularity(book: Dict) -> float:
    r = (book.get("customerReviewRank", 0) or 0) / 10.0
    n = (book.get("salesPoint", 0) or 0)
    return 0.7 * r + 0.3 * (np.tanh(n / 5000))

def mix_score(sem: float, rule: float, pop: float, w=(0.55, 0.25, 0.20)) -> float:
    return w[0]*sem + w[1]*rule + w[2]*pop

def rerank(narr_vec, books: List[Dict], book_vecs, cons: Dict, topk=5) -> List[Dict]:
    sims = (narr_vec @ book_vecs.T).tolist()
    ranked = []
    for i, b in enumerate(books):
        sem = sims[i]
        rule = rule_score(b, cons)
        pop = popularity(b)
        total = mix_score(sem, rule, pop)
        ranked.append((total, sem, rule, pop, b))
    ranked.sort(key=lambda x: x[0], reverse=True)
    out = []
    for score, sem, rule, pop, b in ranked[:topk]:
        b["_scores"] = {"final": score, "semantic": sem, "rule": rule, "pop": pop}
        out.append(b)
    return out
