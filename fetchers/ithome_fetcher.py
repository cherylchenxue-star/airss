"""IT之家 AI频道抓取器."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from config import DEFAULT_HEADERS, REQUEST_TIMEOUT, SOURCES
from fetchers.base import NewsItem
from utils.tagger import auto_tag

logger = logging.getLogger(__name__)


def fetch() -> list[NewsItem]:
    """抓取 IT之家 AI频道新闻列表."""
    url = SOURCES["ithome"]["url"]
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    items: list[NewsItem] = []
    list_div = soup.find("div", id="list")
    if not list_div:
        logger.warning("IT之家: 未找到列表容器 #list")
        return items

    ul = list_div.find("ul", class_="bl")
    if not ul:
        logger.warning("IT之家: 未找到列表 ul.bl")
        return items

    for li in ul.find_all("li", recursive=False):
        title_a = li.find("h2")
        if not title_a:
            continue
        a = title_a.find("a", href=True)
        if not a:
            continue

        title = a.get_text(strip=True)
        link = a["href"]

        desc_div = li.find("div", class_="m")
        description = desc_div.get_text(strip=True) if desc_div else ""

        # 优先使用 data-ot 中的 ISO 时间
        c_div = li.find("div", class_="c")
        pub_date = None
        if c_div and c_div.get("data-ot"):
            try:
                pub_date = datetime.fromisoformat(c_div["data-ot"])
            except ValueError:
                pass

        tags = auto_tag(title, description)

        # IT之家网页端没有公开阅读量接口，基于标签数量做热度估算
        # 使其与 AiBase 真实 PV（约 5000-13000）处于同一量级，确保公平竞争
        tag_count = len(li.find("div", class_="tags").find_all("a")) if li.find("div", class_="tags") else 0
        estimated_pv = 6500 + tag_count * 500

        items.append(
            NewsItem(
                title=title,
                link=link,
                description=description,
                source=SOURCES["ithome"]["name"],
                pub_date=pub_date,
                tags=tags,
                pv=estimated_pv,
            )
        )

    logger.info("IT之家: 抓取 %d 条", len(items))
    return items
