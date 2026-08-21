from __future__ import annotations

import re

from wtforms import Form
from wtforms.fields import HiddenField, StringField, SubmitField, TextAreaField
from wtforms.validators import any_of, data_required, regexp

SAFE_FILENAME_PATTERN = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_/]*\.html$")

NAME_PATTERN = re.compile(r"[a-zA-Z0-9]+")
# index 为固定单文件(不可命名), 不参与创建
CREATABLE_KINDS = ("categories", "specials", "pages", "commons")


class CreateTemplateForm(Form):
    kind = HiddenField(
        "模板类型",
        validators=[
            data_required(message="模板类型不能为空"),
            any_of(
                CREATABLE_KINDS,
                message=f"无效的模板类型，可选: {', '.join(CREATABLE_KINDS)}",
            ),
        ],
        render_kw={"autocomplete": "off"},
    )
    name = StringField(
        "模板名称",
        filters=[lambda x: x.strip().lower() if x else x],
        validators=[
            data_required(message="模板名称不能为空"),
            regexp(NAME_PATTERN, message="模板名称只能是英文字母和数字的组合"),
        ],
        render_kw={"autocomplete": "off"},
    )
    submit = SubmitField("提交保存")


class TemplateWriteForm(Form):
    kind = HiddenField(
        "模板类型",
        validators=[
            data_required(message="模板类型不能为空"),
            any_of(
                ("categories", "specials", "pages", "tags", "index", "commons"),
                message="无效的模板类型",
            ),
        ],
    )
    name = HiddenField(
        "模板名称",
        validators=[
            data_required(message="模板名称不能为空"),
            regexp(SAFE_FILENAME_PATTERN, message="非法的文件路径"),
        ],
    )
    content = TextAreaField(
        "模板内容",
        validators=[data_required(message="模板内容不能为空")],
    )
