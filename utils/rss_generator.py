"""RSS 生成器."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from feedgen.feed import FeedGenerator

if TYPE_CHECKING:
    from fetchers.base import NewsItem


def build_rss(items: list[NewsItem], output_path: str) -> str:
    """根据新闻列表生成 RSS 2.0 XML 文件,返回输出路径."""
    fg = FeedGenerator()
    fg.title("全网AI核心资讯聚合")
    fg.description("聚合猫目、AiBase、IT之家三大AI资讯源的实时RSS")
    fg.link(href="https://github.com/")
    fg.language("zh-CN")
    fg.lastBuildDate(datetime.now(timezone.utc))

    for item in items:
        entry = fg.add_entry(order="append")
        entry.title(item.title)
        entry.link(href=item.link)
        desc_prefix = f"【{item.source}】"
        entry.description(f"{desc_prefix}{item.description}")
        if item.pv > 0:
            entry.category(term=f"🔥热度 {item.pv:,}")
        if item.pub_date:
            entry.pubDate(item.pub_date.astimezone(timezone.utc))
        if item.tags:
            for tag in item.tags:
                entry.category(term=tag)
        entry.guid(item.link, permalink=True)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fg.rss_file(output_path, pretty=True)
    return output_path
