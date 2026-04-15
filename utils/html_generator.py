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
<style>
  :root {
    --primary: #4f46e5;
    --primary-dark: #4338ca;
  }
  .glass {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
  }
  .card-hover {
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .card-hover:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px -12px rgba(0, 0, 0, 0.12);
  }
  .source-bar-aibase { background: linear-gradient(180deg, #3b82f6, #2563eb); }
  .source-bar-ithome { background: linear-gradient(180deg, #10b981, #059669); }
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .tag-pill {
    transition: all 0.15s ease;
  }
  .tag-pill:hover {
    transform: scale(1.05);
  }
  .search-glow:focus {
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15);
  }
</style>
</head>
<body class="bg-slate-50 text-slate-800 antialiased">

  <!-- Navbar -->
  <nav class="sticky top-0 z-50 bg-gradient-to-r from-slate-900 via-indigo-900 to-slate-900 text-white shadow-lg">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center">
            <i class="fa fa-bolt text-yellow-400 text-lg"></i>
          </div>
          <div>
            <h1 class="text-lg font-bold tracking-tight">每日AI新闻资讯</h1>
            <p class="text-[11px] text-indigo-200 hidden sm:block">聚合 AiBase · IT之家 核心AI动态</p>
          </div>
        </div>
        <div class="flex items-center gap-4">
        </div>
      </div>
    </div>
  </nav>

  <!-- Hero -->
  <header class="bg-white border-b border-slate-200">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <p class="text-sm font-semibold text-indigo-600 mb-1">AI NEWS AGGREGATOR</p>
          <h2 class="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight">每日AI新闻资讯</h2>
          <p class="text-slate-500 mt-2 max-w-xl">按 24 小时热度智能排序，助你第一时间掌握人工智能领域核心动态。</p>
        </div>
        <div class="text-right">
          <div class="text-xs text-slate-400 uppercase tracking-wider">最后更新</div>
          <div class="text-slate-700 font-mono text-sm mt-1" id="buildTime">{build_time}</div>
        </div>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
        <div class="rounded-lg bg-slate-50 border border-slate-200 p-3">
          <div class="text-xs text-slate-500">文章总数</div>
          <div class="text-xl font-bold text-slate-900 mt-1" id="statTotal">0</div>
        </div>
        <div class="rounded-lg bg-blue-50 border border-blue-100 p-3">
          <div class="text-xs text-blue-600">AiBase</div>
          <div class="text-xl font-bold text-blue-700 mt-1" id="statAibase">0</div>
        </div>
        <div class="rounded-lg bg-emerald-50 border border-emerald-100 p-3">
          <div class="text-xs text-emerald-600">IT之家</div>
          <div class="text-xl font-bold text-emerald-700 mt-1" id="statIthome">0</div>
        </div>
        <div class="rounded-lg bg-orange-50 border border-orange-100 p-3">
          <div class="text-xs text-orange-600">24h 内</div>
          <div class="text-xl font-bold text-orange-700 mt-1" id="stat24h">0</div>
        </div>
      </div>
    </div>
  </header>

  <!-- Filters -->
  <section class="sticky top-16 z-40 glass border-b border-slate-200">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <div class="flex flex-col lg:flex-row gap-4">
        <div class="relative flex-1">
          <i class="fa fa-search absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"></i>
          <input id="searchInput" type="text" placeholder="搜索标题、摘要、标签、来源..."
                 class="search-glow w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 focus:border-indigo-500 focus:outline-none bg-white text-sm" />
        </div>
        <div class="flex gap-2 overflow-x-auto pb-1 no-scrollbar" id="tagFilters">
          <button class="tag-pill px-3.5 py-2 rounded-full text-xs font-semibold bg-slate-800 text-white shadow-sm" data-tag="">全部</button>
        </div>
      </div>
    </div>
  </section>

  <!-- Content -->
  <main class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div id="newsList" class="space-y-5">
      <!-- JS rendered -->
    </div>

    <div id="emptyState" class="hidden text-center py-20">
      <div class="w-20 h-20 mx-auto rounded-full bg-slate-100 flex items-center justify-center mb-4">
        <i class="fa fa-search text-3xl text-slate-400"></i>
      </div>
      <h3 class="text-lg font-semibold text-slate-700">未找到匹配的内容</h3>
      <p class="text-sm text-slate-500 mt-1">试试切换标签或调整搜索关键词</p>
    </div>
  </main>

  <!-- Footer -->
  <footer class="bg-white border-t border-slate-200 mt-12">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="text-sm text-slate-500">
          © 2026 每日AI新闻资讯 · 数据源自 <a href="https://news.aibase.com/zh/news" target="_blank" class="text-indigo-600 hover:underline">AiBase</a> 与 <a href="https://next.ithome.com/ai" target="_blank" class="text-indigo-600 hover:underline">IT之家</a>
        </div>
        <div class="flex items-center gap-4 text-sm text-slate-500">
          <a href="airss.xml" target="_blank" class="hover:text-slate-800"><i class="fa fa-rss text-orange-500 mr-1"></i> RSS 订阅</a>
          <a href="https://github.com/cherylchenxue-star/airss" target="_blank" class="hover:text-slate-800"><i class="fa fa-github mr-1"></i> GitHub</a>
        </div>
      </div>
    </div>
  </footer>

<script>
const newsData = {json_data};

const tagColors = {
  '大模型': 'bg-purple-50 text-purple-700 border-purple-200',
  '芯片算力': 'bg-blue-50 text-blue-700 border-blue-200',
  '具身智能': 'bg-green-50 text-green-700 border-green-200',
  'AI应用': 'bg-pink-50 text-pink-700 border-pink-200',
  '智能硬件': 'bg-indigo-50 text-indigo-700 border-indigo-200',
  '企业动态': 'bg-orange-50 text-orange-700 border-orange-200',
  '安全伦理': 'bg-red-50 text-red-700 border-red-200',
  '投融资': 'bg-yellow-50 text-yellow-700 border-yellow-200',
  '国内新闻': 'bg-emerald-50 text-emerald-700 border-emerald-200',
  '海外新闻': 'bg-sky-50 text-sky-700 border-sky-200',
};

let currentTag = '';
let searchKeyword = '';

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
  if (source === 'AiBase') return { name: 'AiBase', color: 'text-blue-700 bg-blue-50 border-blue-200', bar: 'source-bar-aibase' };
  if (source === 'IT之家') return { name: 'IT之家', color: 'text-emerald-700 bg-emerald-50 border-emerald-200', bar: 'source-bar-ithome' };
  return { name: source, color: 'text-slate-700 bg-slate-100 border-slate-200', bar: 'bg-slate-400' };
}

function renderStats(items) {
  const total = items.length;
  const aibase = items.filter(i => i.source === 'AiBase').length;
  const ithome = items.filter(i => i.source === 'IT之家').length;
  const in24h = items.filter(i => i.pub_date && (Date.now() - new Date(i.pub_date).getTime()) < 86400000).length;
  document.getElementById('statTotal').textContent = total;
  document.getElementById('statAibase').textContent = aibase;
  document.getElementById('statIthome').textContent = ithome;
  document.getElementById('stat24h').textContent = in24h;
}

function renderTags(filteredItems) {
  const counts = {};
  filteredItems.forEach(item => {
    (item.tags || []).forEach(t => counts[t] = (counts[t] || 0) + 1);
  });
  const tags = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const container = document.getElementById('tagFilters');
  const allActive = currentTag === '' ? 'bg-slate-800 text-white shadow-sm' : 'bg-white text-slate-600 border border-slate-300 hover:bg-slate-50';
  container.innerHTML = `<button class="tag-pill px-3.5 py-2 rounded-full text-xs font-semibold whitespace-nowrap ${allActive}" data-tag="">全部</button>`;
  tags.forEach(([tag, count]) => {
    const active = currentTag === tag ? 'bg-slate-800 text-white shadow-sm border-transparent' : (tagColors[tag] || 'bg-white text-slate-600 border border-slate-300 hover:bg-slate-50');
    const el = document.createElement('button');
    el.className = `tag-pill px-3.5 py-2 rounded-full text-xs font-semibold whitespace-nowrap border ${active}`;
    el.dataset.tag = tag;
    el.textContent = `${tag} · ${count}`;
    container.appendChild(el);
  });
}

function renderList() {
  const list = document.getElementById('newsList');
  const empty = document.getElementById('emptyState');
  const kw = searchKeyword.trim().toLowerCase();

  const filtered = newsData.filter(item => {
    const matchTag = !currentTag || (item.tags || []).includes(currentTag);
    const matchKw = !kw ||
      (item.title || '').toLowerCase().includes(kw) ||
      (item.description || '').toLowerCase().includes(kw) ||
      (item.tags || []).join(' ').toLowerCase().includes(kw) ||
      (item.source || '').toLowerCase().includes(kw);
    return matchTag && matchKw;
  });

  renderStats(filtered);
  renderTags(filtered);

  if (filtered.length === 0) {
    list.innerHTML = '';
    empty.classList.remove('hidden');
    return;
  }
  empty.classList.add('hidden');

  list.innerHTML = filtered.map((item, idx) => {
    const meta = sourceMeta(item.source);
    const timeRel = hoursAgo(item.pub_date);
    const heatBadge = item.pv ? `<span class="inline-flex items-center gap-1 text-xs font-semibold text-orange-600 bg-orange-50 px-2 py-1 rounded-md border border-orange-100"><i class="fa fa-fire"></i> ${item.pv.toLocaleString()}</span>` : '';
    return `
    <article class="card-hover relative flex gap-4 bg-white rounded-2xl p-5 border border-slate-200">
      <div class="shrink-0 w-1.5 rounded-full ${meta.bar}"></div>
      <div class="flex-1 min-w-0">
        <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
          <h3 class="text-lg font-bold text-slate-900 leading-snug hover:text-indigo-600 transition">
            <a href="${item.link}" target="_blank" class="focus:outline-none">${item.title}</a>
          </h3>
          <div class="flex items-center gap-2 shrink-0">
            <span class="px-2.5 py-1 rounded-md text-xs font-semibold border ${meta.color}">${meta.name}</span>
            ${heatBadge}
          </div>
        </div>
        <p class="text-sm text-slate-600 mt-2 line-clamp-2 leading-relaxed">${item.description}</p>
        <div class="flex flex-wrap items-center gap-2 mt-3">
          ${(item.tags || []).map(t => `<span class="px-2 py-0.5 rounded text-[11px] font-medium border ${tagColors[t] || 'bg-slate-50 text-slate-600 border-slate-200'}">${t}</span>`).join('')}
        </div>
        <div class="flex items-center gap-4 mt-4 text-xs text-slate-400">
          <span class="flex items-center gap-1"><i class="fa fa-clock-o"></i> ${fmtDate(item.pub_date)}</span>
          ${timeRel ? `<span class="text-slate-500 font-medium">${timeRel}</span>` : ''}
          <a href="${item.link}" target="_blank" class="ml-auto sm:ml-0 text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1">阅读原文 <i class="fa fa-external-link"></i></a>
        </div>
      </div>
    </article>
    `;
  }).join('');
}

document.getElementById('tagFilters').addEventListener('click', e => {
  if (e.target.classList.contains('tag-pill')) {
    currentTag = e.target.dataset.tag;
    renderList();
  }
});

document.getElementById('searchInput').addEventListener('input', e => {
  searchKeyword = e.target.value;
  renderList();
});

renderList();
</script>
</body>
</html>
"""


def build_html(items: list[NewsItem], output_path: str) -> str:
    """生成 HTML 预览页面,返回输出路径."""
    data = []
    for item in items:
        data.append({
            "title": item.title,
            "link": item.link,
            "description": item.description,
            "source": item.source,
            "pub_date": item.pub_date.isoformat() if item.pub_date else None,
            "tags": item.tags,
            "pv": item.pv,
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
