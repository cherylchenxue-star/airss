"""基础类型与接口."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NewsItem:
    """统一新闻条目结构."""

    title: str
    link: str
    description: str
    source: str
    pub_date: datetime | None = None
    tags: list[str] = field(default_factory=list)
    pv: int = 0
    heat_score: float = 0.0
