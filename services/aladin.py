"""
알라딘 Open API 클라이언트
"""
from typing import List, Dict, Optional, Literal
import httpx
from app.config import settings

BASE = "http://www.aladin.co.kr/ttb/api/"
DEFAULT_VERSION = "20131101"

SearchTarget = Literal["Book", "Foreign", "Music", "DVD"]
QueryType = Literal[
    "Bestseller", "ItemNewAll", "ItemNewSpecial", "ItemNew",
    "ItemEditorChoice", "BlogBest", "ItemNewHot", "Recommend"
]

class AladinError(RuntimeError):
    pass

class AladinClient:
    def __init__(self, api_key: Optional[str] = None, base: str = BASE):
        self.api_key = api_key or settings.ALADIN_TTB_KEY
        self.base = base.rstrip("/") + "/"

    async def _get(self, path: str, params: Dict) -> Dict:
        if not self.api_key:
            raise AladinError("ALADIN_TTB_KEY is missing. Set it in .env")
        q = {
            "ttbkey": self.api_key,
            "output": "js",
            "Version": DEFAULT_VERSION,
            **params,
        }
        try:
            async with httpx.AsyncClient(timeout=25) as client:
                r = await client.get(self.base + path, params=q)
                r.raise_for_status()
                data = r.json()
        except httpx.HTTPStatusError as e:
            raise AladinError(f"HTTP {e.response.status_code} from Aladin for {path}") from e
        except Exception as e:
            raise AladinError(f"Request to Aladin failed for {path}: {e}") from e

        if isinstance(data, dict) and "error" in data:
            raise AladinError(f"Aladin API error for {path}: {data.get('error')}")
        return data

    async def item_search(
        self, query: str, *, start: int = 1, max_results: int = 40,
        sort: str = "Accuracy", search_target: SearchTarget = "Book",
        category_id: Optional[int] = None, cover: str = "Big",
        opt_result: Optional[str] = None, author: Optional[str] = None,
        publisher: Optional[str] = None,
    ) -> List[Dict]:
        params = {
            "Query": query,
            "SearchTarget": search_target,
            "start": max(1, start),
            "MaxResults": min(max_results, 50),
            "Sort": sort,
            "Cover": cover,
        }
        if category_id: params["CategoryId"] = category_id
        if opt_result: params["OptResult"] = opt_result
        if author: params["Author"] = author
        if publisher: params["Publisher"] = publisher
        data = await self._get("ItemSearch.aspx", params)
        return data.get("item", [])

    async def item_list(
        self, *, query_type: QueryType = "Bestseller", start: int = 1,
        max_results: int = 50, search_target: SearchTarget = "Book",
        category_id: Optional[int] = None, year: Optional[int] = None,
        month: Optional[int] = None, week: Optional[int] = None,
        cover: str = "Big", opt_result: Optional[str] = None,
    ) -> List[Dict]:
        params = {
            "QueryType": query_type,
            "SearchTarget": search_target,
            "start": max(1, start),
            "MaxResults": min(max_results, 100),
            "Cover": cover,
        }
        if category_id: params["CategoryId"] = category_id
        if year: params["Year"] = year
        if month: params["Month"] = month
        if week: params["Week"] = week
        if opt_result: params["OptResult"] = opt_result
        data = await self._get("ItemList.aspx", params)
        return data.get("item", [])

    async def item_lookup(
        self, *, item_id: str, item_id_type: Literal["ISBN13", "ISBN", "ItemId"] = "ISBN13",
        cover: str = "Big", opt_result: Optional[str] = None, search_target: SearchTarget = "Book",
    ) -> List[Dict]:
        params = {
            "ItemId": item_id,
            "ItemIdType": item_id_type,
            "Cover": cover,
            "SearchTarget": search_target,
        }
        if opt_result: params["OptResult"] = opt_result
        data = await self._get("ItemLookUp.aspx", params)
        return data.get("item", [])

_client: Optional[AladinClient] = None
def get_client() -> AladinClient:
    global _client
    if _client is None:
        _client = AladinClient()
    return _client
