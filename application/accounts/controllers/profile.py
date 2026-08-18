from __future__ import annotations

from typing import cast

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Controller, Request, get, post
from litestar.datastructures.multi_dicts import FormMultiDict
from litestar.params import URLEncodedBody
from litestar.response import Response, Template

from application.accounts.forms import PasswordForm
from application.accounts.models import User
from application.accounts.services import UserService
from application.htmx import HTMXMixin
from application.security import logout_action


class ProfileController(HTMXMixin, Controller):
    """修改密码"""

    path = "/profile"

    dependencies = {"service": create_service_provider(UserService)}

    @get(name="profile:password")
    async def password_view(self, request: Request) -> Template:
        user = cast(User, request.user)
        form = PasswordForm(current_user=user)
        return self.htmx_render(
            template_name="profile_password.html.j2",
            context={"form": form},
        )

    @post(name="profile:password_save")
    async def password_save(
        self,
        request: Request,
        data: URLEncodedBody[FormMultiDict],
        service: UserService,
    ) -> Response | Template:
        user = cast(User, request.user)
        form = PasswordForm(formdata=data, current_user=user)
        if form.validate():
            await service.update({"password_hash": form.new_password.data}, user.id)
            logout_action(request)
            return self.htmx_success("密码修改成功", redirect=data.get("url"))
        return self.htmx_render(
            template_name="profile_password.html.j2",
            context={"form": form},
        )
