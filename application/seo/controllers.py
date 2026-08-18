from __future__ import annotations

from typing import Annotated

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Controller, get, post
from litestar.datastructures.multi_dicts import FormMultiDict
from litestar.params import QueryParameter, URLEncodedBody
from litestar.response import Response, Template

from application.guards import PermissionGuard
from application.htmx import HTMXMixin

from .forms import PushForm
from .models import PushLog
from .schemas import PushLogSchema
from .services import PushLogService

view_permission = PermissionGuard("seo:view", "查看 SEO", "SEO 推送")
push_permission = PermissionGuard("seo:push", "推送链接", "SEO 推送")


def _build_preview_panel(
    new_urls: list[str], dupe_urls: list[str], excluded_urls: list[str]
) -> dict:
    """预览面板: 发现重复项, 不推送, 让用户选强制/跳过。"""
    details = []
    if new_urls:
        details.append(f"{len(new_urls)} 条新 URL 将推送")
    if excluded_urls:
        details.append(f"{len(excluded_urls)} 条未匹配站点将跳过")
    return {
        "mode": "preview",
        "message": f"发现 {len(dupe_urls)} 条已推送过的重复 URL，请选择如何处理",
        "details": details,
        "dupes": dupe_urls,
        "excluded": excluded_urls,
    }


def _build_done_panel(
    raw: dict, skipped_dupes: list[str], excluded_urls: list[str]
) -> dict:
    """推送完成后的结果面板。

    skipped_dupes: 被跳过的重复项(跳过模式才有); excluded_urls: 未匹配站点的。
    """
    if "error" in raw:
        return {
            "mode": "done",
            "type": "error",
            "message": f"推送失败: {raw['error']}",
            "details": [],
            "skipped_dupes": skipped_dupes,
            "excluded": excluded_urls,
        }
    total = raw.get("total", 0)
    success = raw.get("success", 0)
    errors = raw.get("errors", [])
    not_same_site = raw.get("not_same_site", [])
    not_valid = raw.get("not_valid", [])

    details = []
    if skipped_dupes:
        details.append(f"{len(skipped_dupes)} 条重复已跳过")
    if excluded_urls:
        details.append(f"{len(excluded_urls)} 条未匹配站点已跳过")
    if errors:
        details.append(f"{len(errors)} 个站点推送失败")
    if not_same_site:
        details.append(f"{len(not_same_site)} 条非本站 URL 被拒")
    if not_valid:
        details.append(f"{len(not_valid)} 条不合法 URL 被拒")

    if total == 0 and skipped_dupes:
        message = f"全部 {len(skipped_dupes)} 条已推送过，未推送"
        rtype = "error"
    elif total == 0:
        message = "没有 URL 匹配已配置站点" if excluded_urls else "没有可推送的 URL"
        rtype = "error"
    elif success == 0:
        # total>0 但 0 成功: 百度未接受任何 URL (非本站/不合法/超配额等), 不是成功
        message = f"推送失败: 0/{total} 条成功，百度未接受任何 URL"
        rtype = "error"
    else:
        message = f"推送完成: {success}/{total} 条成功"
        rtype = "success"

    return {
        "mode": "done",
        "type": rtype,
        "message": message,
        "details": details,
        "skipped_dupes": skipped_dupes,
        "excluded": excluded_urls,
        "not_same_site": not_same_site,
        "not_valid": not_valid,
    }


class SEOController(HTMXMixin, Controller):
    path = "/seo"

    dependencies = {
        "push_log_service": create_service_provider(PushLogService),
    }

    @get(name="seo:index", guards=[view_permission])
    async def index(
        self,
        push_log_service: PushLogService,
        page: Annotated[int, QueryParameter(ge=1)] = 1,
        page_size: Annotated[int, QueryParameter(ge=1, le=100)] = 10,
    ) -> Template:
        pagination = await push_log_service.paginate(
            page=page,
            page_size=page_size,
            order_by=[("created_at", True)],
            schema_type=PushLogSchema,
        )
        return self.htmx_render(
            template_name="seo_logs.html.j2",
            context={"pagination": pagination},
        )

    @get("push", name="seo:push_form", guards=[push_permission])
    async def push_form(
        self,
    ) -> Template:
        return self.htmx_render(
            template_name="seo_push_form.html.j2",
            context={"form": PushForm(), "result": None},
        )

    @post("push", name="seo:push", guards=[push_permission])
    async def push(
        self,
        data: URLEncodedBody[FormMultiDict],
        push_log_service: PushLogService,
    ) -> Response:
        """执行推送：手动输入 URL，每行一个。有重复项时先预览(强制/跳过)再推送。"""
        form = PushForm(data)
        result = None
        if form.validate():
            urls = form.urls.parsed  # URLListField 已解析为非空列表
            already_pushed = await push_log_service.get_many(
                PushLog.url.in_(urls),
                PushLog.status == "success",
            )
            already_pushed_urls = [p.url for p in already_pushed]
            new_urls, dupe_urls, excluded_urls = push_log_service.categorize_urls(
                urls, already_pushed_urls
            )
            action = form.action.data  # None=首次确认(无 radio); skip/force=预览后选择
            if action in ("force", "skip"):
                # 第二步: 已选强制/跳过, 实际推送
                to_push = new_urls + dupe_urls if action == "force" else new_urls
                raw = (
                    await push_log_service.push_to_baidu(to_push)
                    if to_push
                    else {"total": 0, "success": 0, "errors": []}
                )
                skipped_dupes = dupe_urls if action == "skip" else []
                result = _build_done_panel(raw, skipped_dupes, excluded_urls)
                form = PushForm()  # 推完清空
            elif dupe_urls:
                # 有重复但没选 action(首次或未选) -> action 报错 + 显示 radios
                form.action.errors = ["二者必须选一个"]
                result = _build_preview_panel(new_urls, dupe_urls, excluded_urls)
            else:
                # 第一步: 无重复 -> 直接推新的
                raw = (
                    await push_log_service.push_to_baidu(new_urls)
                    if new_urls
                    else {"total": 0, "success": 0, "errors": []}
                )
                result = _build_done_panel(raw, [], excluded_urls)
                form = PushForm()  # 推完清空
        return self.htmx_render(
            template_name="seo_push_form.html.j2",
            context={"form": form, "result": result},
        )
