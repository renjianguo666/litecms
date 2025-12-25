from __future__ import annotations

from typing import Any, Sequence, Type, cast

from advanced_alchemy.filters import LimitOffset
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from litestar import Request, Response
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.exceptions import TemplateNotFoundException
from litestar.pagination import ClassicPagination
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel


async def paginate[T: BaseModel](
    request: Request,
    schema: Type[T],
    repo: SQLAlchemyAsyncRepository,
    *filter_args,  # SQLAlchemy 表达式
    page_size: int = 10,
    order_by: Any = None,
    **filter_kwargs: Any,  # key=value 过滤
) -> ClassicPagination[dict[str, Any]]:
    page = max(1, int(request.query_params.get("page", 1)))

    result, count = await repo.list_and_count(
        LimitOffset(limit=page_size, offset=(page - 1) * page_size),
        *filter_args,
        **filter_kwargs,
        order_by=order_by,
    )

    items = [schema.model_validate(item).model_dump() for item in result]

    total_pages = (count + page_size - 1) // page_size

    return ClassicPagination(
        items=items,
        page_size=page_size,
        current_page=page,
        total_pages=total_pages,
    )


async def render_template(
    request: Request,
    template_name: str | Sequence[str],
    *,
    status_code: int = HTTP_200_OK,
    **context: Any,
) -> Response:
    engine = cast(JinjaTemplateEngine, request.app.template_engine)

    # 支持按列表顺序查找模板
    if isinstance(template_name, Sequence) and not isinstance(template_name, str):
        template_candidates = list(template_name)
    else:
        template_candidates = [cast(str, template_name)]

    template = None
    for name in template_candidates:
        try:
            template = engine.get_template(name)
            break
        except TemplateNotFoundException:
            continue

    if template is None:
        raise TemplateNotFoundException(
            template_name=template_candidates[0] if template_candidates else "unknown"
        )

    # 构建完整的上下文，包含 request
    full_context: dict[str, Any] = {"request": request}
    if context:
        full_context.update(context)

    # 使用 render_async 异步渲染模板
    html = await template.render_async(**full_context)

    return Response(
        content=html,
        media_type="text/html",
        status_code=status_code,
    )
