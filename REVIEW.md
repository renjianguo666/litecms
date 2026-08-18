# 生产上线前全项目审查报告

**日期**：2026-08-02
**项目**：litecms
**审阅范围**：全部 models、services、controllers、forms、config、security、middleware

---

## 🔴 CRITICAL — 阻塞上线

### 1. 前台 catch-all URL 解析是空壳

**文件**：`application/web/controllers.py:35-42`

```python
@get("{path:path}", name="web:resolve")
def resolve(self, path, db_session, page=1) -> str:
    return f"---------> {path} ==== {page}"
```

所有前台 URL（`/news/123`、`/about` 等）都返回这段调试字符串。`_render_category` 方法写好了但从未被调用。Page → Category → Content 按优先级匹配解析的逻辑完全没有实现。

**改法**：在 `resolve` 中实现三级匹配：先精确匹配 `Page.path` → 再前缀匹配 `Category.path` → 最后匹配 `Content.path`。NotFound 时返回 404。



---

### 6. `provide_services()` 无 session 分支写入静默丢失 ✅ 已修复

**文件**：`application/deps.py:67-75`

> 已在 `yield` 后显式 `db_session.commit()`。

---

### 7. 外链图片转存 SSRF ✅ 已修复

**文件**：`application/media/ssrf.py` + `application/media/services.py`

> 新增 `ssrf.py`：URL 协议校验 + DNS 解析 + 内网 IP 黑名单。
> `localize_remote` 改用手动重定向，每一跳都经过 SSRF 校验。

---

### 8. 媒体上传全部读入内存再检查大小 ✅ 已修复

**文件**：`application/media/services.py:57-59, 80-82`

> `upload_image`：移除自定义 `upload_max_size` 设置项和内存中的大小检查，上传大小限制改由 Litestar `request_max_body_size` 在框架层统一拦截。
> `localize_remote`：`max_size` 改用 `cfg.request_max_body_size`，与框架限制保持一致。

---

### 9. `build_permalink` 忽略传入的 `key`，URL 随机变 ✅ 已修复

**文件**：`application/permalink.py`

> 新 `permalink.py` 的 `{key}` 从 `model.id` 确定性派生（`uuid_to_base31`），更新文章 URL 不再变。
> 附带：`{num}` 默认与正数 `:N` 改取低位（后 8 位），同毫秒批量创建 1000 篇×3 轮零重复。

---

### 10. 栏目移动不更新子孙 content_path，无循环检测 ✅ 已修复

**文件**：`application/taxonomies/services.py` — `CategoryService.update`

> 已实现：
> - 循环检测（`_resolve_parent`）：移到自己或子孙 → 409，写入前拦截、零副作用
> - trail 级联：修复快照前缀 bug（history 与 updated 同一对象导致的 `REPLACE(新,新)` 空操作）+ `with_for_update` 并发行锁
> - path 语义：仅用户显式修改才重算，移动栏目不动 URL（产品决策，文章 URL 各管各）
> - 事务兜底：异常 rollback，路径冲突 IntegrityError → 409 友好提示
> - 修复移动/改 path 因 `lazy="raise"` 必 500 的问题
> 实测：5 层树 × 9 场景 × 30 断言全通过（含 DB 层一致性扫描）。

---

### 11. Tag find-or-create 竞态 → 500 ✅ 已修复

**文件**：`application/taxonomies/services.py` — `TagService.resolve_tags`（原 `get_or_create_many`）

> SAVEPOINT（`session.begin_nested()`）隔离每个 tag 的 insert：并发冲突只回退这一个 insert，
> 外层事务（文章保存）不受影响；冲突后重查并发插入的 tag。
> 实测：两个独立 session 并发创建同名 tag → 各自返回正确对象，DB 仅一条。

---

### 12. `retrieve_user_handler` 不预加载 roles/permissions ✅ 已修复

**文件**：`application/security.py:40-46`

> 已加 `load=[selectinload(User.roles).selectinload(Role.permissions)]`（`security.py:55-56`，`selectinload` 自 `sqlalchemy.orm` 导入），每请求一次性预加载 roles+permissions，消除 N+1。

```python
def retrieve_user_handler(session, connection):
    user = service.get_one_or_none(id=user_id)  # 没 preload
    return user if user and user.is_active else None
```

每次请求 `PermissionGuard` 调用 `user.has_permission(code)` → `User.roles`（lazy="selectin" ON）→ `Role.permissions`（lazy="selectin" ON）。每个请求至少 2-3 条额外 SQL。

**改法**：
```python
user = service.get_one_or_none(
    id=user_id,
    load=[selectinload(User.roles).selectinload(Role.permissions)]
)
```

---

## 🟡 MEDIUM — 上线后优先修复

