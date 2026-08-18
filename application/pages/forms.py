from __future__ import annotations

from wtforms import BooleanField, Form, StringField, SubmitField, TextAreaField
from wtforms.fields.choices import SelectField
from wtforms.validators import AnyOf, DataRequired, Length, Optional, Regexp

from application.themes.utils import get_templates


class PageForm(Form):
    title = StringField(
        "标题",
        validators=[
            DataRequired(message="标题不能为空"),
            Length(max=255, message="标题不能超过 255 个字符"),
        ],
        render_kw={"autocomplete": "off"},
    )
    path = StringField(
        "路径",
        validators=[
            DataRequired(message="路径不能为空"),
            # 白名单(Django slug 思路): 只允许字母数字/下划线/连字符/点/路径分隔/,
            # 禁反斜杠(浏览器当 / 跳外站)、?#/%(URL 特殊语义)、<>空白(注入)等。
            # 填错走字段错误显式提示, 不静默转换。
            Regexp(
                r"^/[a-zA-Z0-9_\-{}.]+(?:/[a-zA-Z0-9_\-{}.]+)*/?$|^/$",
                message="路径必须以 / 开头，只能包含字母、数字、下划线、连字符及路径占位符",
            ),
            Length(max=255, message="路径不能超过 255 个字符"),
        ],
        render_kw={"placeholder": "/about"},
        description="以 / 开头， 如无 / 开头，会自动添加",
    )
    description = TextAreaField(
        "描述",
        filters=[lambda v: (v or "").strip() or None],
    )
    cover_url = StringField(
        "封面",
        render_kw={"autocomplete": "off"},
        filters=[lambda v: (v or "").strip() or None],
        validators=[Length(max=255, message="封面地址不能超过 255 个字符")],
    )
    text = TextAreaField("内容", validators=[DataRequired(message="内容不能为空")])
    template = SelectField(
        "模板",
        validators=[Optional()],
        filters=[lambda v: v or None],
    )
    is_active = BooleanField("是否上线")
    submit = SubmitField("提交保存")

    def append_field_error(self, field_name: str, message: str) -> None:
        field = self._fields.get(field_name)
        if field:
            field.errors = list(field.errors) + [message]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.template.choices = [("", "默认模板")] + [
            (item, item) for item, _ in get_templates("pages")
        ]


class PageDestroyForm(Form):
    title = StringField("单页标题", render_kw={"disabled": ""})
    confirm = StringField(
        "删除确认",
        validators=[AnyOf(["我确认删除"], message='请输入"我确认删除"以确认操作')],
        render_kw={"placeholder": "我确认删除"},
    )
    submit = SubmitField("确认删除")
