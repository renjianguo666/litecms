"""模板管理器"""

from __future__ import annotations

from pathlib import Path

from anyio import Path as AsyncPath
from litestar.exceptions import HTTPException, NotFoundException


class TemplateManager:
    """
    storage/templates 目录的模板文件管理器

    目录结构：
    - 根目录：页面模板（如 red.category.html）
    - common/：公共组件
    - macros/：宏模板
    """

    ALLOWED_EXTENSION = ".html"

    def __init__(self, root_dir: Path):
        self.root = root_dir.resolve()

    def _validate_filename(self, filename: str) -> None:
        """校验文件名"""
        if not filename.endswith(self.ALLOWED_EXTENSION):
            raise HTTPException(status_code=400, detail="文件必须以 .html 结尾")
        if ".." in filename:
            raise HTTPException(status_code=400, detail="非法的文件名")

    def _get_path(self, filename: str) -> AsyncPath:
        """获取文件完整路径"""
        self._validate_filename(filename)
        # 必须严格。去掉开头/，并转义反斜杠
        clean_name = filename.lstrip("/").replace("\\", "/")
        target = (self.root / clean_name).resolve()

        if not str(target).startswith(str(self.root)):
            raise HTTPException(status_code=400, detail="非法的文件路径")

        return AsyncPath(target)

    async def list(self, subdir: str | None = None) -> list[str]:
        """列出模板文件"""
        target = AsyncPath(self.root / subdir) if subdir else AsyncPath(self.root)
        if not await target.exists():
            return []

        result = []
        async for entry in target.rglob("*.html"):
            if await entry.is_file():
                rel = entry.relative_to(self.root)
                result.append(str(rel).replace("\\", "/"))

        return sorted(result)

    async def read(self, filename: str) -> str:
        """读取文件内容"""
        path = self._get_path(filename)
        if not await path.exists():
            raise NotFoundException(f"文件不存在: {filename}")
        return await path.read_text(encoding="utf-8")

    async def write(self, filename: str, content: str) -> None:
        """写入文件（创建或更新）"""
        path = self._get_path(filename)
        parent = path.parent
        if not await parent.exists():
            await parent.mkdir(parents=True, exist_ok=True)
        await path.write_text(content, encoding="utf-8")

    async def delete(self, filename: str) -> None:
        """删除文件"""
        path = self._get_path(filename)
        if not await path.exists():
            raise NotFoundException(f"文件不存在: {filename}")
        await path.unlink()

    async def rename(self, old: str, new: str) -> None:
        """重命名文件"""
        old_path = self._get_path(old)
        new_path = self._get_path(new)

        if not await old_path.exists():
            raise NotFoundException(f"文件不存在: {old}")
        if await new_path.exists():
            raise HTTPException(status_code=409, detail=f"目标文件已存在: {new}")

        parent = new_path.parent
        if not await parent.exists():
            await parent.mkdir(parents=True, exist_ok=True)

        await old_path.rename(new_path)