### 13. 登出用 GET 请求，可被 CSRF 强制登出 ✅ 已修复

**文件**：`application/accounts/controllers/auth.py:49-52` + `application/dashboard/templates/base_header.html.j2`

> `@get("/logout")` 改为 `@post("/logout")`；模板退出节点改 `hx-post` + `hx-confirm`（HTMX 自动携带 CSRF token）。
> GET 攻击（`<img src>`）→ 405；跨站 POST → CSRF 403；正常用户 → hx-post 正常登出。

---

### 14. HTMX 非 HX 分支开放重定向 ✅ 已修复

**文件**：`application/htmx.py`

> `HXTriggerLocation`/`ClientRedirect`/`HXLocation` 三处非 HX 分支统一经 `_safe_relative_url()` 剥离 scheme/netloc，仅保留相对路径。

非 HX 请求的 `redirect` 直接用用户传入的 URL，不做 scheme/host 剥离。所有控制器传 `data.get("url")` 进 `htmx_success(redirect=...)`，攻击者可构造 `url=https://evil.com`。

**改法**：统一用 `urlparse` 剥离 scheme 和 netloc，只保留 path。

---

### 15. Session cookie 未设 `secure=True` ✅ 已修复

**文件**：`application/security.py`

> `secure=not cfg.debug`（生产 True / 开发 False），并加 `samesite="strict"`。

`ServerSideSessionConfig` 默认 `secure=False`。生产环境如果走 HTTPS（前面有 Nginx），Cookie 不会标 Secure 标志，可能被中间人截获。

**改法**：生产环境设置 `secure=True`、`samesite="strict"`。

---

### 16. 登录不轮换 session ID ✅ 已修复

**文件**：`application/security.py`

> `login_action` 重写 cookie 值为 `secrets.token_hex(32)`。已对照 Litestar 源码验证：中间件与 handler 共享 `ScopeState.cookies`（缓存在 `scope["state"]`），改动会传递到 `store_in_message` 用新 ID 存储并下发。

```python
def login_action(request, user):
    request.session[USER_SESSION_KEY] = str(user.id)
```

只设了 user key，没有 `session.regenerate()`。攻击者先诱导用户访问一个页面建立 session，用户登录后 session ID 不变 → session fixation。

**改法**：登录成功后调用 session ID 重新生成（Litestar `ServerSideSessionBackend` 的支持方式需确认）。

---

### 17. 登出只 clear 不删除服务端存储 ✅ 已修复

**文件**：`application/security.py`

> `logout_action` 置 `request.scope["session"] = Empty`，触发 `store_in_message` 的 `Empty` 分支 `delete(session_id)` 删除服务端条目并下发过期 cookie。

```python
def logout_action(request):
    request.session.clear()
```

`ServerSideSessionBackend` 的 session 文件留在 `storages/sessions/`，直到被定时清理任务删除。短期积累大量孤儿文件。

**改法**：登出时主动删除服务端 session 存储条目。

---

### 18. SQLite `BEGIN IMMEDIATE` 影响读并发  ⚠️ 经实测：串行化属实，所提改法均不可行

**文件**：`application/database.py:59-62`

```python
@event.listens_for(engine, "begin")
def _sqla_on_begin_sqlite(dbapi_connection):
    dbapi_connection.exec_driver_sql("BEGIN IMMEDIATE")
```

每个事务（包括纯读事务）都拿写锁。WAL 模式下读者本来不阻塞写者，现在全串行化了。

**改法**（原建议，均不可行）：只在写事务时用 `BEGIN IMMEDIATE`，或者去掉这个 listener 靠 WAL 的 `busy_timeout` 处理写冲突。

> **实测结论（2026-08-03，用真实 `create_sqlalchemy_engine` 压测）**：
> - **串行化属实（#18 判断对）**：`BEGIN IMMEDIATE` 对只读事务也生效，读也拿写锁。实测写者未提交 hold 1.2s 期间访客 `get` 阻塞 1236ms、两读并发 R2 阻塞 834ms。读挡写、读挡读，全串行。（注：WAL 本身读不挡，但本配置读也走 IMMEDIATE。）
> - **correctness 无问题**：两编辑并发，B 等 A 提交后读到新值再改，两次 +1 都生效（最终 v=2），不丢更新、不报 517。
> - **改法二证伪**：`busy_timeout` 只覆盖 `SQLITE_BUSY`，不覆盖 `SQLITE_BUSY_SNAPSHOT`(517，瞬时失败不重试)。去 listener 改 deferred 会让"先读后写"偶发 517 -> 500，且应用无重试兜底。
> - **改法一做不到**：`begin` 事件触发时不知是否写，需 app 层捕获 517 重试。
> - **结论**：correctness 层无需改（串行但不出错）。读并发要优化得 Postgres 或 deferred+517 重试，不是简单去 listener。

