from enum import StrEnum


class PublishStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

    @property
    def label(self) -> str:
        labels = {
            "draft": "草稿",
            "published": "已发布",
            "archived": "已归档",
        }
        return labels[self.value]
