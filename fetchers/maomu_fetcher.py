"""猫目 AI快讯抓取器."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

import requests

from config import DEFAULT_HEADERS, REQUEST_TIMEOUT, SOURCES
from fetchers.base import NewsItem
from utils.devalue import parse_devalue
from utils.tagger import auto_tag

logger = logging.getLogger(__name__)


def fetch() -> list[NewsItem]:
    """抓取猫目 AI快讯列表（解析 Vue SSR 内嵌 dehydrated 数据）."""
    url = SOURCES["maomu"]["url"]
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    html = resp.text

    m = re.search(
        r'\[\["ShallowReactive",1\].*?(?=\u003c\/script\u003e)',
        html,
        re.DOTALL,
    )
    if not m:
        logger.warning("猫目: 未找到 dehydrated state")
        return []

    try:
        data = parse_devalue(m.group(0))
    except Exception as exc:  # noqa: BLE001
        logger.warning("猫目: 解析 devalue 失败: %s", exc)
        return []

    # 递归查找 newsListFetch
    def _find_news(obj: object, depth: int = 0) -> dict | None:
        if depth > 12:
            return None
        if isinstance(obj, dict):
            if "newsListFetch" in obj:
                return obj["newsListFetch"]  # type: ignore[return-value]
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    found = _find_news(v, depth + 1)
                    if found:
                        return found
        elif isinstance(obj, list):
            for v in obj:
                if isinstance(v, (dict, list)):
                    found = _find_news(v, depth + 1)
                    if found:
                        return found
        return None

    news = _find_news(data)
    if not isinstance(news, dict):
        logger.warning("猫目: 未找到 newsListFetch")
        return []

    raw_list = news.get("list", [])
    if not isinstance(raw_list, list):
        logger.warning("猫目: newsListFetch.list 非列表")
        return []

    items: list[NewsItem] = []
    for article in raw_list:
        if not isinstance(article, dict):
            continue
        title = article.get("title") or ""
        subtitle = article.get("subtitle") or ""
        source_link = article.get("sourceLink") or ""
        sid = article.get("sid") or ""
        # 原文链接优先使用 sourceLink, 否则回退到站内详情页
        link = source_link if source_link else f"https://maomu.com/news/detail/{sid}"

        # 发布时间: 从 publishedAtDate 提取 "YYYY-MM-DD"
        pub_date = None
        published_at_date = article.get("publishedAtDate") or ""
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", str(published_at_date))
        if date_match:
            date_str = date_match.group(1)
            time_str = article.get("publishedAt") or "00:00"
            try:
                pub_date = datetime.strptime(
                    f"{date_str} {time_str}", "%Y-%m-%d %H:%M"
                ).replace(tzinfo=timezone(offset=timedelta(hours=8)))
            except ValueError:
                pass

        pv = article.get("views") or 0
        tags = auto_tag(title, subtitle)
        items.append(
            NewsItem(
                title=title,
                link=link,
                description=subtitle,
                source=SOURCES["maomu"]["name"],
                pub_date=pub_date,
                tags=tags,
                pv=int(pv) if pv else 0,
            )
        )

    logger.info("猫目: 抓取 %d 条", len(items))
    return items
