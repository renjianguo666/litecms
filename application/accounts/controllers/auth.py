from __future__ import annotations

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Controller, Request, get, post
from litestar.datastructures.multi_dicts import FormMultiDict
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.params import URLEncodedBody
from litestar.response import Redirect, Template

from application.accounts.forms import LoginForm
from application.accounts.services import UserService
from application.config import cfg
from application.htmx import ClientRedirect, HTMXMixin, HTMXRequest
from application.security import login_action, logout_action

LOGIN_TEMPLATE = "login.html.j2"


login_rate_limit = RateLimitConfig(rate_limit=("minute", 5))


class AuthController(HTMXMixin, Controller):
    path = "/"

    dependencies = {"service": create_service_provider(UserService)}

    @get("/login", name="auth:login_view", exclude_from_auth=True)
    async def login_view(self) -> Template:
        return Template(template_name=LOGIN_TEMPLATE, context={"form": LoginForm()})

    @post(
        "/login",
        name="auth:login",
        exclude_from_auth=True,
        middleware=[login_rate_limit.middleware],
    )
    async def login_submit(
        self,
        request: Request,
        service: UserService,
        data: URLEncodedBody[FormMultiDict],
    ) -> ClientRedirect | Redirect | Template:
        form = LoginForm(formdata=data)
        if form.validate():
            user = await service.get_one_or_none(username=form.username.data)
            if not user or not user.password_hash.verify(form.password.data):
                form.form_errors.append("用户或密码错误")
            elif not user.is_active:
                form.form_errors.append("账号已被禁用")
            else:
                login_action(request, user)
                redirect_to = request.url_for("dashboard:index")
                if isinstance(request, HTMXRequest) and request.htmx:
                    return self.htmx_redirect(redirect_to)
                return Redirect(redirect_to)

        return Template(template_name=LOGIN_TEMPLATE, context={"form": form})

    @post("/logout", name="auth:logout")
    async def logout(self, request: Request) -> ClientRedirect | Redirect:
        logout_action(request)
        if isinstance(request, HTMXRequest) and request.htmx:
            return self.htmx_redirect(f"{cfg.admin_url_prefix}/login")
        return Redirect(f"{cfg.admin_url_prefix}/login")
