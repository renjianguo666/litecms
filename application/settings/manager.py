"""系统设置 - TOML 文件存储

所有设置存在 storages/settings.toml，类型天然保留，零数据库依赖。
分为两部分:
- 注册字段: 各模块通过 SettingRegistry 声明,表单生成结构化字段
- 模板变量: 非注册 key,供模板通过 settings.xxx 使用
"""

from __future__ import annotations

import io
import tomllib
from typing import Any

import tomli_w
from litestar.contrib.jinja import JinjaTemplateEngine

from application.config import get_config
from application.settings.fields import SettingRegistry

SETTINGS_FILE = get_config().storage_dir / "settings.toml"
# settings.toml 的进程间文件锁(Linux/macOS)。save_settings 是
# read-modify-write,多 worker 并发会 lost update(后写覆盖先写)。
# tmp.replace 换 inode,直接锁 settings.toml 不保护新文件,故用独立 .lock。
# Windows 无 fcntl,开发期单进程无并发写,不加锁(行为与无锁时一致)。
try:
    import fcntl

    _HAVE_FLOCK = True
except ImportError:  # Windows
    fcntl = None  # 绑定占位, 避免 "possibly unbound"; 运行时由 _HAVE_FLOCK 守卫不访问
    _HAVE_FLOCK = False

# mtime 校验缓存：每次调用 stat() 对比文件修改时间，变了才重新读盘解析。
# 与 lru_cache 的进程级缓存不同——文件是各 worker 共享的事实源，任何进程
# 写入都会体现为 mtime 变化，跨 worker 数据天然一致（同 PHP opcache 的
# validate_timestamps 机制）。原子替换(tmp.replace) 换新 inode 后 mtime
# 必然不同，无需 watch inode。
_cached_settings: dict[str, Any] | None = None
_cached_mtime: int | None = None


def load_settings() -> dict[str, Any]:
    """读取所有设置，类型由 TOML 原生保留。

    结果缓存在内存中，每次调用一次 stat() 校验 mtime（~1-2μs），
    文件变了才重读。保存设置后无需任何刷新动作，下次调用自动拿到新值。
    """
    global _cached_settings, _cached_mtime
    try:
        mtime = SETTINGS_FILE.stat().st_mtime_ns
    except FileNotFoundError:
        return {}
    if _cached_settings is not None and mtime == _cached_mtime:
        return _cached_settings
    with open(SETTINGS_FILE, "rb") as f:
        _cached_settings = tomllib.load(f)
        _cached_mtime = mtime
    return _cached_settings


def save_settings(data: dict[str, Any], free_text: str | None = None) -> None:
    """保存设置到 TOML 文件: 加锁 → 读全量 → 合并模板变量 → 覆盖传入字段 → 原子写回。

    data 只传要改的字段, 未传字段原样保留, 不会丢配置。
    free_text 是模板变量区(非注册 key)的 TOML 文本, 来自设置表单的
    template_vars textarea: 传了则 textarea 是模板变量区的权威,
    文本中删掉的行会真正删除; 不传(None)则模板变量区原样保留。

    全程持排他文件锁, 串行化多 worker 的 read-modify-write, 杜绝 lost
    update(后写者覆盖先写者丢一整次保存)。锁内先丢弃本进程缓存的旧快照
    重读, 确保拿到他 worker 的最新值。Windows 无 fcntl, 走 no-op。
    """
    global _cached_settings
    # 独立 .lock 文件: tmp.replace 换 settings.toml 的 inode, 锁旧 fd
    # 不保护新文件; .lock 文件不被替换, inode 稳定, 锁贯穿整个写周期。
    # open 在 try 外: 失败时 lock_fd 不会被赋值, 无 fd 要关;
    # flock 移进 try: open 成功后任何异常(含 flock 信号中断)都走 finally 关 fd。
    lock_fd = open(SETTINGS_FILE.with_suffix(".lock"), "a+") if _HAVE_FLOCK else None
    try:
        if lock_fd is not None:
            assert fcntl is not None  # lock_fd 非 None ⟺ _HAVE_FLOCK ⟺ fcntl 已 import
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
        # 锁内丢缓存重读: 他 worker 可能刚写过, 本进程内存里是旧快照。
        _cached_settings = None
        merged = load_settings()
        if free_text is not None:
            try:
                free = tomllib.loads(free_text) if free_text.strip() else {}
            except tomllib.TOMLDecodeError:
                free = None  # 解析失败则不动模板变量区
            if free is not None:
                reg_keys = SettingRegistry.keys()
                for k in [k for k in merged if k not in reg_keys]:
                    del merged[k]
                merged.update(free)
        merged.update(data)
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = SETTINGS_FILE.with_suffix(".tmp")
        with open(tmp, "wb") as f:
            tomli_w.dump(merged, f, multiline_strings=True)
        tmp.replace(SETTINGS_FILE)
        # mtime 校验下无需刷新缓存：下次 load_settings 的 stat 会检测到 mtime 变化
    finally:
        if lock_fd is not None:
            assert fcntl is not None
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()


def get_free_text() -> str:
    """提取模板变量区(非注册 key)的 TOML 文本,供表单 textarea 使用。

    返回的是合法的 TOML 文本,只包含非注册字段。
    """
    settings = load_settings()
    reg_keys = SettingRegistry.keys()
    free = {k: v for k, v in settings.items() if k not in reg_keys}
    if not free:
        return ""
    buf = io.BytesIO()
    tomli_w.dump(free, buf, multiline_strings=True)
    return buf.getvalue().decode("utf-8")


def get_settings(key: str, default: Any = None) -> Any:
    """读取一个注册配置,自动带 registry 声明的默认值。

    优先级: settings.toml 值 > registry 默认值 > 传入 default
    每次调用都走 load_settings(),save_settings 后拿新值,实时。
    """
    settings = load_settings()
    if key in settings:
        return settings[key]
    for f in SettingRegistry.fields():
        if f.key == key:
            return f.default
    return default


class TemplateSettings:
    """注入 Jinja2 globals,模板里 {{ settings.site_name }} 实时读最新缓存"""

    def __getattr__(self, name: str) -> Any:
        return get_settings(name, "")


def register_template_callables(engine: JinjaTemplateEngine) -> None:
    engine.engine.globals["settings"] = TemplateSettings()

    # 前台模板全局标签 (category_select/article_select/... 帝国式) 是 async def,
    # 只注册到 web 前台专用异步引擎 (web/template.py 构建时挂载),
    # 本同步引擎 (admin 后台/错误页) 不挂载。
