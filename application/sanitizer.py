"""HTML 净化配置 & 函数

nh3 白名单方式净化 HTML，核心规则：
1. 只允许白名单内的标签和属性通过
2. iframe 的 src 域名必须在白名单内
3. 所有其他内容（script/事件属性等）天然剥离
"""

from __future__ import annotations

from urllib.parse import urlparse

import nh3

# 使用 selectolax 替换  BeautifulSoup4
# from bs4 import BeautifulSoup
from selectolax.lexbor import LexborHTMLParser

# === 允许的属性（按标签分组） ===
# 允许的标签 = 这个字典的 key（单一数据源，只维护一份）
# 所有标签都放行 style；style 里能留哪些 CSS 属性由 filter_style_properties 把关
ALLOWED_ATTRS: dict[str, set[str]] = {
    "p": {"style"},
    "div": {"style"},
    "h1": {"style"},
    "h2": {"style"},
    "h3": {"style"},
    "h4": {"style"},
    "h5": {"style"},
    "h6": {"style"},
    "blockquote": {"style"},
    "pre": {"style"},
    "hr": {"style"},
    "br": {"style"},
    "strong": {"style"},
    "em": {"style"},
    "u": {"style"},
    "s": {"style"},
    "del": {"style"},
    "sub": {"style"},
    "sup": {"style"},
    "mark": {"style"},
    "span": {"style"},
    "code": {"style"},
    "ul": {"style"},
    "ol": {"style"},
    "li": {"style"},
    "a": {"href", "title", "target", "rel", "style"},
    "img": {"src", "alt", "title", "width", "height", "loading", "style"},
    "table": {"style"},
    "thead": {"style"},
    "tbody": {"style"},
    "tfoot": {"style"},
    "tr": {"style"},
    "th": {"colspan", "rowspan", "scope", "style"},
    "td": {"colspan", "rowspan", "style"},
    "caption": {"style"},
    "colgroup": {"span", "style"},
    "col": {"span", "style"},
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
        "style",
    },
    "source": {"src", "type", "style"},
    "iframe": {"src", "width", "height", "frameborder", "allowfullscreen", "allow", "title", "referrerpolicy", "style"},
}

# 允许的标签 = 属性表的 key（不再单独维护一份标签名单）
ALLOWED_TAGS: set[str] = set(ALLOWED_ATTRS)

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


# 使用 selectolax 替换  BeautifulSoup4
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
        filter_style_properties={"text-align"},
        url_schemes={"http", "https", "mailto"},
        # ALLOWED_ATTRS 已显式允许 a[rel], 需关闭 nh3 默认的 link_rel 强制,
        # 否则 nh3>=0.3 对任何输入都抛 ValueError
        link_rel=None,
    )

    tree = LexborHTMLParser(cleaned)

    for iframe in tree.css("iframe"):
        src_val = iframe.attributes.get("src")
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

    return tree.body.inner_html or "" if tree.body else ""


# def sanitize_html(html_text: str) -> str:
#     """净化 HTML：剥离危险标签/属性，校验 iframe 域名白名单。

#     不在白名单内的标签属性和域名都会被删除。
#     """
#     if not html_text or not html_text.strip():
#         return ""

#     cleaned = nh3.clean(
#         html_text,
#         tags=ALLOWED_TAGS,
#         attributes=ALLOWED_ATTRS,
#         url_schemes={"http", "https", "mailto"},
#         # ALLOWED_ATTRS 已显式允许 a[rel], 需关闭 nh3 默认的 link_rel 强制,
#         # 否则 nh3>=0.3 对任何输入都抛 ValueError
#         link_rel=None,
#     )

#     # 逐 iframe 补刀：src 域名不在白名单的整个 iframe 去掉
#     # 用 lxml 解析(需遍历删除非法 iframe)。lxml 是文档解析器, 会把片段自动
#     # 补全为完整文档(套 <html><body>), 故不能用 str(soup) 返回——会把外壳
#     # 一起存进库, 污染前台 DOM 与编辑器回显。取 body 内部片段输出。
#     soup = BeautifulSoup(cleaned, "lxml")
#     for iframe in soup.find_all("iframe"):
#         src_val = iframe.get("src")
#         src = src_val.strip() if isinstance(src_val, str) else ""
#         if not src:
#             iframe.decompose()
#             continue
#         parsed = urlparse(src)
#         if parsed.hostname not in IFRAME_ALLOWED_DOMAINS or parsed.scheme not in (
#             "http",
#             "https",
#         ):
#             iframe.decompose()

#     # decode_contents() 只返回 <body> 内部子节点, 不含 html/body 外壳。
#     # 空输入已在上方过滤, 此处理论上 body 不会为 None, 兜底防脏数据。
#     return soup.body.decode_contents() if soup.body else ""
