from pathlib import Path

from application.config import get_config

from .forms import SAFE_FILENAME_PATTERN

TEMPLATE_ROOT: Path = get_config().storage_dir / "templates"


def get_templates(kind: str) -> list[tuple[str, str | None]]:
    tpl_path = TEMPLATE_ROOT / kind
    result: list[tuple[str, str | None]] = []
    for tpl in tpl_path.rglob("*.html"):
        parts = tpl.relative_to(tpl_path).parts
        group = parts[0] if len(parts) > 1 else None
        result.append((tpl.name, group))
    return result


def get_template(kind: str, name: str) -> Path:
    if not SAFE_FILENAME_PATTERN.fullmatch(name):
        raise PermissionError("非法路径")

    target = (TEMPLATE_ROOT / kind / name).resolve()
    if not str(target).startswith(str(TEMPLATE_ROOT.resolve())):
        raise PermissionError("非法路径")
    if not target.parent.exists():
        raise FileNotFoundError("模板不存在")

    return target
