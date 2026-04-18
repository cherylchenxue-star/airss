"""HTML 预览页面生成器."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fetchers.base import NewsItem


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>每日AI新闻资讯</title>
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css" />
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&amp;display=swap" />
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans SC', sans-serif; }
  .headline-font { font-family: 'Noto Serif SC', Georgia, serif; }

  .tag-badge { transition: all 0.2s ease; }
  .tag-badge:hover { transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.1); }

  .news-card {
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    border-left: 3px solid transparent;
  }
  .news-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 28px -4px rgba(0,0,0,0.12);
    border-left-color: #4f46e5;
  }

  .heat-bar {
    background: linear-gradient(90deg, #e0e7ff 0%, #c7d2fe 50%, #6366f1 100%);
  }

  .category-tab {
    position: relative;
    transition: all 0.2s ease;
  }
  .category-tab.active::after {
    content: '';
    position: absolute;
    bottom: -2px; left: 0; right: 0;
    height: 2px;
    background: #4f46e5;
    border-radius: 2px;
  }

  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .animate-in {
    animation: fadeInUp 0.4s ease forwards;
  }

  .gradient-header {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
  }

  .live-indicator {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  .truncate-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .truncate-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .shadow-card {
    box-shadow: 0 1px 3px 0 rgba(0,0,0,0.05), 0 4px 12px 0 rgba(0,0,0,0.08);
  }
  .shadow-card-hover {
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08), 0 10px 24px 0 rgba(0,0,0,0.12);
  }
</style>
</head>
<body class="bg-gray-50 min-h-screen">

  <!-- 顶部导航 -->
  <header class="gradient-header text-white shadow-lg sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <div class="flex items-center space-x-3">
          <div class="w-9 h-9 bg-white/15 rounded-lg flex items-center justify-center backdrop-blur">
            <i class="fa fa-bolt text-yellow-400 text-lg"></i>
          </div>
          <div>
            <h1 class="text-lg font-bold tracking-wide headline-font">每日AI新闻资讯</h1>
            <p class="text-xs text-indigo-200 -mt-0.5">聚合 AiBase · IT之家 核心AI动态</p>
          </div>
        </div>
        <div class="flex items-center space-x-4">
          <div class="hidden sm:flex items-center space-x-2 text-sm text-indigo-200">
            <span class="w-2 h-2 bg-green-400 rounded-full live-indicator"></span>
            <span id="update-time">{build_time}</span>
          </div>
          <a href="airss.xml" target="_blank"
             class="hidden sm:flex items-center space-x-1.5 bg-white/15 hover:bg-white/25 px-3 py-1.5 rounded-lg text-sm transition-colors backdrop-blur">
            <i class="fa fa-rss text-orange-300"></i>
            <span>RSS 订阅</span>
          </a>
        </div>
      </div>
    </div>
  </header>

  <!-- 统计栏 -->
  <div class="bg-white border-b border-gray-200 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
      <div class="flex items-center justify-between flex-wrap gap-3">
        <div class="flex items-center space-x-6 text-sm">
          <div class="flex items-center space-x-2">
            <i class="fa fa-newspaper-o text-gray-400"></i>
            <span class="text-gray-500">今日AI资讯</span>
            <span id="total-count" class="font-bold text-indigo-700 text-lg">-</span>
            <span class="text-gray-400">条</span>
          </div>
          <div class="hidden sm:flex items-center space-x-2">
            <span class="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
            <span class="text-gray-500">AiBase</span>
            <span id="aibase-count" class="font-semibold text-gray-700">-</span>
          </div>
          <div class="hidden sm:flex items-center space-x-2">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span class="text-gray-500">IT之家</span>
            <span id="ithome-count" class="font-semibold text-gray-700">-</span>
          </div>
          <div class="hidden sm:flex items-center space-x-2">
            <span class="w-1.5 h-1.5 rounded-full bg-orange-500"></span>
            <span class="text-gray-500">24h内</span>
            <span id="in24h-count" class="font-semibold text-gray-700">-</span>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <button onclick="refreshData()" id="refresh-btn"
                  class="flex items-center space-x-1.5 text-sm text-gray-500 hover:text-indigo-600 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors">
            <i class="fa fa-refresh" id="refresh-icon"></i>
            <span>刷新</span>
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- 主体内容 -->
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <div class="flex flex-col lg:flex-row gap-6">

      <!-- 左侧：新闻列表 -->
      <div class="flex-1 min-w-0">
        <!-- 排序与时间范围 -->
        <div class="bg-white rounded-xl shadow-card p-1 mb-5 flex items-center gap-1 overflow-x-auto">
          <button onclick="setSort('heat')" id="tab-heat"
                  class="category-tab active flex-1 min-w-[80px] px-4 py-2.5 text-sm font-medium rounded-lg text-center transition-colors text-indigo-700 bg-indigo-50">
            <i class="fa fa-fire mr-1.5"></i>按热度
          </button>
          <button onclick="setSort('time')" id="tab-time"
                  class="category-tab flex-1 min-w-[80px] px-4 py-2.5 text-sm font-medium rounded-lg text-center transition-colors text-gray-600 hover:bg-gray-50">
            <i class="fa fa-clock-o mr-1.5"></i>按时间
          </button>
          <div class="shrink-0 pl-2 border-l border-gray-200 ml-1">
            <select id="time-range" onchange="setTimeRange(this.value)"
                    class="px-3 py-2 text-sm rounded-lg border border-gray-200 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 cursor-pointer">
              <option value="all">全部时间</option>
              <option value="today">今日</option>
              <option value="7days">最近7天</option>
              <option value="30days">最近30天</option>
            </select>
          </div>
        </div>

        <!-- 热门标签 -->
        <div class="mb-5">
          <div id="tag-filters" class="flex flex-wrap gap-2">
            <!-- JS渲染 -->
          </div>
        </div>

        <!-- 搜索框 -->
        <div class="relative mb-5">
          <i class="fa fa-search absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
          <input type="text" id="search-input" placeholder="搜索新闻标题、标签、来源..."
                 oninput="handleSearch(this.value)"
                 class="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all shadow-sm">
        </div>

        <!-- 新闻列表 -->
        <div id="news-list" class="space-y-4">
          <div class="text-center py-20">
            <i class="fa fa-circle-o-notch fa-spin text-3xl text-gray-300 mb-4"></i>
            <p class="text-gray-400">正在加载新闻数据...</p>
          </div>
        </div>
      </div>

      <!-- 右侧：侧边栏 -->
      <aside class="w-full lg:w-80 space-y-5">
        <!-- 来源分布 -->
        <div class="bg-white rounded-xl shadow-card p-5">
          <h3 class="text-sm font-bold text-gray-800 mb-4 flex items-center">
            <i class="fa fa-pie-chart text-indigo-500 mr-2"></i>
            来源分布
          </h3>
          <div id="source-stats" class="space-y-3">
            <span class="text-sm text-gray-400">加载中...</span>
          </div>
        </div>

        <!-- 关于 -->
        <div class="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-5 border border-indigo-100">
          <h3 class="text-sm font-bold text-indigo-800 mb-2">关于本站</h3>
          <p class="text-xs text-indigo-600/80 leading-relaxed">
            自动抓取并聚合 AiBase 与 IT之家 AI 频道的前沿资讯，按 24 小时热度智能排序，助你第一时间掌握人工智能领域核心动态。
          </p>
          <div class="mt-3 flex items-center space-x-3">
            <a href="airss.xml" target="_blank"
               class="inline-flex items-center space-x-1 text-xs text-indigo-600 hover:text-indigo-800 font-medium">
              <i class="fa fa-rss"></i>
              <span>RSS 源</span>
            </a>
            <span class="text-indigo-300">|</span>
            <span class="text-xs text-indigo-500/60">数据每 6h 更新</span>
          </div>
        </div>
      </aside>
    </div>
  </main>

  <!-- 底部 -->
  <footer class="bg-white border-t border-gray-200 mt-12">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="flex flex-col sm:flex-row items-center justify-between text-xs text-gray-400">
        <p>每日AI新闻资讯 · 数据源自 <a href="https://news.aibase.com/zh/news" target="_blank" class="text-indigo-500 hover:underline">AiBase</a> 与 <a href="https://next.ithome.com/ai" target="_blank" class="text-indigo-500 hover:underline">IT之家</a></p>
        <p class="mt-2 sm:mt-0">仅供信息参考，不代表本站立场</p>
      </div>
    </div>
  </footer>

<script>
const newsData = {json_data};

const tagColors = {
  '大模型': { color: '#9333ea', bg: '#f3e8ff' },
  '芯片算力': { color: '#2563eb', bg: '#dbeafe' },
  '具身智能': { color: '#16a34a', bg: '#dcfce7' },
  'AI应用': { color: '#db2777', bg: '#fce7f3' },
  '智能硬件': { color: '#4f46e5', bg: '#e0e7ff' },
  '企业动态': { color: '#ea580c', bg: '#ffedd5' },
  '安全伦理': { color: '#dc2626', bg: '#fee2e2' },
  '投融资': { color: '#ca8a04', bg: '#fef9c3' },
  '国内新闻': { color: '#059669', bg: '#d1fae5' },
  '海外新闻': { color: '#0ea5e9', bg: '#e0f2fe' },
};

let currentTag = '';
let currentSearch = '';
let currentSort = 'heat';
let currentTimeRange = 'all';

function fmtDate(iso) {
  if (!iso) return '未知时间';
  const d = new Date(iso);
  const pad = n => n.toString().padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function hoursAgo(iso) {
  if (!iso) return null;
  const h = (Date.now() - new Date(iso).getTime()) / 3600000;
  if (h < 1) return Math.round(h * 60) + '分钟前';
  if (h < 24) return Math.round(h) + '小时前';
  return Math.round(h / 24) + '天前';
}

function sourceMeta(source) {
  if (source === 'AiBase') return { name: 'AiBase', color: 'text-blue-700', icon: 'fa-flag', dot: 'bg-blue-500' };
  if (source === 'IT之家') return { name: 'IT之家', color: 'text-emerald-700', icon: 'fa-globe', dot: 'bg-emerald-500' };
  return { name: source, color: 'text-gray-700', icon: 'fa-newspaper-o', dot: 'bg-gray-500' };
}

function init() {
  document.getElementById('total-count').textContent = newsData.length;
  document.getElementById('aibase-count').textContent = newsData.filter(i => i.source === 'AiBase').length;
  document.getElementById('ithome-count').textContent = newsData.filter(i => i.source === 'IT之家').length;
  document.getElementById('in24h-count').textContent = newsData.filter(i => i.pub_date && (Date.now() - new Date(i.pub_date).getTime()) < 86400000).length;
  renderTagFilters();
  renderSourceStats();
  applyFilters();
}

function refreshData() {
  const icon = document.getElementById('refresh-icon');
  icon.classList.add('fa-spin');
  applyFilters();
  renderTagFilters();
  renderSourceStats();
  setTimeout(() => icon.classList.remove('fa-spin'), 500);
}

function setSort(sortType) {
  currentSort = sortType;
  document.querySelectorAll('.category-tab').forEach(btn => {
    btn.classList.remove('active', 'text-indigo-700', 'bg-indigo-50');
    btn.classList.add('text-gray-600');
  });
  const activeBtn = document.getElementById('tab-' + sortType);
  activeBtn.classList.add('active', 'text-indigo-700', 'bg-indigo-50');
  activeBtn.classList.remove('text-gray-600');
  applyFilters();
}

function setTag(tag) {
  currentTag = tag;
  renderTagFilters();
  applyFilters();
}

function setTimeRange(range) {
  currentTimeRange = range;
  applyFilters();
}

function handleSearch(value) {
  currentSearch = value.trim().toLowerCase();
  applyFilters();
}

function isInTimeRange(pubDate, range) {
  if (!pubDate || range === 'all') return true;
  const now = new Date();
  const pub = new Date(pubDate);
  const diffMs = now - pub;
  const diffDays = diffMs / 86400000;

  if (range === 'today') {
    return diffDays < 1;
  }
  if (range === '7days') {
    return diffDays < 7;
  }
  if (range === '30days') {
    return diffDays < 30;
  }
  return true;
}

function applyFilters() {
  let filtered = newsData.filter(n => {
    const matchTag = !currentTag || (n.tags || []).includes(currentTag);
    const matchSearch = !currentSearch ||
      (n.title || '').toLowerCase().includes(currentSearch) ||
      (n.description || '').toLowerCase().includes(currentSearch) ||
      (n.tags || []).some(t => t.toLowerCase().includes(currentSearch)) ||
      (n.source || '').toLowerCase().includes(currentSearch);
    const matchTime = isInTimeRange(n.pub_date, currentTimeRange);
    return matchTag && matchSearch && matchTime;
  });

  if (currentSort === 'time') {
    filtered.sort((a, b) => new Date(b.pub_date || 0) - new Date(a.pub_date || 0));
  } else {
    filtered.sort((a, b) => (b.pv || 0) - (a.pv || 0));
  }

  renderNewsList(filtered);
}

function renderNewsList(filtered) {
  const container = document.getElementById('news-list');

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="text-center py-16 bg-white rounded-xl shadow-card">
        <i class="fa fa-inbox text-4xl text-gray-300 mb-4"></i>
        <p class="text-gray-500">没有找到符合条件的新闻</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map((item, i) => renderNewsCard(item, i)).join('');
}

function renderNewsCard(item, index) {
  const rank = index + 1;
  const isTop3 = rank <= 3;
  const meta = sourceMeta(item.source);
  const timeRel = hoursAgo(item.pub_date);
  const heatPercent = Math.min(100, (item.pv || 0) / 200);

  const tagsHtml = (item.tags || []).map(tag => {
    const tc = tagColors[tag] || { color: '#6b7280', bg: '#f3f4f6' };
    return `<span class="tag-badge inline-block px-2 py-0.5 rounded text-xs font-medium" style="color:${tc.color};background:${tc.bg};border:1px solid ${tc.color}20;">${tag}</span>`;
  }).join('');

  const rankBadge = isTop3
    ? `<span class="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-700 text-white flex items-center justify-center text-sm font-bold shadow-md">${rank}</span>`
    : `<span class="w-7 h-7 rounded-lg bg-gray-100 text-gray-500 flex items-center justify-center text-sm font-medium">${rank}</span>`;

  return `
    <article class="news-card animate-in bg-white rounded-xl shadow-card p-5 sm:p-6" style="animation-delay: ${index * 0.03}s">
      <div class="flex items-start gap-4">
        <div class="flex-shrink-0 mt-0.5">${rankBadge}</div>
        <div class="flex-1 min-w-0">
          <a href="${item.link}" target="_blank" rel="noopener noreferrer" class="group block">
            <h2 class="headline-font text-base sm:text-lg font-semibold text-gray-900 leading-snug group-hover:text-indigo-700 transition-colors truncate-2">
              ${item.title}
            </h2>
          </a>

          <div class="mt-2 flex flex-wrap gap-1.5">
            ${tagsHtml}
          </div>

          <p class="mt-2.5 text-sm text-gray-500 leading-relaxed truncate-3">
            ${item.description || '暂无摘要'}
          </p>

          <div class="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-gray-400">
            <span class="flex items-center space-x-1">
              <span class="w-1.5 h-1.5 rounded-full ${meta.dot}"></span>
              <span class="${meta.color}">${meta.name}</span>
            </span>
            ${item.pub_date ? `
            <span class="flex items-center space-x-1">
              <i class="fa fa-clock-o"></i>
              <span>${fmtDate(item.pub_date)}</span>
            </span>
            ` : ''}
            ${timeRel ? `<span class="text-gray-500 font-medium">${timeRel}</span>` : ''}

            <div class="flex items-center space-x-1.5 ml-auto">
              <i class="fa fa-fire text-orange-400"></i>
              <div class="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div class="h-full rounded-full heat-bar" style="width: ${heatPercent}%"></div>
              </div>
              <span class="text-orange-500 font-medium">${item.pv || 0}</span>
            </div>
          </div>
        </div>
      </div>
    </article>
  `;
}

function renderTagFilters() {
  const tagCounts = {};
  newsData.forEach(n => {
    (n.tags || []).forEach(t => {
      tagCounts[t] = (tagCounts[t] || 0) + 1;
    });
  });

  const sortedTags = Object.entries(tagCounts).sort((a, b) => b[1] - a[1]).slice(0, 15);

  if (sortedTags.length === 0) {
    document.getElementById('tag-filters').innerHTML = '<span class="text-sm text-gray-400">暂无标签</span>';
    return;
  }

  let html = '';
  const allActive = !currentTag ? 'text-indigo-700 bg-indigo-50 border-indigo-200' : 'text-gray-600 bg-white border-gray-200 hover:bg-gray-50';
  html += `<button onclick="setTag('')" class="px-2.5 py-1 rounded-lg text-xs font-medium border transition-all ${allActive}">全部</button>`;

  html += sortedTags.map(([name, count]) => {
    const tc = tagColors[name] || { color: '#6b7280', bg: '#f3f4f6' };
    const active = currentTag === name;
    const activeClass = active ? 'ring-2 ring-indigo-500 ring-offset-1' : '';
    return `<button onclick="setTag('${name}')"
      class="tag-badge px-2.5 py-1 rounded-lg text-xs font-medium border transition-all hover:scale-105 ${activeClass}"
      style="color:${tc.color};background:${tc.bg};border-color:${tc.color}30;">
      ${name} <span class="opacity-60">${count}</span>
    </button>`;
  }).join('');

  document.getElementById('tag-filters').innerHTML = html;
}

function renderSourceStats() {
  const counts = {};
  newsData.forEach(n => {
    counts[n.source] = (counts[n.source] || 0) + 1;
  });
  const total = newsData.length;

  const colors = {
    'AiBase': { bar: 'bg-blue-500', bg: 'bg-blue-50' },
    'IT之家': { bar: 'bg-emerald-500', bg: 'bg-emerald-50' },
  };

  document.getElementById('source-stats').innerHTML = Object.entries(counts).map(([source, count]) => {
    const pct = total ? Math.round((count / total) * 100) : 0;
    const c = colors[source] || { bar: 'bg-gray-500', bg: 'bg-gray-50' };
    return `
      <div>
        <div class="flex items-center justify-between text-xs mb-1">
          <span class="text-gray-600 font-medium">${source}</span>
          <span class="text-gray-400">${count} 条 (${pct}%)</span>
        </div>
        <div class="w-full h-2 ${c.bg} rounded-full overflow-hidden">
          <div class="h-full ${c.bar} rounded-full transition-all" style="width: ${pct}%"></div>
        </div>
      </div>
    `;
  }).join('');
}

init();
</script>
</body>
</html>
"""


def build_html(items: list[NewsItem] | list[dict], output_path: str) -> str:
    """生成 HTML 预览页面,返回输出路径."""
    data = []
    for item in items:
        if isinstance(item, dict):
            data.append({
                "title": item["title"],
                "link": item["link"],
                "description": item["description"],
                "source": item["source"],
                "pub_date": item["pub_date"],
                "tags": item["tags"],
                "pv": item["pv"],
                "heat_score": item.get("heat_score", 0),
            })
        else:
            data.append({
                "title": item.title,
                "link": item.link,
                "description": item.description,
                "source": item.source,
                "pub_date": item.pub_date.isoformat() if item.pub_date else None,
                "tags": item.tags,
                "pv": item.pv,
                "heat_score": item.heat_score,
            })

    html = (
        _HTML_TEMPLATE
        .replace("{build_time}", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
        .replace("{json_data}", json.dumps(data, ensure_ascii=False))
    )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
