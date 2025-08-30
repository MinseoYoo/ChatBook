# app/services/categories.py
from typing import Dict, List, Optional

"""
알라딘 CategoryId 매핑 (대분류 예시)
- 실서비스 전 최신 분류표로 보강하세요.
"""

GENRE_TO_CATEGORY: Dict[str, int] = {
    "한국소설(2000년대 이후)": 50993,
    "에세이": 55889,
    "시": 50246,
    "추리/스릴러": 50928,
    "과학": 987,
    "인문학": 656,
    "역사": 74,
    "경제경영": 170,
    "자기계발": 336,
    "IT/컴퓨터": 798,
    "어린이": 1108,
    "청소년": 1137,
    "예술/대중문화": 517,
}

def list_genre_options() -> List[str]:
    """UI용 대분류 목록"""
    return list(GENRE_TO_CATEGORY.keys())

def get_category_id(genre_name: str) -> Optional[int]:
    return GENRE_TO_CATEGORY.get(genre_name)
