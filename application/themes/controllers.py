from __future__ import annotations

from pathlib import Path
from typing import Literal

from litestar import Controller, Request, get, post
from litestar.concurrency import sync_to_thread
from litestar.datastructures.multi_dicts import FormMultiDict
from litestar.params import FromPath, FromQuery, URLEncodedBody
from litestar.response import Response, Template

from application.config import get_config
from application.guards import PermissionGuard
from application.htmx import HTMXMixin

from .forms import CreateTemplateForm, TemplateWriteForm
from .utils import get_template, get_templates

TEMPLATE_ROOT: Path = get_config().storage_dir / "templates"

KINDS: dict[str, str] = {
    "index": "首页模板",
    "categories": "栏目模板",
    "specials": "专题模板",
    "pages": "单页模板",
    "tags": "标签模板",
    "commons": "通用模板",
}

# tag 模板为固定结构（唯一、不可命名），这两个文件名是预定的
TAG_FILES = ("show.html", "index.html")

# 首页模板固定单文件 (storages/templates/index.html, 渲染时优先于内置 web_index.html)
INDEX_FILES = ("index.html",)

# 固定文件模板: 存在即优先于内置模板, 支持启用/禁用(重命名 .bak 开关)。
# index 文件在 storages/templates 根下, tags 在 storages/templates/tags/ 下。
FIXED_KINDS: dict[str, tuple[str, ...]] = {
    "index": INDEX_FILES,
    "tags": TAG_FILES,
}


TemplateKind = Literal["index", "categories", "specials", "pages", "tags", "commons"]
TemplateCreatableKind = Literal["categories", "specials", "pages", "commons"]


view_permission = PermissionGuard("templates:view", "查看模板", "模板管理")
create_permission = PermissionGuard("templates:create", "创建模板", "模板管理")
write_permission = PermissionGuard("templates:update", "编辑模板", "模板管理")


