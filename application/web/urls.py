from __future__ import annotations


TAG_SHOW = "/t/{slug:str}"
SPECIAL_SHOW = "/s/{slug:str}"


def build_tag_url(slug: str) -> str:
    return TAG_SHOW.replace(":str", "").format(slug=slug)


def build_special_url(slug: str) -> str:
    return SPECIAL_SHOW.replace(":str", "").format(slug=slug)
