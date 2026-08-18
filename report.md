# application/ 上线前复审报告(第二轮)

> 范围:`application/` 全模块(~7900 行)。8 路并行子代理逐文件深审。
> 目的:① 验证上一轮修复是否生效、有无回归;② 排查新问题。

## 总体结论

上一轮高危修复(开放重定向、越权提权、SSRF、style 注入)大部分生效。但复审发现:**3 项上一轮回归/遗漏**、**2 个新高危**(数据丢失 + RCE)、**1 个上线阻塞**(前台是调试桩)。能上生产的前提:修掉 🔴 并就「前台是否上线」做决策。

---

## 🔴 高危 / 阻塞(上线前必须处理)

### 1. web 前台是调试桩,不具备上线条件
- **文件**:`web/controllers.py`
- **问题**:`index`(line 29)返回固定字符串 `"index page"`;`resolve`(line 39)返回调试输出;`tag`(line 96)/`special`(line 133)引用**不存在的模板** `web/tag.html`、`web/special.html` → 访问即 500。
- **决策**:只上后台 → 在 `router.py` 注释掉 `WebController` 挂载;要上前台 → 补实现 + 模板。

### 2. ✅ 已修复 | 编辑带标签文章保存会静默丢失全部标签
- **文件**:`articles/templates/article_form.html.j2:21`
- **问题**:`data-tags="{{ selected_tags | tojson }}"` 双引号属性。`tojson` 不转义 JSON 内部的 `"`,属性被截断 → `JSON.parse` 抛错 → Alpine store 为空 → 提交空 tags → `resolve_tags([])` 清空已有关联。
- **影响**:编辑已有标签的文章 → 保存 → 标签全丢,无报错。
- **已修复**:`data-tags` 改单引号包裹,与同文件 `data-config` 行 39、`tags_dialog` 行 8 的 tojson 用法对齐。实测多标签/含引号标签名/空数组三种场景 `JSON.parse` 均正确还原。

### 3. ✅ 已修复 | 反射 XSS → SSTI → RCE
- **文件**:`themes/templates/themes.html.j2:41` + `themes/controllers.py:56-60`
- **问题**:`x-data="{ activeTarget: '{{ template_path }}' }"`,`template_path` 来自 `target` 查询参数(用户可控)。值在 Alpine JS 表达式上下文,浏览器先解码 HTML 实体再交给 Alpine 求值,Jinja autoescape 失效——payload `x';alert(1);y='` 的 `'` 被转成 `&#39;`,浏览器解码还原成 `'`,Alpine 求值 `'x';alert(1);y=''` 执行 alert。仅在 `kind=tags` 时可达:非 tags 分支走 `get_template` 校验拦截,tags 分支对非法 target 不拦直接渲染。借 XSS 调 `templates:write` 写恶意 Jinja2 模板 → SSTI → RCE。
- **已修复(两处):** ① 模板 `x-data` 改 `{{ template_path | default('', true) | tojson | forceescape }}`(与 `role_form.html.j2:10` 同一模式)——`tojson` 把引号转成 `'`/`"`(JS 字符串转义,不闭合),`forceescape` 转外层定界符。② controller tags 分支 target 不在 `TAG_FILES` 时 `htmx_error` 提前返回(与非 tags 的 `get_template` 校验对称)。实测 5 种 payload 全部被挡,正常文件名仍正常工作。

---

## 🟠 中危待修(上线前建议修)

### 4. ✅ 已修复 | 过期 session 清理是死代码
- **文件**:`security.py:128-133`
- **问题**:`state.get("sessions_last_cleared", now)` 在 key 不存在时返回 `now`,`now - now == 0` 条件恒 False;`sessions_last_cleared` 只在 if 体内写 → 永不执行 → `delete_expired()` 永不调用 → session 文件无限累积至磁盘满。
- **已修复(security.py):** `state.get` 不传 default(不存在返回 None),条件加 `last_cleared is None or`,首次立即清理并写入时间戳,之后每 1 天一次。模拟执行验证:旧写法清理 0 次,新写法首次执行、1 秒后不执行、1 天后执行。

### 5. ✅ 已修复 | 非超管可任意分配角色(垂直提权)
- **文件**:`accounts/controllers/user.py`(new/edit/create/update 四处)+ `forms.py`
- **问题**:上一轮只堵 `is_superuser`,漏了 `roles`。持 `user_update` 的非超管可在表单选任意角色给自己加全权 → 等同超管业务能力。`roles` 字段对所有有 `user_update`/`user_create` 权限的人无差别渲染。
- **已修复(user.py):** 角色分配收归超管(帝国式)——非超管四处 `del form.roles`:渲染时不渲染角色字段(用户看不到),提交时 `form.data` 不含 roles(攻击者手动 POST roles 也无效,保留目标原角色/创建无角色用户)。超管不受限。理由:非超管能分配角色 = 能制造比自己权限高的账号 = 提权路径,任何权限子集门槛都堵不严(全 `role_*` 权限的非超管仍可分配全权角色),故直接收归 `is_superuser`,与上一轮 #2「非超管不碰超管」同一套逻辑。create 路径补 `current_user` 注入。`is_superuser` 是普通 bool 列不依赖关系加载,无 lazy 风险。