class TemplateController(HTMXMixin, Controller):
    path = "/templates"

    @get(name="templates:index", guards=[view_permission])
    async def index(
        self,
        request: Request,
        kind: FromQuery[TemplateKind] = "categories",
        target: FromQuery[str] | None = None,
    ) -> Template | Response:
        if kind == "tags":
            templates = [(f, None) for f in TAG_FILES]
        elif kind == "index":
            templates = [(f, None) for f in INDEX_FILES]
        else:
            templates = get_templates(kind)

        content = ""
        if target:
            if kind == "tags":
                # tags 模板为固定文件(show.html/index.html), 非法 target 直接拒绝,
                # 不让其直达渲染(与非 tags 分支 get_template 的路径校验对称,
                # 也避免 template_path 带非法值进模板的 Alpine x-data 上下文)。
                # target 在 TAG_FILES 但文件不存在是合法的(空编辑器创建内容), 放行。
                if target not in TAG_FILES:
                    return self.htmx_error(
                        "非法的标签模板",
                        redirect=f"{request.url_for('templates:index')}?kind={kind}",
                    )
                content = await self._read_template(TEMPLATE_ROOT / "tags" / target)
            elif kind == "index":
                # 首页模板固定单文件, 校验与 tags 同理; 文件不存在合法(空编辑器创建内容)
                if target not in INDEX_FILES:
                    return self.htmx_error(
                        "非法的首页模板",
                        redirect=f"{request.url_for('templates:index')}?kind={kind}",
                    )
                content = await self._read_template(TEMPLATE_ROOT / target)
            else:
                try:
                    tpl = get_template(kind, target)
                    content = await sync_to_thread(tpl.read_text, encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    return self.htmx_error(
                        "模板文件读取失败",
                        redirect=f"{request.url_for('templates:index')}?kind={kind}",
                    )
        states = self._fixed_states(kind)
        return self.htmx_render(
            "themes.html.j2",
            context={
                "kinds": KINDS,
                "kind": kind,
                "templates": templates,
                "template_path": target,
                "template_content": content,
                "form": CreateTemplateForm(),
                # 固定文件模板开关状态: active(原件在) / disabled(bak 在) / none(未创建)
                "fixed_states": states,
                # 当前编辑的文件是否处于禁用态(原件不在仅 .bak 在), 模板显示提示条
                "template_disabled": bool(target) and states.get(target) == "disabled",
            },
        )

    async def _read_template(self, path: Path) -> str:
        """读模板内容: 原件存在读原件, 否则读 .bak(禁用态内容在备份里, 编辑器不空)。

        编辑与启用/禁用各司其职: 禁用态保存写 .bak(见 save), 原件不重建。
        """
        if path.exists():
            return await sync_to_thread(path.read_text, encoding="utf-8")
        bak = path.with_name(path.name + ".bak")
        if bak.exists():
            return await sync_to_thread(bak.read_text, encoding="utf-8")
        return ""

    def _fixed_states(self, kind: str) -> dict[str, str]:
        """固定文件模板启用状态: 原文件在=active, 仅 .bak 在=disabled, 都没有=none。"""
        states: dict[str, str] = {}
        if kind not in FIXED_KINDS:
            return states
        root = TEMPLATE_ROOT if kind == "index" else TEMPLATE_ROOT / kind
        for fname in FIXED_KINDS[kind]:
            if (root / fname).exists():
                states[fname] = "active"
            elif (root / f"{fname}.bak").exists():
                states[fname] = "disabled"
            else:
                states[fname] = "none"
        return states

    @get("new/{kind:str}", name="templates:new", guards=[create_permission])
    async def new(self, kind: FromPath[TemplateKind]) -> Template:
        return self.htmx_render(
            "theme_form.html.j2",
            context={"form": CreateTemplateForm(data={"kind": kind})},
            block_name=None,
        )

    @post("create", name="templates:create", guards=[create_permission])
    async def create(self, data: URLEncodedBody[FormMultiDict]) -> Response | Template:
        form = CreateTemplateForm(formdata=data)
        if not form.validate():
            return self.htmx_render(
                "theme_form.html.j2", context={"form": form}, block_name=None
            )

        assert form.kind.data is not None
        assert form.name.data is not None

        base = TEMPLATE_ROOT / form.kind.data

        is_cate = form.kind.data == "categories"

        tpl = base / form.name.data if is_cate else base / f"{form.name.data}.html"

        if tpl.exists():
            form.name.errors = [
                *form.name.errors,
                f"模板已存在: {tpl.relative_to(base)}",
            ]
            return self.htmx_render(
                "theme_form.html.j2", context={"form": form}, block_name=None
            )

        try:
            if is_cate:
                await sync_to_thread(tpl.mkdir, parents=True, exist_ok=True)
                for fname in ("index.html", "list.html", "article.html"):
                    await sync_to_thread((tpl / fname).touch)
            else:
                await sync_to_thread(tpl.parent.mkdir, parents=True, exist_ok=True)
                await sync_to_thread(tpl.touch)
        except (PermissionError, FileNotFoundError, OSError):
            return self.htmx_error("创建模板失败", skip_redirect=True)

        return self.htmx_success("创建成功")

    @post(name="templates:write", guards=[write_permission])
    async def save(self, data: URLEncodedBody[FormMultiDict]) -> Response:
        form = TemplateWriteForm(formdata=data)
        if not form.validate():
            return self.htmx_error("表单验证失败", skip_redirect=True)

        assert form.kind.data is not None
        assert form.name.data is not None
        assert form.content.data is not None

        fixed: Path | None = None
        if form.kind.data == "tags":
            if form.name.data not in TAG_FILES:
                return self.htmx_error("非法的标签模板文件", skip_redirect=True)
            fixed = TEMPLATE_ROOT / "tags" / form.name.data
        elif form.kind.data == "index":
            if form.name.data not in INDEX_FILES:
                return self.htmx_error("非法的首页模板文件", skip_redirect=True)
            fixed = TEMPLATE_ROOT / form.name.data

        try:
            if fixed is not None:
                # 禁用态(原件不在仅 .bak 在): 保存只更新备份, 不重建原件——
                # 编辑与启用/禁用各司其职, 生效与否完全由按钮开关决定
                if not fixed.exists() and fixed.with_name(fixed.name + ".bak").exists():
                    fixed = fixed.with_name(fixed.name + ".bak")
                await sync_to_thread(fixed.parent.mkdir, parents=True, exist_ok=True)
                tpl = fixed
            else:
                tpl = get_template(form.kind.data, form.name.data)
            await sync_to_thread(tpl.write_text, form.content.data, encoding="utf-8")
        except (PermissionError, FileNotFoundError, OSError):
            return self.htmx_error("模板保存失败", skip_redirect=True)

        return self.htmx_success("保存成功", skip_redirect=True)

    @post("disable", name="templates:disable", guards=[write_permission])
    async def disable(
        self, request: Request, data: URLEncodedBody[FormMultiDict]
    ) -> Response:
        """禁用固定文件模板 (index/tags): 文件 → 文件.bak, 前台回退内置模板。"""
        kind, name = data.get("kind"), data.get("name")
        if kind not in FIXED_KINDS or name not in FIXED_KINDS[kind]:
            return self.htmx_error("非法的模板文件", skip_redirect=True)
        root = TEMPLATE_ROOT if kind == "index" else TEMPLATE_ROOT / kind
        tpl = root / name
        if tpl.exists():
            bak = root / f"{name}.bak"
            if bak.exists():
                await sync_to_thread(bak.unlink)
            await sync_to_thread(tpl.rename, bak)
        return self.htmx_success(
            "已禁用模板",
            # 带 target 跳回当前编辑的文件, 不落回空编辑器
            redirect=f"{request.url_for('templates:index')}?kind={kind}&target={name}",
        )

    @post("enable", name="templates:enable", guards=[write_permission])
    async def enable(
        self, request: Request, data: URLEncodedBody[FormMultiDict]
    ) -> Response:
        """启用固定文件模板 (index/tags): 文件.bak → 文件, 前台恢复自定义模板。

        若原件已存在(禁用期间编辑保存过, 内容比 .bak 新): 新内容优先, 丢旧备份。
        """
        kind, name = data.get("kind"), data.get("name")
        if kind not in FIXED_KINDS or name not in FIXED_KINDS[kind]:
            return self.htmx_error("非法的模板文件", skip_redirect=True)
        root = TEMPLATE_ROOT if kind == "index" else TEMPLATE_ROOT / kind
        bak = root / f"{name}.bak"
        if bak.exists():
            tpl = root / name
            if tpl.exists():
                await sync_to_thread(
                    bak.unlink
                )  # 禁用期间保存过新内容(原件重建): 不覆盖, 丢旧备份
            else:
                await sync_to_thread(bak.rename, tpl)
        return self.htmx_success(
            "已启用模板",
            # 带 target 跳回当前编辑的文件, 不落回空编辑器
            redirect=f"{request.url_for('templates:index')}?kind={kind}&target={name}",
        )
