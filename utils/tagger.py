"""智能标签识别模块."""

from __future__ import annotations

from config import TAG_CONFIG


def auto_tag(title: str, description: str) -> list[str]:
    """根据标题和摘要内容匹配关键词,返回分类标签列表."""
    text = f"{title} {description}".lower()
    tags: list[str] = []
    for tag_name, keywords in TAG_CONFIG.items():
        for kw in keywords:
            if kw.lower() in text:
                tags.append(tag_name)
                break
    return tags