### 6. ✅ 已修复 | PNG 解压炸弹内存放大
- **文件**:`media/processing.py`
- **问题**:PNG 无 `draft` 降采样,`img.thumbnail()` 内部 `img.load()` 全量解码。PIL 默认 `MAX_IMAGE_PIXELS≈89M`,以内允许分配 ~356MB。认证用户传外链(SSRF 只挡内网),并发数个即 OOM。
- **已修复(processing.py):** `img.size` 来自 PNG header(IHDR)读取不触发全量解码,在 `thumbnail()`(内部全量解码)之前按尺寸预判——任一边 >6000px 直接 `raise ValueError`(走 `process_image` 的 `except → ValidationException` 转 400)。6000px 解码 ≈144MB 单张可控,超过判定炸弹。实测 6 场景通过:正常小图/4000px 缩小转/7000px 拒绝/6000 边界放行/6001 拒绝/`process_image` 包装转 ValidationException。

### 7. ✅ 已修复 | 存储层异常未捕获,API 返回 HTML 500
- **文件**:`media/services.py` + `controllers.py:52`
- **问题**:`upload_image`/`download_image` 直接 `await get_storage().save(...)`,未包 try。OSS `put_object`/本地 `write_bytes` 抛原生异常 → 落全局 500 → 返回 HTML 给应返回 JSON 的接口。
- **已修复(services.py):** 两处 `save()` 包 `try/except → raise ValidationException("图片存储失败")`,走控制器已注册的 JSON handler,不回显内部细节。实测 OSError/ConnectionError 均转 ValidationException 不泄漏原生异常。

### 8. ✅ 已修复 | SEO 成功路径 decode("utf-8") 漏捕 UnicodeDecodeError
- **文件**:`seo/services.py:154`
- **问题**:`json.loads(resp.read().decode("utf-8"))` 的 except 只覆盖 `HTTPError` 与 `(TimeoutError, URLError, json.JSONDecodeError)`。`UnicodeDecodeError` 是 `ValueError` 子类但不属 `json.JSONDecodeError` → 穿透 500。对照错误路径 line 150 已用 `ValueError` 正确覆盖,唯独成功路径漏。
- **已修复(services.py):** line 154 元组加 `ValueError`(与 line 150 对齐)。`ValueError` 是 `UnicodeDecodeError` 和 `JSONDecodeError` 的共同父类,现在成功路径的非 UTF-8 响应走重试→`{"error":...}`,不再穿透 500。

### 9. ✅ 已修复 | Page.path 未过滤反斜杠(开放重定向)
- **文件**:`pages/forms.py` + `pages/services.py:26,35`
- **问题**:`normalize_path`(Litestar 工具)只压正斜杠 `//` 不处理反斜杠 `\`。`normalize_path('\\evil.com/x')` → `/\\evil.com/x`(反斜杠保留),满足 CheckConstraint `LIKE '/%'`。`pages.html.j2:10`「查看」`<a href="{{ row.path }}">` 渲染后浏览器把 `\` 当 `/` → 协议相对 `//evil.com/x` → 跳外站。
- **已修复(forms.py):** `path` 字段加 `Regexp` 白名单校验(Django slug 思路):`^/[a-zA-Z0-9_\-{}.]+(?:/[a-zA-Z0-9_\-{}.]+)*/?$|^/$`——只允许字母数字/下划线/连字符/点/路径分隔/占位符 `{}`,禁反斜杠(浏览器当 `/` 跳外站)、`?#`/`%`(URL 特殊语义)、`<>`空白(注入)、`//`(协议相对)。填错走 WTForms 字段错误(显式报错,不静默转换,与主流一致)。实测 11 场景通过。**categories 的 `path`/`content_path`(taxonomies/forms.py)同类问题顺手对齐**——两个字段加同一白名单正则,占位符 `{parent}/{key}` 正常放行,含 `\`/`?`/`//` 等被拒,实测 5 场景通过。

### 10. ✅ 已修复 | Category update 缺跨表 path 唯一校验
- **文件**:`taxonomies/services.py` + `taxonomies/controllers/categories.py`
- **问题**:create 调了 `check_path_unique`,update 在 path 重算后从不调用,只靠 DB 本表 unique(`Category.path unique=True` 挡同表撞,但跨表 Page/Content 无 DB 约束)。把栏目 path 改成与某 Page/Content 相同不报错 → 前台路由解析歧义。
- **已修复(services.py + controllers.py):** ① service update path 重算后加 `check_path_unique(session, updated.path, exclude_id=updated.id)`,与 create 对齐(排除自身 id)。② controller update 加 `except PathConflictError → form.append_field_error("path", ...)`,与 create 的错误展示一致。create/update 现在对称。

