from enum import Enum
from typing import Dict

class State(str, Enum):
    SQUIN = "SQUIN"
    FACTUAL = "FACTUAL"
    TITLE = "TITLE"
    RANK = "RANK"
    EXPLAIN = "EXPLAIN"

PROMPTS: Dict[State, str] = {
    State.SQUIN: "요즘 어떤 이야기/감정/분위기가 마음에 남았나요? 최근 재미있게 읽은 책의 '무엇'이 좋았는지도 편하게 말씀해 주세요.",
    State.FACTUAL: "그 이야기에서 특히 좋았던 점(캐릭터/정보/분위기/문체)은 무엇이었나요? 분량·국내/해외·전자책 가능 여부도 알려주세요.",
    State.TITLE: "추리/에세이/과학/로맨스 등 중에 더 끌리는 쪽이 있을까요? 새 작가 vs 익숙한 작가 중 선호도 알려주세요.",
}