---

### 19. `sync_to_db` 破坏性删除权限 🟢 按约定不修

**文件**：`application/guards.py:77-82`

```python
for code, perm in existing.items():
    if code not in code_perms:
        session.delete(perm)  # ← 直接删除！
```

注释掉一个 `PermissionGuard(...)` 再跑 `permissions_db`，对应权限被删，所有角色-权限关联 CASCADE 消失。没有确认、没有 dry-run。

**改法**：加 `--dry-run` 和 `--force` 参数；生产环境默认只增不改不删。

> 🟢 决定不改。此命令定位为"安装时一次性 seed"：首次安装权限表为空，`sync_to_db` 走纯 INSERT，DELETE 分支无数据可删、不触发；生产装完不再跑，且不接入每次发版的自动部署。仅在"移除 `PermissionGuard(...)` 后又重跑"时才会 CASCADE 删授权--该场景由操作者知情、手动控制，属可接受的操作风险。

---

### 20. 软删除 Content 阻止删除用户 ✅ 已修复（去除软删除）

**文件**：`application/accounts/services.py:83-85`

```python
content_count = self.repository.session.scalar(
    select(exists().where(Content.creator_id == item_id))
)
```

用了 SQLAlchemy Core `select`，不受 ORM 全局 `with_loader_criteria(deleted_at IS NULL)` 过滤。用户的所有 Content 都软删了也删不掉用户。

**改法**：加 `Content.deleted_at.is_(None)` 过滤，或改用 ORM `select(Content).where(...)`。

> **去除软删除（2026-08-04）**：经设计决策，移除 Content 的软删除机制——`SoftDeleteModelMixin`/`SoftDeleteServiceMixin` + `database.py` 全局 `with_loader_criteria` 过滤器 + `deleted_at` 列。`ContentService.delete()`/`ArticleService.delete()` 回退为基类硬删除。`UserService.delete()` 的 `exists()` 检查不再被软删除过滤器绕过——#20 随之消失：检查现在正确统计所有内容（已无软删行），有内容则 409、无内容则放行。#34（`SoftDeleteServiceMixin.delete()` 依赖 identity-map）因整个 mixin 删除而消除。实测（内存 DB，反映去列后 schema）：硬删后行确消失；有内容用户 409、无内容用户删除成功。

---

### 21. `data.pop("categories")` 无默认值

**文件**：`application/articles/services.py:146`

```python
categories = CategoryRepository(...).get_many(
    CollectionFilter(field_name="id", values=data.pop("categories"))
)
```

如果 form 数据里没有 `"categories"` 键，直接 `KeyError` 500。

**改法**：`data.pop("categories", [])` 或 `data.get("categories", [])`。

---

### 22. 手动 commit + autocommit 双重提交 ✅ 已修复

**文件**：
- `application/database.py:71` — `before_send_handler="autocommit"`
- `application/articles/services.py:245` — `self.repository.session.commit()`
- `application/taxonomies/services.py:191` — `self.repository.session.commit()`

服务层手动 commit 后，请求结束时 autocommit 又 commit 一次。手动 commit 之后如果 controller 中后续代码抛异常，已经写进去的数据无法回滚。

**改法**：去掉服务层手动 commit，统一靠 autocommit。

**✅ 修复**：移除 `ArticleService.update` 与 `CategoryService.update` 的手动 `session.commit()` 及冗余的 `kwargs["auto_commit"]=False`（默认即 False，只 flush），统一由 `before_send_handler="autocommit"` 在响应时按状态码提交/回滚。

实测（真实 service + 真实模型 + 真实 autocommit handler 端到端，非替身模型）：正常更新（含 tags M2M 跨表）经 autocommit 正确落库；path 冲突抛异常经 `except Exception` 兜底回滚、无半成品落库；update 成功后若异常，autocommit 5xx 全回滚（恢复请求级原子性）。对照确认旧代码手动 commit 后异常拦不住已落库（即 #22 病根），移除后消除。

注：REVIEW 所述"双重提交"本身无害（第二次 commit 作用在空事务上为 no-op），真问题是手动 commit 提前固化破坏原子性。`CategoryService.update` 的 `except IntegrityError` 死代码已清理（它 import 自 `sqlalchemy.exc`，接不到 advanced_alchemy 抛出的 `DuplicateKeyError`，实测确认；`except Exception` 兜底保留，行为不变）。

---

### 23. 无效 TOML 静默丢弃 ❌ 误报

**文件**：`application/settings/manager.py:68-73`

```python
try:
    free = tomllib.loads(free_text)
except tomllib.TOMLDecodeError:
    free = {}
```

用户在模板变量 textarea 里写了错误格式的 TOML，保存后静默丢失，无任何提示。

