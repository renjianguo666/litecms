from __future__ import annotations

import uuid

from wtforms import (
    BooleanField,
    Form,
    IntegerField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import UUID, AnyOf, DataRequired, Optional, Regexp

from application.themes.utils import get_templates


def get_category_template_choices(kind: str) -> list[tuple[str, str]]:
    templates = get_templates(kind)
    groups = {group for _, group in templates if group is not None}
    return [(g, g) for g in groups]


class CategoryForm(Form):
    parent_id = StringField(
        "父栏目",
        validators=[Optional(), UUID(message="非法的父栏目 ID 格式")],
        filters=[lambda x: x if x else None],
    )
    name = StringField(
        "栏目名称", validators=[DataRequired()], render_kw={"autocomplete": "off"}
    )
    title = StringField(
        "栏目标题",
        render_kw={"autocomplete": "off"},
        filters=[lambda v: (v or "").strip() or None],
    )
    description = TextAreaField(
        "栏目描述",
        filters=[lambda v: (v or "").strip() or None],
    )
    cover_url = StringField(
        "栏目图片",
        render_kw={"autocomplete": "off"},
        filters=[lambda v: (v or "").strip() or None],
    )

    path = StringField(
        "栏目路径",
        validators=[
            DataRequired(message="栏目路径不能为空"),
            # 白名单(Django slug 思路): 只允许字母数字/下划线/连字符/点/路径分隔/
            # 及占位符 {}. 禁反斜杠(浏览器当 / 跳外站)、?#/%(URL 特殊语义)、<>空白等。
            Regexp(
                r"^/[a-zA-Z0-9_\-{}.]+(?:/[a-zA-Z0-9_\-{}.]+)*/?$|^/$",
                message="路径必须以 / 开头，只能包含字母、数字、下划线、连字符及路径占位符",
            ),
        ],
        description="占位符：key、parent、year、yy、month、mm、day、dd、num",
        render_kw={"autocomplete": "off", "placeholder": "/{parent}/{key}"},
    )
    content_path = StringField(
        "内容路径",
        validators=[
            DataRequired(message="内容路径不能为空"),
            Regexp(
                r"^/[a-zA-Z0-9_\-{}.]+(?:/[a-zA-Z0-9_\-{}.]+)*/?$|^/$",
                message="路径必须以 / 开头，只能包含字母、数字、下划线、连字符及路径占位符",
            ),
        ],
        description="占位符：key、category、year、yy、month、mm、day、dd、num",
        render_kw={"autocomplete": "off", "placeholder": "/{category}/{key}"},
    )

    domain = StringField(
        "域名",
        description="绑定域名后内容归属站点 sitemap; 留空归主站",
        filters=[lambda v: (v or "").strip() or None],
    )

    page_size = IntegerField("页面大小", default=20)
    priority = IntegerField("优先级", default=0)
    template = SelectField(
        "模板",
        validators=[Optional()],
        filters=[lambda v: v or None],
    )

    submit = SubmitField("提交保存")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.template.choices = [("", "默认模板")] + get_category_template_choices(
            "categories"
        )

    def append_field_error(self, field_name: str, message: str) -> None:
        field = self._fields.get(field_name)
        if field:
            field.errors = list(field.errors) + [message]


class SpecialForm(Form):
    name = StringField(
        "名称", validators=[DataRequired()], render_kw={"autocomplete": "off"}
    )
    title = StringField(
        "标题", validators=[DataRequired()], render_kw={"autocomplete": "off"}
    )
    slug = StringField(
        "URL标识",
        validators=[DataRequired(message="URL标识不能为空")],
        render_kw={"autocomplete": "off"},
    )
    priority = IntegerField("优先级", default=0)

    description = TextAreaField(
        "描述",
        filters=[lambda v: (v or "").strip() or None],
    )
    cover_url = StringField(
        "封面",
        filters=[lambda v: (v or "").strip() or None],
    )

    template = SelectField(
        "模板",
        validators=[Optional()],
        filters=[lambda v: v or None],
    )
    is_active = BooleanField("是否上线", default=True)
    submit = SubmitField("提交保存")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.template.choices = [("", "默认模板")] + [
            (item, item) for item, _ in get_templates("specials")
        ]


class TagForm(Form):
    name = StringField(
        "名称", validators=[DataRequired()], render_kw={"autocomplete": "off"}
    )
    slug = StringField(
        "标识",
        validators=[Optional()],
        description="留空将自动生成（中文转拼音，英文保留）",
        render_kw={"autocomplete": "off", "placeholder": "留空自动生成"},
    )
    submit = SubmitField("提交保存")


class FeatureForm(Form):
    name = StringField(
        "名称", validators=[DataRequired()], render_kw={"autocomplete": "off"}
    )
    slug = StringField(
        "标识",
        validators=[Optional()],
        description="留空将自动生成（中文转拼音，英文保留）",
        render_kw={"autocomplete": "off", "placeholder": "留空自动生成"},
    )
    is_active = BooleanField("启用", default=True)
    submit = SubmitField("提交保存")


class ContentIdsForm(Form):
    """关联/移除内容的 checkbox 表单: content_ids 多选 UUID + 回跳 url。

    只校验提交值, 不渲染 choices/不用 obj=, 故 coerce=uuid.UUID 安全:
    合法产出 list[UUID], 非法/空串走 form.validate() 字段错误, 不裸抛 500。
    """

    content_ids = SelectMultipleField(coerce=uuid.UUID, validate_choice=False)
    url = StringField(
        validators=[Optional()],
        filters=[lambda x: x if x else None],
    )


class CategoryDestroyForm(Form):
    name = StringField("栏目名称", render_kw={"disabled": ""})
    confirm = StringField(
        "删除确认",
        validators=[AnyOf(["我确认删除"], message='请输入"我确认删除"以确认操作')],
        render_kw={"placeholder": "我确认删除"},
    )
    submit = SubmitField("确认删除")

    def disabled(self):
        for field in self:
            field.render_kw = {"disabled": ""}


class TagDestroyForm(Form):
    name = StringField("标签名称", render_kw={"readonly": ""})
    confirm = StringField(
        "删除确认",
        validators=[AnyOf(["我确认删除"], message='请输入"我确认删除"以确认操作')],
        render_kw={"placeholder": "我确认删除"},
    )
    submit = SubmitField("确认删除")


class FeatureDestroyForm(Form):
    name = StringField("推荐名称", render_kw={"readonly": ""})
    confirm = StringField(
        "删除确认",
        validators=[AnyOf(["我确认删除"], message='请输入"我确认删除"以确认操作')],
        render_kw={"placeholder": "我确认删除"},
    )
    submit = SubmitField("确认删除")


class SpecialDestroyForm(Form):
    name = StringField("专题名称", render_kw={"readonly": ""})
    confirm = StringField(
        "删除确认",
        validators=[AnyOf(["我确认删除"], message='请输入"我确认删除"以确认操作')],
        render_kw={"placeholder": "我确认删除"},
    )
    submit = SubmitField("确认删除")