### 11. ✅ 已修复 | role_form 页面模式表单引号未闭合
- **文件**:`accounts/templates/role_form.html.j2:103`
- **问题**:page 分支 `hx-disabled-elt="[type=submit]` 缺闭合 `"`(dialog 分支 line 73 是闭合的)。`>` 落入未闭合属性值,隐藏 `url` 字段及部分字段被吞,表单结构损坏。
- **触发**:直链访问 `/admin/roles/new` 或 `/admin/roles/{id}/edit`(不带 `?dialog=true`)。
- **已修复(role_form.html.j2):** 补全引号 `hx-disabled-elt="[type=submit]"`,与 dialog 分支对齐。

### 12. ✅ 已修复 | SpecialForm.template 死字段(模型无列,提交值静默丢弃)
- **文件**:`taxonomies/models/specials.py` + 迁移
- **问题**:`SpecialForm` 暴露 `template` SelectField 并在模板渲染,但 `Special` 模型与表都无 `template` 列(对比 `Category.template` 有列)。advanced_alchemy `model_from_dict` 跳过非映射属性,用户选择永不落库。
- **已修复(specials.py + 迁移):** 给 `Special` 模型补 `template: Mapped[str | None] = mapped_column(String(100), comment="模板")`,与 `Category.template` 完全对齐。迁移 `2026-08-10_special_template_6f3a1b8c4d7e.py` 给 `taxonomies_specials` 表 `add_column`。表单字段 + 模板渲染保留不动。**需跑 `alembic upgrade head` 应用新列。**

### 13. ✅ 已修复 | settings save_settings flock 在 try 之外(fd 泄漏隐患)
- **文件**:`settings/manager.py:76-78`(本轮新加)
- **问题**:`flock(LOCK_EX)` 在 `try` 块之外,若抛异常(信号中断,极罕见)时 `lock_fd` 已 open 未进 try → `finally` 不执行 → fd 不关闭。
- **已修复(manager.py):** `flock` 移进 `try` 块。`open` 留在 try 外(失败时 `lock_fd` 不被赋值,无 fd 要关),`open` 成功后 `flock` 与业务逻辑都在 try 内,任何异常都走 `finally` 关 fd。

---

## 🟡 低危(择机处理)

### media
- ✅ 扩展名白名单加 `.jpeg`(`services.py:22`)。
- `services.py:106` 错误信息回显目标地址/状态码(脱敏,待定日志策略)。
- `ssrf.py:14-29` IPv6 `::/128` 未入黑名单(实际不可利用,`::` 连接通常失败)。
- ✅ OSS 客户端单例加 shutdown close 钩子(`storage.py` 新增 `close_storage()`,`create_app` 挂 `on_shutdown`;LocalStorage 无资源释放,OSS 才调 `client.close()`)。

### accounts
- `security.py:34-38` 登录未轮换 session ID(会话固定)。**已验证 Litestar 无 rotate/regenerate/cycle API**。`clear_session` 实测无法单请求内换 SID。现有 `samesite=strict` + `secure` 已把攻击面压至同子域/站内 XSS。**降级不修,待框架提供 API。**
- `auth.py:36` 登录时序差异可枚举用户名(限流方案待定,产品取向)。

### articles / pages
- `articles/forms.py:58` categories 不校验 UUID 格式/存在性(coerce=uuid.UUID 渲染路径崩,需 pre_validate+str,暂跳过)。
- `articles/forms.py` / `pages/forms.py` 多个 StringField 无 `Length(max=...)`(要逐个核对 DB 列长度,暂跳过)。
- `articles/controllers.py:247` tag_dialog 守卫用 create_permission(改 view_permission 需确认权限边界,暂跳过)。
- ✅ pages 列表排序方向改 DESC(与 articles 对齐,`pages/controllers.py:59`)。
- ✅ `articles.html.j2` / `pages.html.j2`「查看」加 `rel="noopener noreferrer"`。

### taxonomies
- ✅ 3 处「加载更多」search 加 `| urlencode`。
- `attach_contents` 不复验发布状态(业务决策,暂跳过)。
- `categories.py:164-180` destroy TOCTOU(DB 已防数据损坏,仅体验 500,暂跳过)。

### themes
- tags 读写绕过集中 `get_template` 校验(重构两套路径合一,改动大,当前白名单正确,暂跳过)。
- tags 列表恒返回 TAG_FILES(实为 tags 固定结构设计,文件不存在时点进去创建,非 bug,跳过)。
- `utils.py:25` `startswith` 前缀校验(当前不可利用,防御纵深,暂跳过)。
- ✅ `manager.py` 弃用死代码已删(无 import 引用)。

