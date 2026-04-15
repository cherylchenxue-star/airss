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
<title>AirSS - 全网AI核心资讯聚合</title>
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css" />
<style>
  .tag-chip { cursor: pointer; transition: all .2s; }
  .tag-chip:hover { transform: translateY(-1px); }
  .tag-active { ring: 2px; ring-offset: 1px; }
  .source-maomu { background: #fef3c7; color: #92400e; }
  .source-aibase { background: #dbeafe; color: #1e40af; }
  .source-ithome { background: #d1fae5; color: #065f46; }
</style>
</head>
<body class="bg-gray-50 text-gray-800">
<div class="max-w-5xl mx-auto px-4 py-6">
  <header class="mb-6">
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-2xl font-bold flex items-center gap-2">
          <i class="fa fa-rss text-orange-500"></i> 全网AI核心资讯聚合
        </h1>
        <p class="text-sm text-gray-500 mt-1">来源：猫目 · AiBase · IT之家</p>
      </div>
      <div class="text-right">
        <div class="text-xs text-gray-400">更新时间</div>
        <div class="font-mono text-sm" id="buildTime">{build_time}</div>
        <div class="text-xs text-gray-500 mt-1">共 <span id="totalCount" class="font-semibold">0</span> 条</div>
      </div>
    </div>
  </header>

  <div class="sticky top-0 z-10 bg-gray-50/95 backdrop-blur py-3 border-b border-gray-200 mb-4">
    <div class="flex flex-col md:flex-row gap-3">
      <div class="relative flex-1">
        <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
        <input id="searchInput" type="text" placeholder="搜索标题 / 摘要 / 标签..."
               class="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-400 bg-white" />
      </div>
      <div class="flex gap-2 overflow-x-auto pb-1" id="tagFilters">
        <span class="tag-chip px-3 py-1.5 rounded-full text-xs font-medium bg-gray-200 text-gray-700" data-tag="">全部</span>
      </div>
    </div>
  </div>

  <div id="newsList" class="space-y-4">
    <!-- JS 渲染 -->
  </div>

  <div id="emptyState" class="hidden text-center py-16 text-gray-400">
    <i class="fa fa-inbox text-4xl mb-2"></i>
    <p>未找到匹配的内容</p>
  </div>
</div>

<script>
const newsData = {json_data};

const tagColors = {
  '大模型': 'bg-purple-100 text-purple-700',
  '芯片算力': 'bg-blue-100 text-blue-700',
  '具身智能': 'bg-green-100 text-green-700',
  'AI应用': 'bg-pink-100 text-pink-700',
  '智能硬件': 'bg-indigo-100 text-indigo-700',
  '企业动态': 'bg-orange-100 text-orange-700',
  '安全伦理': 'bg-red-100 text-red-700',
  '投融资': 'bg-yellow-100 text-yellow-700',
  '国内新闻': 'bg-emerald-100 text-emerald-700',
  '海外新闻': 'bg-sky-100 text-sky-700',
};

let currentTag = '';
let searchKeyword = '';

function fmtDate(iso) {
  if (!iso) return '未知时间';
  const d = new Date(iso);
  const pad = n => n.toString().padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function sourceClass(source) {
  if (source === '猫目') return 'source-maomu';
  if (source === 'AiBase') return 'source-aibase';
  if (source === 'IT之家') return 'source-ithome';
  return 'bg-gray-100 text-gray-600';
}

function renderTags() {
  const counts = {};
  newsData.forEach(item => {
    (item.tags || []).forEach(t => counts[t] = (counts[t] || 0) + 1);
  });
  const tags = Object.entries(counts).sort((a,b) => b[1] - a[1]);
  const container = document.getElementById('tagFilters');
  container.innerHTML = `<span class="tag-chip px-3 py-1.5 rounded-full text-xs font-medium ${currentTag === '' ? 'bg-gray-800 text-white' : 'bg-gray-200 text-gray-700'}" data-tag="">全部</span>`;
  tags.forEach(([tag, count]) => {
    const active = currentTag === tag ? 'bg-gray-800 text-white' : (tagColors[tag] || 'bg-gray-100 text-gray-600');
    const el = document.createElement('span');
    el.className = `tag-chip px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap ${active}`;
    el.dataset.tag = tag;
    el.textContent = `${tag} ${count}`;
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

  document.getElementById('totalCount').textContent = filtered.length;

  if (filtered.length === 0) {
    list.innerHTML = '';
    empty.classList.remove('hidden');
    return;
  }
  empty.classList.add('hidden');

  list.innerHTML = filtered.map((item, idx) => `
    <article class="bg-white rounded-xl p-4 shadow-sm border border-gray-100 hover:shadow-md transition">
      <div class="flex items-start justify-between gap-3">
        <h2 class="text-lg font-semibold leading-snug">
          <a href="${item.link}" target="_blank" class="hover:text-orange-600">${item.title}</a>
        </h2>
        <span class="text-xs px-2 py-1 rounded-md font-medium whitespace-nowrap ${sourceClass(item.source)}">${item.source}</span>
      </div>
      <div class="flex flex-wrap gap-2 mt-2">
        ${(item.tags || []).map(t => `<span class="text-[11px] px-2 py-0.5 rounded-full ${tagColors[t] || 'bg-gray-100 text-gray-600'}">${t}</span>`).join('')}
      </div>
      <p class="text-sm text-gray-600 mt-2 line-clamp-2">${item.description}</p>
      <div class="flex items-center gap-3 mt-3 text-xs text-gray-400">
        <span><i class="fa fa-clock-o mr-1"></i>${fmtDate(item.pub_date)}</span>
        ${item.pv ? `<span class="text-orange-500 font-medium"><i class="fa fa-fire mr-1"></i>热度 ${item.pv.toLocaleString()}</span>` : ''}
        <a href="${item.link}" target="_blank" class="text-orange-500 hover:underline">阅读原文 <i class="fa fa-external-link"></i></a>
      </div>
    </article>
  `).join('');
}

document.getElementById('tagFilters').addEventListener('click', e => {
  if (e.target.classList.contains('tag-chip')) {
    currentTag = e.target.dataset.tag;
    renderTags();
    renderList();
  }
});

document.getElementById('searchInput').addEventListener('input', e => {
  searchKeyword = e.target.value;
  renderList();
});

renderTags();
renderList();
</script>
</body>
</html>
"""


def build_html(items: list[NewsItem], output_path: str) -> str:
    """生成 HTML 预览页面,返回输出路径."""
    # 将 NewsItem 序列化为 JSON 友好的 dict 列表
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
