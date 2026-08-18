from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from aiohttp.abc import AbstractResolver, ResolveResult
from litestar.concurrency import sync_to_thread
from litestar.exceptions import ValidationException

# -------------------------------------------------------
# 内网 IP 段黑名单
# -------------------------------------------------------
_PRIVATE_NETS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
    ipaddress.IPv4Network("0.0.0.0/8"),  # "This" network
    ipaddress.IPv4Network("10.0.0.0/8"),  # 私有
    ipaddress.IPv4Network("100.64.0.0/10"),  # CGNAT (含阿里云内网/metadata)
    ipaddress.IPv4Network("127.0.0.0/8"),  # 环回
    ipaddress.IPv4Network("169.254.0.0/16"),  # 链路本地 (云元数据)
    ipaddress.IPv4Network("172.16.0.0/12"),  # 私有
    ipaddress.IPv4Network("192.0.0.0/24"),  # IETF 保留
    ipaddress.IPv4Network("192.168.0.0/16"),  # 私有
    ipaddress.IPv4Network("198.18.0.0/15"),  # 基准测试
    ipaddress.IPv4Network("224.0.0.0/4"),  # 组播
    ipaddress.IPv4Network("240.0.0.0/4"),  # 保留
    ipaddress.IPv6Network("::1/128"),  # IPv6 环回
    ipaddress.IPv6Network("fc00::/7"),  # IPv6 唯一本地
    ipaddress.IPv6Network("fe80::/10"),  # IPv6 链路本地
]

MAX_REDIRECTS = 3


class PinningResolver(AbstractResolver):
    """连接时解析并校验 IP: 命中内网黑名单则拒绝, 返回公网 IP。

    把 DNS 解析 + 内网校验放在 aiohttp 建连路径上, 校验与连接发生在同一处,
    消除 "校验时解析一次 / 连接时再解析一次" 的 DNS rebinding TOCTOU。
    TLS 的 SNI/证书校验仍用 URL 域名(aiohttp 行为), 不受 IP pin 影响。
    """

    async def resolve(
        self, host: str, port: int = 0, family: socket.AddressFamily = socket.AF_INET
    ) -> list[ResolveResult]:
        # 解析逻辑对齐 aiohttp.DefaultResolver: 校验后复用同一解析结果建连,
        # 消除 DNS rebinding TOCTOU。内网黑名单校验注入在拿到地址后、返回前。
        try:
            infos = await sync_to_thread(
                socket.getaddrinfo,
                host,
                port,
                type=socket.SOCK_STREAM,
                family=family,
                flags=socket.AI_ADDRCONFIG,
            )
        except socket.gaierror as e:
            raise ValidationException(f"域名解析失败: {host}") from e

        results: list[ResolveResult] = []
        for family, _type, proto, _canon, address in infos:
            if family == socket.AF_INET6 and len(address) < 3:
                # IPv6 未启用 / Python 构建不支持, 跳过
                continue
            # sockaddr 形如 (host, port) 或 IPv6 的 (host, port, ...); host 是 str
            resolved_host = str(address[0])
            ip = ipaddress.ip_address(resolved_host)
            # IPv4-mapped IPv6 (::ffff:x.x.x.x) 转回 IPv4 再查, 防止绕过
            if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
                ip = ip.ipv4_mapped
            for net in _PRIVATE_NETS:
                if ip in net:
                    raise ValidationException("不允许请求内网地址")
            results.append(
                ResolveResult(
                    hostname=host,
                    host=resolved_host,
                    port=port,
                    family=family,
                    proto=proto,
                    flags=0,
                )
            )
        return results

    async def close(self) -> None:
        pass


async def validate_url(url: str) -> str:
    """校验图片 URL scheme 与 IP 字面量, 返回原 url。

    - 域名 host: DNS 内网校验交由 PinningResolver 在连接时统一完成
      (校验与建连同一处, 消除 DNS rebinding TOCTOU)。
    - IP 字面量 host: aiohttp 建连时跳过 resolver, 故在此静态校验。
      IP 不经 DNS、不会变化, 无 rebinding 风险, 静态校验即可。

    重定向每跳都会调用。
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValidationException("只允许 http/https 链接")

    host = parsed.hostname
    if not host:
        raise ValidationException("无法解析链接中的主机名")

    # IP 字面量: aiohttp 建连跳过 resolver, 在此校验内网黑名单
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        pass  # 域名, 交给 PinningResolver 连接时校验
    else:
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
            ip = ip.ipv4_mapped
        if any(ip in net for net in _PRIVATE_NETS):
            raise ValidationException("不允许请求内网地址")

    return url
