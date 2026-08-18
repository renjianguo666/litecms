"""HTML 净化配置 & 函数

nh3 白名单方式净化 HTML，核心规则：
1. 只允许白名单内的标签和属性通过
2. iframe 的 src 域名必须在白名单内
3. 所有其他内容（script/事件属性等）天然剥离
"""

from __future__ import annotations

from urllib.parse import urlparse

import nh3
from bs4 import BeautifulSoup

# === 允许的 HTML 标签 ===
ALLOWED_TAGS = {
    # 块级
    "p",
    "br",
    "hr",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "pre",
    "code",
    # 内联
    "strong",
    "em",
    "u",
    "s",
    "del",
    "sub",
    "sup",
    "mark",
    "span",
    "div",
    # 列表
    "ul",
    "ol",
    "li",
    # 链接 & 图片
    "a",
    "img",
    # 表格
    "table",
    "thead",
    "tbody",
    "tfoot",
    "tr",
    "th",
    "td",
    "caption",
    "colgroup",
    "col",
    # 多媒体
    "video",
    "source",
    "iframe",
}

# === 允许的属性（按标签分组） ===
ALLOWED_ATTRS: dict[str, set[str]] = {
    "a": {"href", "title", "target", "rel"},
    "img": {"src", "alt", "title", "width", "height", "loading"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan", "scope"},
    "col": {"span"},
    "colgroup": {"span"},
    "video": {
        "src",
        "controls",
        "width",
        "height",
        "poster",
        "preload",
        "autoplay",
        "loop",
        "muted",
        "playsinline",
    },
    "source": {"src", "type"},
    "iframe": {
        "src",
        "width",
        "height",
        "frameborder",
        "allowfullscreen",
        "allow",
        "title",
        "referrerpolicy",
    },
}

# === iframe src 域名白名单 ===
# 国内 + 国外主流视频平台 embed 域名
IFRAME_ALLOWED_DOMAINS = {
    # YouTube
    "www.youtube.com",
    "www.youtube-nocookie.com",
    # Bilibili
    "player.bilibili.com",
    "www.bilibili.com",
    # 腾讯视频
    "v.qq.com",
    # 优酷
    "player.youku.com",
    # 爱奇艺
    "www.iqiyi.com",
    "open.iqiyi.com",
    # 芒果 TV
    "player.mgtv.com",
    # 西瓜视频
    "www.ixigua.com",
    # 抖音
    "www.douyin.com",
    "open.douyin.com",
    # 快手
    "www.kuaishou.com",
    # 网易视频
    "v.163.com",
    # 搜狐视频
    "tv.sohu.com",
    "my.tv.sohu.com",
    # AcFun
    "www.acfun.cn",
    "player.acfun.cn",
    # PPTV
    "player.pptv.com",
    # Vimeo
    "player.vimeo.com",
    "www.vimeo.com",
    # 央视
    "player.cntv.cn",
    # 微博
    "widget.weibo.com",
}


def sanitize_html(html_text: str) -> str:
    """净化 HTML：剥离危险标签/属性，校验 iframe 域名白名单。

    不在白名单内的标签属性和域名都会被删除。
    """
    if not html_text or not html_text.strip():
        return ""

    cleaned = nh3.clean(
        html_text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        url_schemes={"http", "https", "mailto"},
        # ALLOWED_ATTRS 已显式允许 a[rel], 需关闭 nh3 默认的 link_rel 强制,
        # 否则 nh3>=0.3 对任何输入都抛 ValueError
        link_rel=None,
    )

    # 逐 iframe 补刀：src 域名不在白名单的整个 iframe 去掉
    # 用 lxml 解析(需遍历删除非法 iframe)。lxml 是文档解析器, 会把片段自动
    # 补全为完整文档(套 <html><body>), 故不能用 str(soup) 返回——会把外壳
    # 一起存进库, 污染前台 DOM 与编辑器回显。取 body 内部片段输出。
    soup = BeautifulSoup(cleaned, "lxml")
    for iframe in soup.find_all("iframe"):
        src_val = iframe.get("src")
        src = src_val.strip() if isinstance(src_val, str) else ""
        if not src:
            iframe.decompose()
            continue
        parsed = urlparse(src)
        if parsed.hostname not in IFRAME_ALLOWED_DOMAINS or parsed.scheme not in (
            "http",
            "https",
        ):
            iframe.decompose()

    # decode_contents() 只返回 <body> 内部子节点, 不含 html/body 外壳。
    # 空输入已在上方过滤, 此处理论上 body 不会为 None, 兜底防脏数据。
    return soup.body.decode_contents() if soup.body else ""
