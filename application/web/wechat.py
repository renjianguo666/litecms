"""微信公众号 JS-SDK 分享封装。

模板里 {{ wechat_share(title="标题", desc="描述", img="图URL") | safe }}
渲染一段 <script>: wx.config + wx.ready 注入分享配置。

凭据从 .env 读 (WECHAT_APP_ID / WECHAT_APP_SECRET), 属部署级配置
(与 OSS 密钥一致, 走 config.py 的 cfg), 不进入后台 settings.toml。
凭据未配置时返回空串, 不注入 JS, 不报错。

access_token / jsapi_ticket 进程级缓存, 提前 5 分钟过期。
签名 URL 直接用 request.url (当前请求真实 URL)。

HTTP 用 aiohttp 异步获取, 不阻塞事件循环 (与 media/seo 模块一致)。
"""

from __future__ import annotations

import hashlib
import random
import time
from string import ascii_letters, digits
from typing import TYPE_CHECKING

import aiohttp
from jinja2 import Environment

from application.config import cfg

if TYPE_CHECKING:
    from litestar import Request


jinja2_env = Environment()
template = jinja2_env.from_string("""
<script type="text/javascript" src="https://res.wx.qq.com/open/js/jweixin-1.6.0.js"></script>
<script>
wx.config({
    debug: false,
    appId: "{{ appid }}",
    timestamp: {{ timestamp }},
    nonceStr: "{{ nonce_str }}",
    signature: "{{ signature }}",
    jsApiList: {{ js_api_list | tojson }}
});
wx.ready(function () {
    var share = {
        title: "{{ title }}" || document.title,
        desc: "{{ desc }}" || document.querySelector('meta[name="description"]')?.content || "",
        link: "{{ link }}" || location.href,
        imgUrl: "{{ img }}"
    };
    {%- for name in js_api_list %}
    wx.{{ name }}(share);
    {%- endfor %}
});
</script>
""")


class WeChatShare:
    """微信公众号 JS-SDK 分享。"""

    # 进程级缓存 (类变量, 全实例共享)
    _access_token = {"value": "", "expires_at": 0}
    _jsapi_ticket = {"value": "", "expires_at": 0}

    _TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
    _TICKET_URL = "https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token={token}&type=jsapi"

    def __init__(self, request: Request, *api_list: str) -> None:
        self.request = request
        self.api_list = list(api_list) if api_list else ["updateAppMessageShareData", "updateTimelineShareData"]
        self.appid = cfg.wechat_app_id
        self.app_secret = cfg.wechat_app_secret
        self.nonce_str = "".join(random.choice(ascii_letters + digits) for _ in range(15))
        self.timestamp = int(time.time())

    async def _get_access_token(self) -> str:
        now = int(time.time())
        if self._access_token["expires_at"] > now:
            return self._access_token["value"]
        timeout = aiohttp.ClientTimeout(total=10)
        async with (
            aiohttp.ClientSession(timeout=timeout) as session,
            session.get(self._TOKEN_URL.format(appid=self.appid, secret=self.app_secret)) as resp,
        ):
            resp.raise_for_status()
            data = await resp.json(content_type=None)
        token = data.get("access_token", "")
        if token:
            self._access_token["value"] = token
            self._access_token["expires_at"] = now + data.get("expires_in", 7200) - 300
        return token

    async def _get_jsapi_ticket(self) -> str:
        now = int(time.time())
        if self._jsapi_ticket["expires_at"] > now:
            return self._jsapi_ticket["value"]
        token = await self._get_access_token()
        if not token:
            return ""
        timeout = aiohttp.ClientTimeout(total=10)
        async with (
            aiohttp.ClientSession(timeout=timeout) as session,
            session.get(self._TICKET_URL.format(token=token)) as resp,
        ):
            resp.raise_for_status()
            data = await resp.json(content_type=None)
        ticket = data.get("ticket", "")
        if ticket:
            self._jsapi_ticket["value"] = ticket
            self._jsapi_ticket["expires_at"] = now + data.get("expires_in", 7200) - 300
        return ticket

    async def _signature(self) -> str:
        ticket = await self._get_jsapi_ticket()
        params = {
            "jsapi_ticket": ticket,
            "noncestr": self.nonce_str,
            "timestamp": str(self.timestamp),
            "url": str(self.request.url),
        }
        param_str = "&".join(f"{k}={params[k]}" for k in sorted(params))
        return hashlib.sha1(param_str.encode("utf-8")).hexdigest()

    async def render(self, title: str = "", desc: str = "", link: str = "", img: str = "") -> str:
        """渲染分享 JS。凭据未配置返回空串, 不注入。"""
        if not self.appid or not self.app_secret:
            return ""

        return template.render(
            appid=self.appid,
            timestamp=self.timestamp,
            nonce_str=self.nonce_str,
            signature=await self._signature(),
            js_api_list=self.api_list,
            title=title,
            desc=desc,
            link=link,
            img=img,
        )

    async def __call__(self, title: str = "", desc: str = "", link: str = "", img: str = "") -> str:
        return await self.render(title=title, desc=desc, link=link, img=img)
