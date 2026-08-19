from __future__ import annotations

from collections.abc import MutableMapping

from advanced_alchemy.exceptions import DuplicateKeyError, NotFoundError
from litestar import Request
from litestar.exceptions import (
    InternalServerException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from litestar.response import Template
from litestar.status_codes import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from litestar.types import ExceptionHandler

from application.checks import PathConflictError

__all__ = ["exception_handler"]


def bad_request_handler(request: Request, exc: Exception) -> Template:
    return Template(
        template_name="errors/400.html.j2", status_code=HTTP_400_BAD_REQUEST
    )


def permission_denied_handler(
    request: Request, exc: PermissionDeniedException
) -> Template:
    return Template(
        template_name="errors/403.html.j2",
        context={"msg": exc.detail},
        status_code=HTTP_403_FORBIDDEN,
    )


def not_found_handler(
    request: Request, exc: NotFoundError | NotFoundException
) -> Template:
    return Template(
        template_name="errors/404.html.j2",
        status_code=HTTP_404_NOT_FOUND,
    )


def internal_error_handler(request: Request, exc: Exception) -> Template:
    request.logger.exception("Unhandled exception")
    return Template(
        template_name="errors/500.html.j2",
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
    )


def conflict_handler(request: Request, exc: Exception) -> Template:
    return Template(template_name="errors/409.html.j2", status_code=HTTP_409_CONFLICT)


ExceptionConfig = MutableMapping[int | type[Exception], ExceptionHandler]

exception_handler: ExceptionConfig = {
    PathConflictError: bad_request_handler,
    ValidationException: bad_request_handler,
    PermissionDeniedException: permission_denied_handler,
    NotFoundError: not_found_handler,
    NotFoundException: not_found_handler,
    HTTP_409_CONFLICT: conflict_handler,
    DuplicateKeyError: conflict_handler,
    InternalServerException: internal_error_handler,
    Exception: internal_error_handler,
}
