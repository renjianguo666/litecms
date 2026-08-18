from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.parse import urlparse

import aiohttp
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from application.mixins import PaginationServiceMixin
from application.settings.manager import load_settings

from .models import PushLog


class PushLogRepository(SQLAlchemyAsyncRepository[PushLog]):
    model_type = PushLog


class PushLogService(PaginationServiceMixin, SQLAlchemyAsyncRepositoryService[PushLog]):
    repository_type = PushLogRepository

    async def push_to_baidu(self, urls: list[str]) -> dict[str, Any]:
        """推送 URL 到百度主动收录 API，支持多站点多 Token。

        按 URL 主机匹配 baidu_push_sites 中配置的站点(每行 '站点URL|Token')，
        匹配到的按站点分组、各用对应 Token 推送；未匹配任何站点的 URL 跳过。
        site 参数用配置的站点原值(含协议, 如 https://www.abc.com), 与百度文档示例一致。

        返回 {"total": N, "success": N, "errors": [...], "not_same_site": [...], "not_valid": [...]}
        或 {"error": "..."}(站点未配置)。not_same_site/not_valid 合并各站点百度返回的未处理 URL。
        """
        sites = self._load_push_sites()
        if not sites:
            return {"error": "百度推送站点未配置，请在系统设置中配置 baidu_push_sites"}

        # host -> site_url (匹配用); site_url -> token (推送用); 同 host 以最后一条配置为准
        host_to_site = {host: site_url for site_url, host, _ in sites}
        site_token = {site_url: token for site_url, _, token in sites}
        groups: dict[str, list[str]] = {site_url: [] for site_url in site_token}
        for url in urls:
            site_url = host_to_site.get(urlparse(url).netloc)
            if site_url is not None:
                groups[site_url].append(url)

        total = sum(len(g) for g in groups.values())
        success_total = 0
        errors: list[str] = []
        not_same_site: list[str] = []
        not_valid: list[str] = []
        for site_url, group_urls in groups.items():
            if not group_urls:
                continue
            result = await self._push_one(site_url, site_token[site_url], group_urls)
            if "error" in result:
                errors.append(
                    f"{site_url}: {result.get('message') or result.get('error')}"
                )
            else:
                success_total += result.get("success", 0)
                not_same_site.extend(result.get("not_same_site") or [])
                not_valid.extend(result.get("not_valid") or [])

        return {
            "total": total,
            "success": success_total,
            "errors": errors,
            "not_same_site": not_same_site,
            "not_valid": not_valid,
        }

    def _load_push_sites(self) -> list[tuple[str, str, str]]:
        """解析百度推送配置: 每行 '站点URL|Token' -> [(site_url, host, token), ...]。

        site_url 原样作为百度接口 site 参数(含协议, 如 https://www.abc.com);
        host(netloc) 仅用于把待推送 URL 归到对应站点。
        格式不合法的行静默跳过(同 urls 字段过滤空行的惯例)。
        """
        raw = load_settings().get("baidu_push_sites", "")
        sites: list[tuple[str, str, str]] = []
        for line in (raw or "").splitlines():
            line = line.strip()
            if not line or "|" not in line:
                continue
            site_url, _, token = line.partition("|")
            site_url = site_url.strip()
            token = token.strip()
            host = urlparse(site_url).netloc
            if site_url and token and host:
                sites.append((site_url, host, token))
        return sites

    def categorize_urls(
        self, urls: list[str], already_pushed_urls: list[str]
    ) -> tuple[list[str], list[str], list[str]]:
        """把 URL 分成 (new, dupes, excluded)，不触发推送。

        new: 匹配已配置站点且未推送过; dupes: 匹配站点但此前推送成功过;
        excluded: 无匹配站点配置。供控制器做"有重复先预览"的判断。
        """
        configured_hosts = {host for _, host, _ in self._load_push_sites()}
        pushed = set(already_pushed_urls)
        new: list[str] = []
        dupes: list[str] = []
        excluded: list[str] = []
        for url in urls:
            if urlparse(url).netloc not in configured_hosts:
                excluded.append(url)
            elif url in pushed:
                dupes.append(url)
            else:
                new.append(url)
        return new, dupes, excluded

    _PUSH_MAX_RETRIES = 2  # 5xx/网络错误重试次数(百度 message: "please retry later")

    async def _push_one(
        self, site_url: str, token: str, urls: list[str]
    ) -> dict[str, Any]:
        """推送单组 URL 到百度(单站点)。

        POST http://data.zz.baidu.com/urls?site={site_url}&token={token}
        Content-Type: text/plain, body 每行一个 URL

        百度 200 返回 {remain, success, not_same_site?, not_valid?}:
        - success: 成功条数; not_same_site: 非本站未处理; not_valid: 不合法。
        百度 4xx/500 返回 {error, message}。

        5xx(含 505 "please retry later")与网络/超时错误自动重试 _PUSH_MAX_RETRIES 次;
        4xx(token 错/配额超/404 等)是真错, 不重试。
        """
        api_url = f"http://data.zz.baidu.com/urls?site={site_url}&token={token}"
        body = "\n".join(urls).encode("utf-8")
        timeout = aiohttp.ClientTimeout(total=30)

        result: dict[str, Any] = {}
        for attempt in range(self._PUSH_MAX_RETRIES + 1):
            should_retry = False
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        api_url,
                        data=body,
                        headers={"Content-Type": "text/plain"},
                    ) as resp:
                        text = await resp.text()
                        try:
                            result = json.loads(text)
                        except json.JSONDecodeError, ValueError:
                            result = {"error": f"响应非 JSON: {text[:200]}"}
                        # 5xx: 百度偶发, 重试; 2xx/4xx: 不重试
                        if resp.status >= 500 and attempt < self._PUSH_MAX_RETRIES:
                            should_retry = True
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                # 网络/超时/连接错误: 重试, 末次保留错误
                result = {"error": str(exc)}
                if attempt < self._PUSH_MAX_RETRIES:
                    should_retry = True

            if not should_retry:
                break
            await asyncio.sleep(1)

        if "error" in result:
            await self._record_batch(
                urls,
                "baidu",
                "failed",
                str(result.get("message") or result.get("error", "")),
            )
        else:
            # 百度不告知具体哪几条成功, 但明确列出被拒的: not_valid(不合法)/not_same_site(非本站)
            not_valid = set(result.get("not_valid") or [])
            not_same_site = set(result.get("not_same_site") or [])
            response_str = json.dumps(result, ensure_ascii=False)
            success_quota = result.get("success", 0)
            # 被拒的标 failed(带原因); 其余按 success 配额前 N 条 success, 超 N 的 failed
            accepted = 0
            for url in urls:
                if url in not_valid:
                    status, reason = "failed", "不合法"
                elif url in not_same_site:
                    status, reason = "failed", "非本站"
                elif accepted < success_quota:
                    status, reason = "success", ""
                    accepted += 1
                else:
                    status, reason = "failed", "超出成功配额"
                self._record(
                    url,
                    "baidu",
                    status,
                    f"{reason}: {response_str}" if reason else response_str,
                )
            await self.repository.session.commit()

        return result

    def _record(
        self,
        url: str,
        platform: str,
        status: str,
        response: str | None = None,
    ) -> None:
        """添加单条推送日志（不提交，由调用方统一 commit）。"""
        self.repository.session.add(
            PushLog(
                url=url,
                platform=platform,
                status=status,
                response=response[:1000] if response else None,
            )
        )

    async def _record_batch(
        self,
        urls: list[str],
        platform: str,
        status: str,
        response: str | None = None,
    ) -> None:
        """批量添加推送日志并提交。"""
        for url in urls:
            self._record(url, platform, status, response)
        await self.repository.session.commit()