**改法**：捕获后返回错误给前端显示。

**❌ 误报原因**：表单层已有内联校验器 `SettingFormBase.validate_template_vars`（`application/settings/forms.py:58-65`），在 `form.validate()` 阶段对 `template_vars` 执行 `tomllib.loads`，解析失败即 `raise StopValidation("TOML 语法错误: ...")`，错误挂到字段上，经 `render_field` → `render_errors` 在 textarea 下方红字显示、并给 textarea 加 `textarea-error` 红框。校验不通过时 `form.save()` 不会执行（`controllers.py:39-40`），故 `manager.py:68` 的 `tomllib.loads` 在 UI 路径下不可达，`except: free={}` 仅是单调用方已被门控的防御性兜底，不会触发。此外 WTForms 校验失败会用提交数据重新渲染表单，textarea 内容保留不丢失。综上不存在"静默丢失、无提示"的问题。

---

### 24. 遗留 `print()` 调试代码 ✅ 已修复

**文件**：`application/accounts/controllers/role.py:120`

```python
print(role.permissions)
```

**改法**：删掉。

---

### 25. `favicon` 返回字符串不是文件 ✅ 已修复

**文件**：`application/web/controllers.py:24-26`

```python
def favicon(self) -> str:
    return "favicon.ico"
```

浏览器收到明文 `"favicon.ico"`。要么用 `File` response，要么删掉让浏览器走 `/static/favicon.ico`。

---

### 26. Debug toolbar `enabled=True` 硬编码 ✅ 已修复

**文件**：`application/plugins.py:27`

```python
DebugToolbarPlugin(LitestarDebugToolbarConfig(enabled=True, ...))
```

虽然 `show_toolbar_callback` 只在 debug 模式显示，但插件本身仍消耗内存和 hook 开销。

**改法**：`enabled=cfg.debug`。

---

## 🟢 LOW — 后续迭代

| # | 文件 | 问题 | 改法 |
|---|------|------|------|
| 27 | `old_guards.py` | 死代码，无人 import | 删掉 |
| 28 | `checks.py:26` | `check_path_unique` TOCTOU 竞态 | catch IntegrityError 映射为 PathConflictError |
| 29 | `accounts/controllers/role.py:99` | ~~permissions choices 未用 str()~~ 已改用 `coerce=UUID` 彻底解决 | ✅ 已处理 |
| 30 | `security.py:63` | `FileStore(Path("storages/sessions"))` 相对路径 | 改为 `cfg.storage_dir / "sessions"` |
| 31 | `config.py:48` | `oss_cdn_url` 默认 `/static/uploads`，路由是 `/uploads` | 统一为 `/uploads` |
| 32 | `config.py:82` | OpenAPI 生产环境也暴露 | `enabled=cfg.debug` |
| 33 | `media/services.py:42` | `image/svg+xml` 在允许列表中，SVG 可嵌入 XSS | 移除 SVG 或做 sanitize |
| 34 | `mixins.py:166` | ~~SoftDelete `delete()` 依赖 identity-map 行为~~ 已随软删除移除消除 | ✅ 已修复（去除软删除） |
| 35 | `models.py` 各文件 | `lazy="joined"` 和 `lazy="selectin"` 作为默认策略 | 改为 `lazy="raise"`，查询处按需加载 |
| 36 | `articles/services.py:158` | 描述/封面为空时自动提取，用户无法主动清空 | 增加判断用户是否提交了该字段 |
| 37 | `dashboard/controllers.py:69` | 最近文章不 preload 关系 | 加 load options |
| 38 | `web/controllers.py:87` | tag/special 页 N+1 查询 | `select()` 加 `.options(selectinload(...))` |

---

## 汇总

| 严重度 | 数量 | 关键主题 |
|--------|------|---------|
| 🔴 CRITICAL | 1 | 前台 catch-all 解析空壳 |
| 🟠 HIGH | 12 | 模板文件写入→RCE、XSS、SSRF、DoS、CSRF、信息泄漏、数据丢失、URL 随机变、栏目移动损坏、Tag 竞态、权限懒加载 |
| 🟡 MEDIUM | 14 | 登出 CSRF、开放重定向、session 安全、事务管理、权限同步、软删、调试代码 |
| 🟢 LOW | 12 | 路径安全、配置完善、模型优化、代码规范 |
| **合计** | **39** | 已修复：#6 #7 #8 #9 #10 #11 #12 #20 #22 #24 #25 #26 #34（本次：#20 #34 经“去除软删除”一并消除）；按约定不修：#19；经实测不修：#18；误报：#23 |

**建议处理顺序**：CRITICAL → HIGH #2-4（安全类优先）→ HIGH #5-8（基础设施）→ HIGH #9-12（业务正确性）→ MEDIUM → LOW