### seo
- ✅ `application/seo/backup/` 死代码目录已删(导入已断裂)。
- `hooks.py:57` sitemap 相对 URL(依赖 site_url 配置,非代码 bug)。

### web
- `controllers.py:84-93,121-130` 列表未过滤 `published_at <= now`(web 前台是调试桩 #1,等实现时一起处理)。
- `controllers.py:41-67` `_render_category` 死代码(同上,等 web 前台实现时处理)。

### core
- `config.py:82-83` OpenAPI 生产暴露(待确认 create_app 接受 None,暂跳过)。
- `checks.py` `check_path_unique` TOCTOU(业务层 catch,涉及多模块,暂跳过)。
- ✅ `security.py:57` `password_hash` 为 None 时容错(`if user.password_hash else ""`,防脏数据 500)。
- ✅ `mixins.py:124` page/page_size 负值兜底(`max(page,1)` / `max(page_size,1)`)。

### settings
- `manager.py:50-53` mtime 缓存粗粒度(生产 Linux 概率极低,加 generation 计数复杂,暂跳过)。

---

## ✅ 本轮已修复

| # | 问题 | 文件 | 修复 |
|---|---|---|---|
| J | 改密后合法用户被踢(pw_fp 回归) | `accounts/controllers/profile.py` | 改密成功后主动 `logout_action` + 整页跳 `/admin/login`,不再走被动踢出路径 |
| D | 静态文件目录 CWD 依赖(上轮 #11 遗漏) | `router.py:50,57` | `directories` 改 `str(BASE_DIR / "public/static")` 等,与 config.py 锚定方式对齐 |
| K | sanitizer 输出被 `<html><body>` 包裹 | `sanitizer.py:177` | `str(soup)` → `soup.body.decode_contents()`,7 场景实测通过 |

---

## 上一轮修复验证

| 上轮编号 | 结论 |
|---|---|
| #1 开放重定向(htmx.py) | ✅ 生效 |
| #2 越权提权(user.py is_superuser) | ✅ 生效,但 **#5 发现 roles 分配仍可提权** |
| #3 改密失效会话(pw_fp) | ⚠️ **有回归 → 本轮 #J 已修** |
| #4 style CSS 注入 | ✅ 生效 |
| #5 媒体下载三连 | ✅ 生效 |
| #6 sitemap_enabled | ✅ 生效 |
| #7 json.loads | ✅ 生效,但 **#9 发现成功路径漏 UnicodeDecodeError** |
| #8 0 成功误判 | ✅ 生效 |
| #9 Page.text sanitize | ✅ 生效,但 **#K 发现输出被外壳包裹 → 已修** |
| #10 page_size 上限 | ✅ 生效 |
| #11 CWD 依赖 | ⚠️ **有遗漏 → 本轮 #D 已修** |
| #12 空 SECRET_KEY | ✅ 生效 |
| #13 SEO 死代码+索引 | ✅ 生效 |
| #14 UUID 解析 | ✅ 生效 |
| #15 模板下拉固化 | ✅ 生效 |

---

## 各模块小结

| 模块 | 评价 |
|---|---|
| core/infra | 上轮安全修复生效;新发现 session 清理死代码(#4)、OpenAPI 暴露、sanitizer 外壳(已修) |
| accounts | 超管越权/自保护到位;角色提权(#5 已修)、改密回归(已修)、role_form 引号(#12);会话固定降级(框架无 API,现有防护兜底) |
| articles/contents | AA update 链路干净;**标签 tojson 丢数据(#2)**、path 不校验唯一(#10)、字段校验缺口 |
| pages | sanitize 已加但受外壳影响(已修);path 反斜杠重定向(#9 已修)、排序方向笔误 |
| media | SSRF/增量读扎实;解压炸弹(#7)、存储 500(#8)、`.jpeg` 缺失 |
| taxonomies | 上轮修复全生效;Category update path 缺口(#12)、SpecialForm 死字段(#14) |
| themes | 路径遍历防护到位;**x-data XSS→RCE(#3)**、tags 校验不对称、死代码 |
| dashboard | 无新问题 |
| seo | 上轮修复全生效;UnicodeDecodeError 漏捕(#9)、backup/ 死代码 |
| web | **整模块调试桩(#1 阻塞)**、模板缺失、published_at 未过滤 |
| settings | 锁/缓存/free_text 设计扎实;flock fd 泄漏小瑕疵(#15)、mtime 粗粒度边界 |

---

## 优先级

1. **上线阻塞**:#1(产品决策)+ #2 + #3。
2. **上线前建议修**:#4–#15 全部 🟠。
3. **择机处理**:🟡 全部。
