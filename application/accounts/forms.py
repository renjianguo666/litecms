from __future__ import annotations

from wtforms import (
    BooleanField,
    Form,
    PasswordField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    AnyOf,
    DataRequired,
    EqualTo,
    Length,
    Optional,
    StopValidation,
)
from wtforms.widgets import CheckboxInput, ListWidget

from application.accounts.models import User


class LoginForm(Form):
    username = StringField(
        "用户名",
        validators=[DataRequired(message="用户名不能为空")],
        render_kw={"autocomplete": "off"},
    )
    password = PasswordField(
        "密码",
        validators=[DataRequired(message="密码不能为空")],
        render_kw={"autocomplete": "off"},
    )
    submit = SubmitField("登录")


class PasswordForm(Form):
    """修改密码表单"""

    old_password = PasswordField(
        "当前密码",
        validators=[DataRequired(message="当前密码不能为空")],
        render_kw={"autocomplete": "off"},
    )
    new_password = PasswordField(
        "新密码",
        validators=[
            DataRequired(message="新密码不能为空"),
            Length(min=8, message="密码至少 8 位"),
        ],
        render_kw={"autocomplete": "off"},
    )
    confirm_password = PasswordField(
        "确认新密码",
        validators=[
            DataRequired(message="确认密码不能为空"),
            EqualTo("new_password", message="两次输入的密码不一致"),
        ],
        render_kw={"autocomplete": "off"},
    )
    submit = SubmitField("修改密码")

    def __init__(
        self,
        formdata=None,
        *,
        current_user: User,
        **kwargs,
    ):
        super().__init__(formdata=formdata, **kwargs)
        self._current_user = current_user

    def validate_old_password(self, field):
        if not field.data:
            raise StopValidation("当前密码不能为空")
        if not self._current_user.password_hash.verify(field.data):
            raise StopValidation("当前密码不正确")

    def validate_new_password(self, field):
        if (
            field.data
            and self.old_password.data
            and field.data == self.old_password.data
        ):
            raise StopValidation("新密码不能与当前密码相同")


class UserCreateForm(Form):
    username = StringField(
        "用户名称",
        validators=[DataRequired(message="用户名称不能为空")],
        render_kw={"autocomplete": "off"},
    )
    password_hash = PasswordField(
        "密码",
        validators=[
            DataRequired(message="密码不能为空"),
            Length(min=8, message="密码至少 8 位"),
        ],
        render_kw={"autocomplete": "off"},
    )
    roles = SelectMultipleField("角色")
    alias = StringField(
        "别名",
        description="如不设置默认为用户名称",
        render_kw={"autocomplete": "off"},
    )
    submit = SubmitField("保存提交")


class UserEditForm(Form):
    username = StringField(
        "用户名称",
        validators=[DataRequired(message="用户名称不能为空")],
        render_kw={"autocomplete": "off"},
    )
    password_hash = PasswordField(
        "密码",
        validators=[Optional(), Length(min=8, message="密码至少 8 位")],
        render_kw={"autocomplete": "off"},
    )
    roles = SelectMultipleField("角色")
    alias = StringField(
        "别名",
        description="如不设置默认为用户名称",
        render_kw={"autocomplete": "off"},
    )
    is_active = BooleanField("启用账号")
    submit = SubmitField("保存提交")


class RoleForm(Form):
    name = StringField(
        "角色名称",
        validators=[DataRequired(message="角色名称不能为空")],
        render_kw={"autocomplete": "off"},
    )
    description = TextAreaField(
        "角色描述",
        # 空串归一 None: 全库只有 NULL 一种空状态, 输出由 schema 统一转 ''
        filters=[lambda v: (v or "").strip() or None],
    )
    permissions = SelectMultipleField(
        "权限",
        coerce=str,
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput(),
    )
    submit = SubmitField("提交保存")


class RoleDestroyForm(Form):
    name = StringField("角色名称", render_kw={"disabled": ""})
    confirm = StringField(
        "删除确认",
        validators=[AnyOf(["我确认删除"], message='请输入"我确认删除"以确认操作')],
        render_kw={"placeholder": "我确认删除"},
    )
    submit = SubmitField("确认删除")


class UserDestroyForm(Form):
    username = StringField("用户名", render_kw={"disabled": ""})
    confirm = StringField(
        "删除确认",
        validators=[AnyOf(["我确认删除"], message='请输入"我确认删除"以确认操作')],
        render_kw={"placeholder": "我确认删除"},
    )
    submit = SubmitField("确认删除")

    def disabled(self):
        for field in self:
            field.render_kw = {"disabled": ""}
