"""AiBase 新闻抓取器."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import DEFAULT_HEADERS, REQUEST_TIMEOUT, SOURCES
from fetchers.base import NewsItem
from utils.devalue import parse_devalue
from utils.tagger import auto_tag

logger = logging.getLogger(__name__)


def _session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))
    return session


def fetch() -> list[NewsItem]:
    """抓取 AiBase 新闻列表（解析 Nuxt SSR 内嵌 dehydrated 数据）."""
    url = SOURCES["aibase"]["url"]
    resp = _session().get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    html = resp.text

    # 提取 <script> 中的 dehydrated state 数组
    m = re.search(
        r'\[\["ShallowReactive",1\].*?(?=\u003c\/script\u003e)',
        html,
        re.DOTALL,
    )
    if not m:
        logger.warning("AiBase: 未找到 dehydrated state")
        return []

    try:
        data = parse_devalue(m.group(0))
        news = data["data"]["getAINewsList"]  # type: ignore[index]
        raw_list = news["data"]["list"]  # type: ignore[index]
    except (KeyError, TypeError) as exc:
        logger.warning("AiBase: 解析数据结构失败: %s", exc)
        return []

    items: list[NewsItem] = []
    for article in raw_list:
        if not isinstance(article, dict):
            continue
        title = article.get("title") or ""
        description = article.get("description") or ""
        oid = article.get("oid")
        link = f"https://news.aibase.com/zh/news/{oid}" if oid else url
        create_time = article.get("createTime") or ""
        pub_date = None
        if create_time:
            try:
                pub_date = datetime.strptime(
                    str(create_time), "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=timezone(offset=timedelta(hours=8)))
            except ValueError:
                pass

        pv = article.get("pv") or 0
        tags = auto_tag(title, description)
        items.append(
            NewsItem(
                title=title,
                link=link,
                description=description,
                source=SOURCES["aibase"]["name"],
                pub_date=pub_date,
                tags=tags,
                pv=int(pv) if pv else 0,
            )
        )

    logger.info("AiBase: 抓取 %d 条", len(items))
    return items
