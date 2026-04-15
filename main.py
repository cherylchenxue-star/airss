"""AirSS 主程序：调度、抓取、去重、生成 RSS."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config import (
    DEFAULT_PV,
    HEAT_24H_WINDOW,
    HEAT_GRAVITY,
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


def aggregate() -> None:
    """执行一次完整的抓取、聚合、生成 RSS 流程."""
    logger.info("===== 开始聚合任务 =====")
    all_items = []
    all_items.extend(fetch_aibase())
    all_items.extend(fetch_ithome())

    # 去重：按 link 去重，保留首次出现的条目
    seen_links: set[str] = set()
    unique_items = []
    for item in all_items:
        if item.link and item.link not in seen_links:
            seen_links.add(item.link)
            unique_items.append(item)

    # 按 24h 热度排序：24h 内按热度衰减分降序，24h 外按时间倒序
    unique_items.sort(key=_heat_score, reverse=True)

    output_path = build_rss(unique_items, OUTPUT_RSS_PATH)
    html_path = build_html(unique_items, OUTPUT_HTML_PATH)
    logger.info("RSS 已生成: %s", output_path)
    logger.info("HTML 已生成: %s (共 %d 条)", html_path, len(unique_items))


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
