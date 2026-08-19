from __future__ import annotations

from collections.abc import Iterator, Sequence
from math import ceil
from typing import TYPE_CHECKING, Any, TypeVar

from advanced_alchemy.exceptions import ErrorMessages
from advanced_alchemy.filters import LimitOffset, StatementFilter
from advanced_alchemy.repository._util import LoadSpec
from advanced_alchemy.repository.typing import ModelT, OrderingPair
from advanced_alchemy.utils.dataclass import Empty, EmptyType
from msgspec import Struct, convert
from sqlalchemy import Select
from sqlalchemy.sql import ColumnElement

if TYPE_CHECKING:
    from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

    _ServiceMixin = SQLAlchemyAsyncRepositoryService
else:

    class _ServiceMixin:
        pass


T = TypeVar("T")


class Pagination[T]:
    def __init__(self, items: Sequence[T], total: int, page_size: int, page: int):
        self.items = items
        self.total = total
        self.page_size = page_size
        self.page = page

    @property
    def pages(self) -> int:
        if not self.total or not self.page_size:
            return 0
        return ceil(self.total / self.page_size)

    def __iter__(self) -> Iterator[Any]:
        yield from self.items

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def prev_num(self) -> int | None:
        return self.page - 1 if self.has_prev else None

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def next_num(self) -> int | None:
        return self.page + 1 if self.has_next else None

    def iter_pages(
        self,
        *,
        left_edge: int = 2,
        left_current: int = 2,
        right_current: int = 4,
        right_edge: int = 2,
    ) -> Iterator[int | None]:
        pages_end = self.pages + 1

        if pages_end == 1:
            return

        left_end = min(1 + left_edge, pages_end)
        yield from range(1, left_end)

        if left_end == pages_end:
            return

        mid_start = max(left_end, self.page - left_current)
        mid_end = min(self.page + right_current + 1, pages_end)

        if mid_start - left_end > 0:
            yield None

        yield from range(mid_start, mid_end)

        if mid_end == pages_end:
            return

        right_start = max(mid_end, pages_end - right_edge)

        if right_start - mid_end > 0:
            yield None

        yield from range(right_start, pages_end)


class PaginationServiceMixin[ModelT](_ServiceMixin):
    async def paginate(
        self,
        *filters: StatementFilter | ColumnElement[bool],
        page: int = 1,
        page_size: int = 15,
        schema_type: type[Struct] | None = None,
        statement: Select[tuple[ModelT]] | None = None,
        auto_expunge: bool | None = None,
        count_with_window_function: bool | None = None,
        order_by: list[OrderingPair] | OrderingPair | None = None,
        error_messages: ErrorMessages | EmptyType | None = Empty,
        load: LoadSpec | None = None,
        execution_options: dict[str, Any] | None = None,
        uniquify: bool | None = None,
        use_cache: bool = True,
        bind_group: str | None = None,
        **kwargs: Any,
    ) -> Pagination[Any]:
        """分页查询，可选转为展示层 Schema。

        schema_type=None 时返回 Pagination[ModelT]（ORM 实例）；
        传入 Schema 子类时返回 Pagination[Schema]，datetime 字段
        经 Schema.__post_init__ 自动转为本地 naive。
        """
        # page/page_size 兜底: HTTP 入口已 QueryParameter(ge=1) 约束,
        # 但 CLI/后台任务可能传 page<=0, 负 offset 会让 LimitOffset 抛错 -> 500。
        page = max(page, 1)
        page_size = max(page_size, 1)
        results, total = await self.get_many_and_count(
            LimitOffset(limit=page_size, offset=page_size * (page - 1)),
            *[f for f in filters if not isinstance(f, LimitOffset)],
            statement=statement,
            auto_expunge=auto_expunge,
            count_with_window_function=count_with_window_function,
            order_by=order_by,
            error_messages=error_messages,
            load=load,
            execution_options=execution_options,
            uniquify=uniquify,
            use_cache=use_cache,
            bind_group=bind_group,
            **kwargs,
        )

        if schema_type is not None:
            results = convert(results, list[schema_type], from_attributes=True)

        return Pagination(
            items=results,
            total=total,
            page_size=page_size,
            page=page,
        )
