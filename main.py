"""AirSS 主程序：调度、抓取、去重、生成 RSS."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config import (
    DEFAULT_PV,
    HEAT_24H_WINDOW,
    HEAT_GRAVITY,
    HISTORY_PATH,
    OUTPUT_HTML_PATH,
    OUTPUT_RSS_PATH,
    SCHEDULE_HOURS,
    TIMEZONE,
)
from fetchers.aibase_fetcher import fetch as fetch_aibase
from fetchers.base import NewsItem
from fetchers.ithome_fetcher import fetch as fetch_ithome
from utils.html_generator import build_html
from utils.rss_generator import build_rss

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def _heat_score(item: NewsItem) -> float:
    """计算文章热度分.

    规则:
    - 24 小时内: score = PV / (小时数^重力), 分值越高越热
    - 24 小时以上: score = -小时数, 按时间倒序排后面
    - 无发布时间: 丢到最后
    """
    if not item.pub_date:
        return -999999999.0

    now = datetime.now(timezone.utc)
    pub = item.pub_date.astimezone(timezone.utc)
    hours_ago = max(0.5, (now - pub).total_seconds() / 3600)

    base_pv = item.pv if item.pv > 0 else DEFAULT_PV

    if hours_ago <= HEAT_24H_WINDOW:
        return base_pv / (hours_ago ** HEAT_GRAVITY)
    return -hours_ago


def _load_history() -> list[dict]:
    """加载历史数据."""
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("历史数据加载失败: %s", exc)
        return []


def _save_history(history: list[dict]) -> None:
    """保存历史数据."""
    os.makedirs(os.path.dirname(HISTORY_PATH) or ".", exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def _merge_to_history(items: list[NewsItem]) -> list[dict]:
    """将新抓取的文章合并到历史数据中，返回完整历史."""
    history = _load_history()
    history_map: dict[str, dict] = {h["link"]: h for h in history if h.get("link")}

    now = datetime.now(timezone.utc).isoformat()
    for item in items:
        if not item.link:
            continue
        entry = {
            "title": item.title,
            "link": item.link,
            "description": item.description,
            "source": item.source,
            "pub_date": item.pub_date.isoformat() if item.pub_date else None,
            "tags": item.tags,
            "pv": item.pv,
            "heat_score": item.heat_score,
            "fetched_at": now,
        }
        history_map[item.link] = entry

    merged = list(history_map.values())
    # 按抓取时间倒序，保留最近 90 天的数据
    cutoff = datetime.now(timezone.utc).timestamp() - 90 * 86400
    merged = [
        h for h in merged
        if h.get("fetched_at") and datetime.fromisoformat(h["fetched_at"]).timestamp() > cutoff
    ]
    return merged


def aggregate() -> None:
    """执行一次完整的抓取、聚合、生成 RSS 流程."""
    logger.info("===== 开始聚合任务 =====")
    all_items = []
    try:
        all_items.extend(fetch_aibase())
    except Exception as exc:
        logger.warning("AiBase 抓取失败: %s", exc)
    try:
        all_items.extend(fetch_ithome())
    except Exception as exc:
        logger.warning("IT之家 抓取失败: %s", exc)

    if not all_items:
        logger.error("所有来源均抓取失败，本次任务结束")
        return

    # 去重：按 link 去重，保留首次出现的条目
    seen_links: set[str] = set()
    unique_items = []
    for item in all_items:
        if item.link and item.link not in seen_links:
            seen_links.add(item.link)
            item.heat_score = _heat_score(item)
            unique_items.append(item)

    # 默认按热度排序：纯按 PV 降序
    unique_items.sort(key=lambda i: i.pv, reverse=True)

    # 合并到历史数据
    full_history = _merge_to_history(unique_items)
    _save_history(full_history)
    logger.info("历史数据已更新: %d 条", len(full_history))

    output_path = build_rss(unique_items, OUTPUT_RSS_PATH)
    html_path = build_html(full_history, OUTPUT_HTML_PATH)
    logger.info("RSS 已生成: %s", output_path)
    logger.info("HTML 已生成: %s (共 %d 条)", html_path, len(full_history))


def run_scheduler() -> None:
    """启动后台调度器."""
    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    for hour in SCHEDULE_HOURS:
        # 24 点即 00:00
        h = hour % 24
        scheduler.add_job(
            aggregate,
            trigger=CronTrigger(hour=h, minute=0),
            id=f"aggregate_{h:02d}00",
            replace_existing=True,
        )
        logger.info("已注册定时任务: %02d:00", h)
    scheduler.start()
    try:
        # 保持主线程存活
        import time
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("调度器已停止")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AirSS - AI 资讯聚合 RSS 生成器")
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="立即执行一次抓取并生成 RSS，然后退出（不启动调度器）",
    )
    args = parser.parse_args()

    if args.run_once:
        aggregate()
    else:
        # 启动时先执行一次，保证立刻有数据
        aggregate()
        run_scheduler()
