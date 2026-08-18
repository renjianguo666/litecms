from __future__ import annotations

from enum import StrEnum


class PublishStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    RETRACTED = "retracted"

    @property
    def label(self) -> str:
        labels = {
            "draft": "草稿",
            "published": "已发布",
            "retracted": "已撤回",
        }
        return labels[self.value]
