"""全局配置与标签库."""

from __future__ import annotations

import os

# 输出文件路径
OUTPUT_RSS_PATH = os.environ.get("OUTPUT_RSS_PATH", "output/airss.xml")
OUTPUT_HTML_PATH = os.environ.get("OUTPUT_HTML_PATH", "output/index.html")

# 时区
TIMEZONE = "Asia/Shanghai"

# 调度时间 (小时)
SCHEDULE_HOURS = [6, 14, 24]  # 06:00, 14:00, 00:00

# 请求超时（秒）
REQUEST_TIMEOUT = 20

# 热度排序配置
DEFAULT_PV = 5000          # 无阅读量数据时的默认热度基数
HEAT_GRAVITY = 1.5         # 时间衰减指数（越大时效性权重越高）
HEAT_24H_WINDOW = 24       # 按热度排序的时间窗口（小时）

# 请求头
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# 标签库配置
TAG_CONFIG = {
    "大模型": [
        "GPT", "Claude", "Gemini", "Llama", "DeepSeek", "Qwen",
        "通义千问", "文心一言", "大模型", "Agent", "Opus", "Sonnet",
    ],
    "芯片算力": [
        "英伟达", "NVIDIA", "台积电", "AMD", "芯片", "算力",
        "华为昇腾", "摩尔线程", "三星", "2nm", "量子计算",
    ],
    "具身智能": [
        "机器人", "人形机器人", "智元", "机器狗", "波士顿动力",
        "荣耀机器人", "马斯克", "Optimus",
    ],
    "AI应用": [
        "AI视频", "AI生图", "Sora", "Stable Diffusion", "Midjourney",
        "AI音乐", "AI写作", "AI漫剧",
    ],
    "智能硬件": [
        "AI眼镜", "AI手机", "智能穿戴", "智能耳机", "AI录音笔", "AI相机",
    ],
    "企业动态": [
        "OpenAI", "Google", "微软", "Meta", "阿里", "百度",
        "字节跳动", "腾讯", "苹果", "Amazon",
    ],
    "安全伦理": [
        "AI安全", "AI诈骗", "AI幻觉", "AI侵权", "AI造假",
        "网络攻击", "监管", "立法",
    ],
    "投融资": [
        "融资", "收购", "估值", "上市", "股价",
    ],
    "国内新闻": [
        "中国", "国产", "国内", "北京", "上海", "深圳", "杭州", "广州", "南京",
        "工信部", "发改委", "科技部", "央视", "新华社", "人民日报",
        "中科院", "清华", "北大", "中科大", "华为", "阿里", "字节", "腾讯",
        "百度", "美团", "小米", "京东", "快手", "滴滴", "智元", "大疆",
        "中国移动", "中国电信", "中国联通", "中国银行", "证监会",
        "天猫", "淘宝", "京东", "拼多多", "网易云", "爱奇艺", "哔哩哔哩",
    ],
    "海外新闻": [
        "美国", "英国", "欧盟", "日本", "韩国", "德国", "法国", "印度",
        "俄罗斯", "加拿大", "澳大利亚", "新加坡", "泰国", "越南",
        "特朗普", "拜登", "马斯克", "扎克伯格", "萨姆·奥尔特曼", "奥特曼",
        "美联储", "SEC", "NASA", "五角大楼", "白宫", "国会", "北约",
        "斯坦福大学", "MIT", "牛津", "剑桥", "硅谷", "华尔街",
        "《金融时报》", "《纽约时报》", "BBC", "NBC",
    ],
}

# 源配置
SOURCES = {
    "maomu": {
        "name": "猫目",
        "url": "https://maomu.com/news",
    },
    "aibase": {
        "name": "AiBase",
        "url": "https://news.aibase.com/zh/news",
    },
    "ithome": {
        "name": "IT之家",
        "url": "https://next.ithome.com/ai",
    },
}
