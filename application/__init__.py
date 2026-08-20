from __future__ import annotations

from typing import Any

from litestar import Litestar
from litestar.datastructures import FormMultiDict

from .config import cfg
from .exceptions import exception_handler
from .media.storage import close_storage
from .plugins import plugins
from .router import route_handlers

__all__ = ["create_app"]


def create_app() -> Litestar:
    return Litestar(
        route_handlers=route_handlers,
        on_shutdown=[close_storage],
        plugins=[
            plugins.structlog,
            plugins.htmx,
            plugins.sqlalchemy,
            plugins.security,
            plugins.cli,
            plugins.debug_toolbar,
        ],
        stores=cfg.stores,
        response_cache_config=cfg.response_cache_config,
        template_config=cfg.template,
        csrf_config=cfg.csrf,
        compression_config=cfg.compression,
        openapi_config=cfg.openapi,
        request_max_body_size=cfg.request_max_body_size,
        exception_handlers=exception_handler,
        type_decoders=[(is_form_multidict, to_form_multidict)],
    )


# =============================================================================
# 这两个函数是 Litestar 的"类型转换器"，让 handler 能自动收到表单数据
#
# 问题在哪:
#   用户提交表单后，Litestar 默认把它解析成普通 dict。
#   但 WTForms 表单库需要的是 FormMultiDict（一种特殊的字典，
#   同一个 key 可以有多个值，比如多选框 checkbox）。
#   类型对不上，handler 里的 data 参数就拿不到数据。
#
# 怎么解决:
#   在 create_app() 里通过 type_decoders=[(判断函数, 转换函数)] 注册。
#   请求进来时，Litestar 会：
#     1. 调 is_form_multidict() 问："这个参数是不是要 FormMultiDict？"
#     2. 如果回答 True，就调 to_form_multidict() 把 dict 变成 FormMultiDict
#     3. handler 里 data 参数就拿到了能直接传给 WTForms 的 FormMultiDict
#
# 结果: handler 里写 `data: URLEncodedBody[FormMultiDict]` 就能直接用，
#       不需要手动转换。
# =============================================================================


def is_form_multidict(target_type: type) -> bool:
    return target_type is FormMultiDict


def to_form_multidict(target_type: type, value: Any) -> FormMultiDict:
    return (
        value
        if isinstance(value, FormMultiDict)
        else FormMultiDict.from_form_data(value)
    )
