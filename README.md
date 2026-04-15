# AirSS - 全网AI核心资讯聚合RSS

[![Deploy](https://github.com/cherylchenxue-star/airss/actions/workflows/deploy.yml/badge.svg)](https://github.com/cherylchenxue-star/airss/actions/workflows/deploy.yml)
[![Pages](https://img.shields.io/badge/GitHub%20Pages-Live-brightgreen)](https://cherylchenxue-star.github.io/airss/)

聚合 **AiBase** 与 **IT之家 AI频道** 的实时资讯，生成统一的 RSS 2.0 Feed 与可交互的 HTML 预览页，并支持 **24小时热度排序** 与 **智能标签识别**。

**在线预览** → [https://cherylchenxue-star.github.io/airss/](https://cherylchenxue-star.github.io/airss/)

---

## 核心功能

- **双源聚合**：
  - [AiBase 新闻](https://news.aibase.com/zh/news) — 侧重行业动态与产品
  - [IT之家 AI频道](https://next.ithome.com/ai) — 侧重科技新闻与硬件
- **24小时热度排序**：不是简单按时间倒序，而是基于阅读量与发布时间衰减计算热度分，让真正热门的文章浮到顶部
- **智能标签**：对标题和摘要进行关键词匹配，自动打上 10 大分类标签（含国内/海外新闻）
- **去重机制**：基于文章链接去重，避免跨源重复
- **HTML 预览页**：带搜索、标签筛选、热度标识的响应式前端页面
- **自动部署**：通过 GitHub Actions 每日定时抓取，自动部署到 GitHub Pages

---

## 热度排序算法

AirSS 的排序逻辑分为两个区间：

### 24 小时内

```
热度分 = PV / (发布小时数 ^ 1.5)
```

- **PV 越高** → 热度分越高
- **发布时间越近** → 分母越小，热度分越高
- 这样既保证高阅读量文章能持续曝光，又让最新发布的文章有合理的时效性加成

### 24 小时以上

自动切换为 **时间倒序**，旧新闻沉底。

### 跨源热度公平性

| 数据源 | 热度数据来源 | 说明 |
|--------|-------------|------|
| **AiBase** | 真实 `pv` 字段 | 网页 SSR 直接返回，真实可靠（约 5000 ~ 13000） |
| **IT之家** | 基于标签数估算 | PC 网页端无公开阅读量 API，以标签数量作为热度代理指标：基础热度 6500 + 每个标签 +500，最终落在 **7000 ~ 9500**，与 AiBase 处于同一量级 |

---

## 智能标签库

| 标签 | 触发关键词示例 |
|------|---------------|
| 大模型 | GPT, Claude, DeepSeek, Qwen, 通义千问, Agent... |
| 芯片算力 | 英伟达, NVIDIA, AMD, 芯片, 算力, 量子计算... |
| 具身智能 | 机器人, 人形机器人, 智元, Optimus... |
| AI应用 | AI视频, Sora, Midjourney, Stable Diffusion... |
| 智能硬件 | AI眼镜, AI手机, 智能穿戴... |
| 企业动态 | OpenAI, Google, 微软, 阿里, 字节跳动... |
| 安全伦理 | AI安全, AI诈骗, AI幻觉, 监管, 立法... |
| 投融资 | 融资, 收购, 估值, 上市, 股价... |
| 国内新闻 | 中国, 国产, 北京, 上海, 华为, 阿里, 清华... |
| 海外新闻 | 美国, 欧盟, 日本, 韩国, 特朗普, 美联储, 斯坦福... |

标签规则定义在 `config.py` 的 `TAG_CONFIG` 中，可自行扩展。

---

## 项目结构

```
airss/
├── .github/workflows/deploy.yml   # GitHub Actions 自动抓取 + 部署
├── config.py                      # 全局配置、标签库、源配置、热度参数
├── main.py                        # 主程序：聚合 + 热度排序 + 输出生成
├── requirements.txt               # Python 依赖
├── fetchers/
│   ├── base.py                    # NewsItem 数据模型
│   ├── aibase_fetcher.py          # AiBase 抓取器（解析 Nuxt dehydrated 数据）
│   └── ithome_fetcher.py          # IT之家抓取器（解析 SSR HTML）
├── utils/
│   ├── devalue.py                 # Nuxt/Vue SSR 脱水 JSON 解析器
│   ├── tagger.py                  # 关键词标签识别
│   ├── rss_generator.py           # RSS 2.0 XML 生成器
│   └── html_generator.py          # HTML 预览页生成器（Tailwind + 搜索/筛选）
└── output/
    ├── airss.xml                  # 生成的 RSS 文件（由 CI 自动生成）
    └── index.html                 # 生成的 HTML 预览页（由 CI 自动生成）
```

---

## 本地运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 立即运行一次

```bash
python main.py --run-once
```

运行后会在 `output/` 目录下生成：
- `airss.xml` — RSS 订阅源
- `index.html` — 可离线打开的 HTML 预览页

### 3. 启动本地定时调度

```bash
python main.py
```

程序启动时会立即抓取一次，随后在北京时间 **06:00、14:00、00:00** 自动触发。

---

## 自动化部署（GitHub Actions → GitHub Pages）

仓库已配置 `.github/workflows/deploy.yml`，无需服务器：

1. **定时触发**：北京时间每日 `06:00`、`14:00`、`23:00` 自动运行抓取
2. **生成产物**：输出 `output/airss.xml` 与 `output/index.html`
3. **自动部署**：使用 `peaceiris/actions-gh-pages` 推送到 `gh-pages` 分支
4. **Pages 生效**：GitHub Pages 从 `gh-pages` 分支提供静态访问

### 如何手动触发

进入仓库的 **Actions → Deploy AirSS** → **Run workflow**，即可立即抓取并部署。

---

## 自定义配置

可通过环境变量调整输出路径：

```bash
export OUTPUT_RSS_PATH=dist/airss.xml
export OUTPUT_HTML_PATH=dist/index.html
python main.py --run-once
```

热度参数也可在 `config.py` 中调整：

```python
DEFAULT_PV = 5000          # 无阅读量数据时的默认热度基数
HEAT_GRAVITY = 1.5         # 时间衰减指数（越大时效性越强）
HEAT_24H_WINDOW = 24       # 按热度排序的时间窗口（小时）
```

---

## 订阅 RSS

```
https://cherylchenxue-star.github.io/airss/airss.xml
```

可直接导入 Feedly、Inoreader、Reeder 等 RSS 阅读器。

---

## 许可证

MIT
