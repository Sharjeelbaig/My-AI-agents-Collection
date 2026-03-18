from pydantic import BaseModel
from typing import List
from typing import Optional

class WebResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: Optional[str] = None
    published_date: Optional[str] = None
    relevance_score: Optional[float] = None

class WebResultList(BaseModel):
    results: List[WebResult]