from __future__ import annotations

from datetime import datetime

from wtforms import (
    DateTimeField,
    Form,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
    validators,
    widgets,
)

from application.config import cfg
from application.contents.enums import PublishStatus


class ArticleForm(Form):
    categories = SelectMultipleField("发布栏目", validators=[validators.data_required(message="栏目必须")])
    title = StringField(
        "标题",
        validators=[
            validators.DataRequired(message="标题不能为空"),
            validators.Length(max=255, message="标题不能超过 255 个字符"),
        ],
        filters=[lambda v: (v or "").strip()],
        render_kw={"autocomplete": "off"},
    )
    text = TextAreaField("内容", validators=[validators.DataRequired(message="内容不能为空")])
    description = TextAreaField(
        "描述",
        filters=[lambda v: (v or "").strip() or None],
    )
    cover_url = StringField(
        "封面",
        render_kw={"autocomplete": "off"},
        filters=[lambda v: (v or "").strip() or None],
        validators=[validators.Length(max=255, message="封面地址不能超过 255 个字符")],
    )
    source = StringField(
        "来源",
        filters=[lambda v: (v or "").strip() or None],
        validators=[validators.Length(max=200, message="来源不能超过 200 个字符")],
    )
    author = StringField(
        "作者",
        filters=[lambda v: (v or "").strip() or None],
        validators=[validators.Length(max=100, message="作者不能超过 100 个字符")],
    )
    features = SelectMultipleField("推荐位", option_widget=widgets.CheckboxInput())
    specials = SelectMultipleField("专题")
    tags = SelectMultipleField("标签", validate_choice=False)

    published_at = DateTimeField(
        "发布时间",
        validators=[validators.Optional()],
        default=lambda: datetime.now(cfg.tzinfo).replace(tzinfo=None, microsecond=0),
        render_kw={"autocomplete": "off"},
    )
    status = SelectField(
        "状态",
        choices=[
            (PublishStatus.DRAFT.value, "草稿"),
            (PublishStatus.PUBLISHED.value, "发布"),
            (PublishStatus.RETRACTED.value, "撤回"),
        ],
        default=PublishStatus.PUBLISHED.value,
    )
    submit = SubmitField("提交保存")


class ArticleEditForm(ArticleForm):
    category = SelectField(
        "发布栏目",
        validators=[
            validators.DataRequired(),
            validators.UUID(message="栏目ID必须是有效的UUID"),
        ],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fields.pop("categories", None)


class ArticleDestroyForm(Form):
    title = StringField("文章标题", render_kw={"readonly": ""})
    confirm = StringField(
        "删除确认",
        validators=[validators.AnyOf(["我确认删除"], message='请输入"我确认删除"以确认操作')],
        render_kw={"placeholder": "我确认删除"},
    )

    submit = SubmitField("确认删除")
