# LiteCMS 前台模板制作文档

本文档面向安装 LiteCMS 后想自定义前台模板的开发者。涵盖：模板文件放哪、每个页面对应哪个模板、可用变量、模板标签（查询函数）的用法和参数。

---

## 目录

1. [模板目录与查找顺序](#1-模板目录与查找顺序)
2. [模板引擎](#2-模板引擎)
3. [全局变量](#3-全局变量)
4. [模板标签（查询函数）](#4-模板标签查询函数)
5. [页面与模板对应关系](#5-页面与模板对应关系)
6. [各页面可用变量详解](#6-各页面可用变量详解)
7. [数据结构（Schema 字段）](#7-数据结构schema-字段)
8. [分页器](#8-分页器)
9. [主题包（自定义模板）](#9-主题包自定义模板)
10. [完整示例](#10-完整示例)

---

## 1. 模板目录与查找顺序

LiteCMS 配置了多个模板目录，Jinja2 按以下顺序查找（先找到的优先）：

| 顺序 | 目录 | 用途 |
|------|------|------|
| 1 | `application/templates/` | 系统级模板 |
| 2 | `application/accounts/templates/` | 账户模块 |
| 3 | `application/articles/templates/` | 文章管理 |
| 4 | `application/dashboard/templates/` | 后台仪表盘 |
| 5 | `application/pages/templates/` | 单页管理 |
| 6 | `application/settings/templates/` | 设置页 |
| 7 | `application/taxonomies/templates/` | 栏目/标签/专题管理 |
| 8 | `application/themes/templates/` | **主题包模板（推荐自定义位置）** |
| 9 | `application/seo/templates/` | SEO 模板 |
| 10 | `application/web/templates/` | **前台内置模板** |
| 11 | `storages/templates/` | **运行时模板（后台动态上传的主题包）** |

**自定义模板推荐放在** `application/themes/templates/` 或 `storages/templates/` 下。同名的模板会覆盖内置的（因为排在 `web/templates/` 前面）。

---

## 2. 模板引擎

- 引擎：**Jinja2**（通过 Litestar 的 `JinjaTemplateEngine`）
- 文件后缀：`.html`（前台内置模板用 `.html`，后台用 `.html.j2`）
- 继承：支持 `{% extends %}` / `{% block %}` / `{% include %}`
- 自动转义：开启（HTML 安全）

所有前台模板继承自 `web_base.html`：

```jinja
{% extends "web_base.html" %}

{% block title %}自定义标题{% endblock %}

{% block content %}
  <!-- 页面内容 -->
{% endblock %}
```

`web_base.html` 定义了 `head` / `content` / `scripts` 三个可覆盖 block，以及完整的页面骨架（header 导航 + main + footer）。

---

## 3. 全局变量

所有模板都能直接用以下变量（无需传参，框架自动注入）：

| 变量 | 类型 | 说明 |
|------|------|------|
| `request` | Request | 当前请求对象，`request.url` 获取当前 URL，`request.url.path` 获取路径 |
| `csrf_input` | str | CSRF 隐藏表单字段，`{{ csrf_input }}` 直接放入 `<form>` |
| `settings` | TemplateSettings | 站点设置对象，`{{ settings.site_name }}` 等，实时读 settings.toml |

### settings 可用字段

`settings.xxx` 读取 `storages/settings.toml` 中的配置，实时生效（修改后无需重启）：

| 字段 | 示例 | 说明 |
|------|------|------|
| `settings.site_name` | 号外网 | 站点名称 |
| `settings.site_title` | | SEO 标题 |
| `settings.site_description` | | 站点描述 |
| `settings.site_url` | http://127.0.0.1:8000 | 站点完整地址 |
| `settings.sitemap_enabled` | true | 是否启用 sitemap |

> settings.toml 中任何非注册字段都能通过 `settings.xxx` 访问（模板变量区）。

---

## 4. 模板标签（查询函数）

模板标签是注册到 Jinja2 全局的可调用函数，在模板里直接调用查数据。类似帝国 CMS 的模板标签。

### categories_tree()

获取全站栏目导航树（含 children 嵌套）。

```jinja
{% for c in categories_tree() %}
  <a href="{{ c.url }}">{{ c.name }}</a>
  {% if c.children %}
    <ul>
      {% for child in c.children %}
        <li><a href="{{ child.url }}">{{ child.name }}</a></li>
      {% endfor %}
    </ul>
  {% endif %}
{% endfor %}
```

- **走 mtime 文件缓存**：首次查库，后续命中内存，后台改栏目即时刷新
- **返回**：`list[dict]`，每个节点含 `id` / `name` / `url` / `parent_id` / `children`（递归）
- **参数**：无
- **用途**：导航菜单、页脚栏目入口

### categories()

获取全站栏目扁平列表（按 trail 升序，即树的先序遍历，不含嵌套）。

```jinja
{% for c in categories() %}
  <a href="{{ c.url }}">{{ c.name }}</a>
{% endfor %}
```

- **走缓存**
- **返回**：`list[CategoryNavSchema]`，字段：`id` / `name` / `url` / `parent_id`
- **用途**：扁平列表展示、面包屑

### category_select(*ids)

按 id 取指定栏目；不传 id 返回全部。

```jinja
{# 取指定栏目 #}
{% set featured_cats = category_select(cat_id_1, cat_id_2) %}
{% for c in featured_cats %}
  <a href="{{ c.url }}">{{ c.name }}</a>
{% endfor %}

{# 取全部 #}
{% for c in category_select() %}
  ...
{% endfor %}
```

- **走缓存**（内存过滤，不查库）
- **参数**：`*ids` — UUID 列表，可变参数
- **返回**：`list[CategoryLiteSchema]`，字段见[数据结构](#7-数据结构schema-字段)

### build_tree(categories)

把扁平栏目列表构建为导航树（dict 嵌套 children）。配合 `category_select` 实现灵活建树。

```jinja
{# 筛选指定栏目后建树 #}
{% set tree = build_tree(category_select(cat_id_1, cat_id_2)) %}
{% for c in tree %}
  <a href="{{ c.url }}">{{ c.name }}</a>
  {% for child in c.children %}
    <a href="{{ child.url }}">{{ child.name }}</a>
  {% endfor %}
{% endfor %}
```

- **参数**：`categories` — 扁平栏目列表（`category_select()` 或 `categories()` 的返回值）
- **返回**：`list[dict]`，树节点含 `children`（递归嵌套）
- **用途**：自定义栏目子集的导航树

### tag_select(...)

查询标签列表（参数化）。

```jinja
{# 取全部标签 (默认按创建时间倒序) #}
{% for t in tag_select() %}
  <a href="/t/{{ t.slug }}">{{ t.name }}</a>
{% endfor %}

{# 取前 20 个 #}
{% for t in tag_select(limit=20) %} ... {% endfor %}

{# 按名称排序 #}
{% for t in tag_select(order_by="name", order_dir="asc") %} ... {% endfor %}
```

**参数：**

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `limit` | `int` / `None` | `None` | 取条数，`None`=全部 |
| `order_by` | `str` | `"created_at"` | 排序字段（`created_at` / `name`） |
| `order_dir` | `"desc"` / `"asc"` | `"desc"` | 排序方向（desc=新建在前） |

- **直接查库**（数据量小，不缓存）
- **返回**：`list[TagSchema]`，字段见[数据结构](#7-数据结构schema-字段)
- **用途**：标签云

### special_select(...)

查询专题列表（参数化）。

```jinja
{# 取启用的专题 (默认按优先级降序) #}
{% for s in special_select() %}
  <a href="{{ s.url }}">{{ s.title or s.name }}</a>
{% endfor %}

{# 取前 5 个启用的专题 #}
{% for s in special_select(limit=5) %} ... {% endfor %}

{# 取全部含未启用 #}
{% for s in special_select(active_only=false) %} ... {% endfor %}
```

**参数：**

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `active_only` | `bool` | `True` | `true` 只取启用的（is_active=True） |
| `limit` | `int` / `None` | `None` | 取条数，`None`=全部 |
| `order_by` | `str` | `"priority"` | 排序字段（`priority` / `created_at`） |
| `order_dir` | `"desc"` / `"asc"` | `"desc"` | 排序方向（desc=优先级高在前） |

- **直接查库**
- **返回**：`list[SpecialSchema]`，字段见[数据结构](#7-数据结构schema-字段)

### article_select(...)

**核心标签**。查询已发布文章列表，参数丰富。

```jinja
{# 取最新 10 篇 #}
{% for a in article_select(limit=10) %}
  <a href="{{ a.url }}">{{ a.title }}</a>
{% endfor %}

{# 取某栏目 5 篇有封面的 #}
{% for a in article_select(category=some_category_id, limit=5, cover=true) %}
  <a href="{{ a.url }}">
    <img src="{{ a.cover_url }}">
    {{ a.title }}
  </a>
{% endfor %}

{# 取头条推荐位的文章 #}
{% set featured = article_select(feature="headline", cover=true, limit=6) %}

{# 按浏览量排序取热门 #}
{% for a in article_select(limit=10, order_by="views") %}
  {{ a.title }} - {{ a.views }} 次浏览
{% endfor %}

{# 取多个栏目的文章 #}
{% for a in article_select(category=[cat_id_1, cat_id_2], limit=10) %}
  ...
{% endfor %}
```

**参数：**

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `category` | `UUID` / `list[UUID]` / `None` | `None` | 按栏目 id 过滤，支持单个或列表 |
| `special` | `str` / `list[str]` / `None` | `None` | 按专题 slug 过滤 |
| `feature` | `str` / `list[str]` / `None` | `None` | 按推荐位 slug 过滤 |
| `limit` | `int` | `10` | 取条数 |
| `cover` | `bool` | `False` | `true` 时只取有封面的 |
| `order_by` | `str` | `"published_at"` | 排序字段（`published_at` / `views`） |
| `order_dir` | `"desc"` / `"asc"` | `"desc"` | 排序方向 |

- **直接查库**（参数化查询，不缓存）
- **返回**：`list[ArticleLiteSchema]`，字段见[数据结构](#7-数据结构schema-字段)
- **注意**：每篇文章带 `category`（所属栏目）和 `creator`（作者）嵌套对象

### wechat_share(...)

渲染微信 JS-SDK 分享 JS。

```jinja
{{ wechat_share(title=article.title, desc=article.description, img=article.cover_url) | safe }}
```

- **参数**：`title` / `desc` / `link` / `img` / `*api_list`
- **返回**：`str`（JS 代码，需 `| safe` 直出）
- 未配置微信凭据时返回空串

---

## 5. 页面与模板对应关系

每个 URL 路由对应一个模板。控制器根据数据状态选择模板（内置 or 主题包）。

| 页面 | URL | 内置模板 | 主题包模板 | 选择条件 |
|------|-----|----------|------------|----------|
| 首页 | `/` | `web_index.html` | — | 固定 |
| 栏目页（目录型） | `/news` 等 | `web_category_index.html` | `categories/{template}/index.html` | 栏目有子栏目 |
| 栏目页（列表型） | `/news/politics` 等 | `web_category.html` | `categories/{template}/list.html` | 栏目无子栏目 |
| 文章详情 | `/news/xxx` | `web_article.html` | `categories/{template}/article.html` | 跟随所属栏目的 template |
| 单页 | `/about` | `web_page.html` | `pages/{template}` | 单页 template 字段有值 |
| 标签聚合 | `/t/{slug}` | `web_tag.html` | — | 固定 |
| 专题聚合 | `/s/{slug}` | `web_special.html` | `specials/{template}` | 专题 template 字段有值 |
| 404 | 任意未匹配 | `web_404.html` | — | 固定 |
| 基础骨架 | — | `web_base.html` | — | 所有页面继承 |

**URL 解析链**（catch-all `{path:path}`）：访问任意路径时，控制器按 `栏目 → 单页 → 文章 → 404` 顺序尝试匹配，第一个命中的渲染对应模板。

---

## 6. 各页面可用变量详解

### 首页 `web_index.html`

控制器不传私有变量，全部数据通过模板标签按需获取：

```jinja
{% extends "web_base.html" %}

{% block content %}
  {# 头条推荐 #}
  {% set featured = article_select(feature="headline", cover=true, limit=6) %}

  {# 最新资讯 #}
  {% for a in article_select(limit=10) %} ... {% endfor %}

  {# 热门阅读 #}
  {% for a in article_select(limit=10, order_by="views") %} ... {% endfor %}

  {# 专题推荐 #}
  {% for s in special_select() %} ... {% endfor %}

  {# 标签云 #}
  {% for t in tag_select() %} ... {% endfor %}
{% endblock %}
```

### 栏目页 `web_category.html` / `web_category_index.html`

| 变量 | 类型 | 说明 |
|------|------|------|
| `category` | CategorySchema | 当前栏目对象，含 `children`（子栏目列表） |
| `breadcrumbs` | list[CategoryLiteSchema] | 面包屑（栏目祖先链，按层级升序） |
| `pagination` | Pagination | 文章分页对象（含 items、分页信息） |

**index 和 list 的区别**：
- `web_category_index.html`（目录型，有子栏目）：查询范围 = 当前栏目 + 所有后代栏目的文章；顶部多一个子栏目入口条
- `web_category.html`（列表型，无子栏目）：查询范围 = 仅当前栏目的文章

两者结构统一，都是「头部 + 面包屑 + 分页文章列表 + 侧栏」。index 模板可直接当 list 用。

```jinja
{# 面包屑 #}
<nav>
  <a href="/">首页</a>
  {% for b in breadcrumbs %}
    <span>›</span>
    <a href="{{ b.url }}">{{ b.name }}</a>
  {% endfor %}
</nav>

{# 栏目标题 #}
<h1>{{ category.title or category.name }}</h1>

{# 子栏目入口 (index 独有) #}
{% for c in category.children %}
  <a href="{{ c.url }}">{{ c.title or c.name }}</a>
{% endfor %}

{# 文章分页列表 #}
{% for a in pagination %}
  <a href="{{ a.url }}">{{ a.title }}</a>
  <span>[{{ a.category.name }}]</span>
  <span>{{ a.published_at }}</span>
{% else %}
  暂无文章
{% endfor %}

{# 分页器 #}
{% include "web_pagination.html" with context %}
```

### 文章详情 `web_article.html`

| 变量 | 类型 | 说明 |
|------|------|------|
| `article` | ArticleSchema | 文章对象，含正文、标签、专题、推荐位 |
| `breadcrumbs` | list[CategoryLiteSchema] | 面包屑 |

```jinja
<h1>{{ article.title }}</h1>
<p>{{ article.published_at }} · {{ article.creator.username }}</p>
<div>{{ article.text | safe }}</div>

{# 标签 #}
{% for t in article.tags %}
  <a href="/t/{{ t.slug }}">{{ t.name }}</a>
{% endfor %}

{# 所属栏目 #}
<a href="{{ article.category.url }}">{{ article.category.name }}</a>
```

### 单页 `web_page.html`

| 变量 | 类型 | 说明 |
|------|------|------|
| `page` | PageSchema | 单页对象 |

```jinja
<h1>{{ page.title }}</h1>
<div>{{ page.text | safe }}</div>
```

### 标签聚合页 `web_tag.html`

| 变量 | 类型 | 说明 |
|------|------|------|
| `tag` | TagSchema | 当前标签对象 |
| `pagination` | Pagination | 该标签下的文章分页 |

### 专题聚合页 `web_special.html`

| 变量 | 类型 | 说明 |
|------|------|------|
| `special` | SpecialSchema | 当前专题对象 |
| `pagination` | Pagination | 该专题下的文章分页 |

---

## 7. 数据结构（Schema 字段）

### CategoryLiteSchema（栏目轻量）

```
id: UUID
name: str              # 栏目名称
title: str | None      # 栏目标题 (SEO 用, 无则用 name)
description: str | None
cover_url: str | None
url: str               # 栏目链接
page_size: int         # 每页文章数
parent_id: UUID | None # 父栏目 id (建树用)
```

### CategorySchema（栏目详情，栏目页用）

继承 CategoryLiteSchema，额外：

```
path: str              # 栏目路径, 如 /news
content_path: str      # 内容链接格式
template: str | None   # 主题包模板名
children: list[CategoryLiteSchema]  # 子栏目 (仅 index 页填充)
```

### CategoryNavSchema（导航节点，categories() 返回）

```
id: UUID
name: str
url: str
parent_id: UUID | None
```

### categories_tree() 返回（树节点 dict）

```
id: UUID
name: str
url: str
parent_id: UUID | None
title: str | None
description: str | None
cover_url: str | None
page_size: int
children: list[dict]   # 递归嵌套
```

### ArticleLiteSchema（文章列表项）

```
id: UUID
title: str
url: str               # 文章链接
description: str | None
cover_url: str | None
source: str | None     # 来源
author: str | None     # 作者
views: int             # 浏览量
published_at: datetime # 发布时间 (已格式化)
category: CategoryLiteSchema  # 所属栏目 (嵌套)
creator: UserSchema           # 创建者 (嵌套)
```

### ArticleSchema（文章详情，额外字段）

继承 ArticleLiteSchema，额外：

```
text: str                      # 正文 HTML
tags: list[TagSchema]          # 标签
specials: list[SpecialSchema]  # 所属专题
features: list[FeatureSchema]  # 所属推荐位
```

### TagSchema（标签）

```
id: UUID
name: str
slug: str              # 英文标识, URL 用
url: str               # /t/{slug}
```

### SpecialSchema（专题）

```
id: UUID
name: str
title: str
description: str | None
slug: str
cover_url: str | None
url: str               # /s/{slug}
template: str | None
```

### FeatureSchema（推荐位）

```
id: UUID
name: str
slug: str              # 英文标识, article_select(feature=slug) 用
```

### UserSchema（作者）

```
id: UUID
username: str
```

### PageSchema（单页）

```
id: UUID
title: str
path: str
url: str
description: str | None
cover_url: str | None
text: str              # 正文 HTML
template: str | None
```

---

## 8. 分页器

`web_pagination.html` 是内置分页器组件，栏目页/标签页/专题页直接 include：

```jinja
{% include "web_pagination.html" with context %}
```

`pagination` 对象可用属性：

| 属性 | 类型 | 说明 |
|------|------|------|
| `pagination` (迭代) | list[ArticleLiteSchema] | 当前页文章列表 |
| `pagination.page` | int | 当前页码 |
| `pagination.pages` | int | 总页数 |
| `pagination.has_prev` | bool | 是否有上一页 |
| `pagination.has_next` | bool | 是否有下一页 |
| `pagination.prev_num` | int | 上一页页码 |
| `pagination.next_num` | int | 下一页页码 |
| `pagination.iter_pages()` | generator | 页码迭代器（含 None 表示省略号） |
| `pagination.total` | int | 总记录数 |

分页通过 URL 参数 `?page=N` 控制。

---

## 9. 主题包（自定义模板）

### 覆盖内置模板

在 `application/themes/templates/` 或 `storages/templates/` 下创建同名文件即可覆盖内置模板。例如：

```
application/themes/templates/
├── web_base.html          # 覆盖基础骨架
├── web_index.html         # 覆盖首页
├── web_article.html       # 覆盖文章详情
└── web_category.html      # 覆盖栏目列表页
```

### 栏目主题包

在后台栏目设置中填写 `template` 字段（模板名），控制器会按以下规则查找：

| 页面 | 模板路径 | 示例 |
|------|----------|------|
| 目录型栏目 | `categories/{template}/index.html` | `categories/news_theme/index.html` |
| 列表型栏目 | `categories/{template}/list.html` | `categories/news_theme/list.html` |
| 文章详情 | `categories/{template}/article.html` | `categories/news_theme/article.html` |

> 文章详情的模板**跟随所属栏目**的 template 字段。即栏目 A 设了 `template="news_theme"`，栏目 A 下的文章都用 `categories/news_theme/article.html`。

创建栏目主题包：

```
application/themes/templates/categories/news_theme/
├── index.html      # 目录型栏目页
├── list.html       # 列表型栏目页
└── article.html    # 文章详情页
```

### 单页主题包

单页的 `template` 字段有值时，走 `pages/{template}`：

```
application/themes/templates/pages/about.html
```

### 专题主题包

专题的 `template` 字段有值时，走 `specials/{template}`：

```
application/themes/templates/specials/tech_weekly.html
```

---

## 10. 完整示例

### 自定义首页

```jinja
{% extends "web_base.html" %}

{% block content %}
  <div class="space-y-10">
    {# 焦点头条: 头条推荐位 + 有封面, 大图 + 右侧列表 #}
    {% set featured = article_select(feature="headline", cover=true, limit=6) %}
    {% if featured %}
      <section class="grid grid-cols-1 md:grid-cols-12 gap-4">
        {# 大图头条 #}
        {% set head = featured[0] %}
        <a href="{{ head.url }}" class="md:col-span-8 aspect-video relative">
          <img src="{{ head.cover_url }}" class="w-full h-full object-cover">
          <div class="absolute bottom-0 p-6 text-white">
            <h2>{{ head.title }}</h2>
          </div>
        </a>
        {# 右侧列表 #}
        <div class="md:col-span-4">
          {% for a in featured[1:] %}
            <a href="{{ a.url }}">{{ a.title }}</a>
          {% endfor %}
        </div>
      </section>
    {% endif %}

    {# 最新资讯 + 侧栏 #}
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <section class="lg:col-span-3">
        <h2>最新资讯</h2>
        {% for a in article_select(limit=10) %}
          <article>
            <a href="{{ a.url }}">{{ a.title }}</a>
            <span>{{ a.published_at }} · {{ a.creator.username }}</span>
          </article>
        {% endfor %}
      </section>

      <aside>
        {# 热门阅读 #}
        <h3>热门阅读</h3>
        {% for a in article_select(limit=10, order_by="views") %}
          <a href="{{ a.url }}">{{ a.title }}</a>
        {% endfor %}

        {# 标签云 #}
        <h3>标签</h3>
        {% for t in tag_select() %}
          <a href="/t/{{ t.slug }}">{{ t.name }}</a>
        {% endfor %}
      </aside>
    </div>
  </div>
{% endblock %}
```

### 自定义栏目列表页

```jinja
{% extends "web_base.html" %}

{% block title %}{{ category.name }} - {{ settings.site_name }}{% endblock %}

{% block content %}
  <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
    <div class="lg:col-span-3">
      {# 面包屑 #}
      <nav>
        <a href="/">首页</a>
        {% for b in breadcrumbs %}
          › <a href="{{ b.url }}">{{ b.name }}</a>
        {% endfor %}
      </nav>

      {# 栏目标题 #}
      <h1>{{ category.title or category.name }}</h1>
      {% if category.description %}
        <p>{{ category.description }}</p>
      {% endif %}

      {# 文章列表 #}
      {% for a in pagination %}
        <article>
          {% if a.cover_url %}
            <img src="{{ a.cover_url }}">
          {% endif %}
          <h2><a href="{{ a.url }}">{{ a.title }}</a></h2>
          <p>{{ a.description }}</p>
          <span>[{{ a.category.name }}]</span>
          <span>{{ a.published_at }}</span>
        </article>
      {% else %}
        <p>暂无文章</p>
      {% endfor %}

      {# 分页器 #}
      {% include "web_pagination.html" with context %}
    </div>

    <aside>
      {# 侧栏: 本周热门 #}
      <h3>本周热门</h3>
      {% for a in article_select(limit=10, order_by="views") %}
        <a href="{{ a.url }}">{{ a.title }}</a>
      {% endfor %}
    </aside>
  </div>
{% endblock %}
```

### 自定义文章详情页

```jinja
{% extends "web_base.html" %}

{% block title %}{{ article.title }} - {{ settings.site_name }}{% endblock %}
{% block description %}{{ article.description or '' }}{% endblock %}

{% block content %}
  <article>
    {# 面包屑 #}
    <nav>
      <a href="/">首页</a>
      {% for b in breadcrumbs %}
        › <a href="{{ b.url }}">{{ b.name }}</a>
      {% endfor %}
    </nav>

    <h1>{{ article.title }}</h1>
    <div>
      <a href="{{ article.category.url }}">{{ article.category.name }}</a>
      {{ article.published_at }}
      {{ article.creator.username }}
      {{ article.views }} 次阅读
    </div>

    {% if article.cover_url %}
      <img src="{{ article.cover_url }}">
    {% endif %}

    {# 正文 #}
    <div class="prose">
      {{ article.text | safe }}
    </div>

    {# 标签 #}
    {% if article.tags %}
      <div>
        {% for t in article.tags %}
          <a href="/t/{{ t.slug }}">{{ t.name }}</a>
        {% endfor %}
      </div>
    {% endif %}

    {# 微信分享 #}
    {{ wechat_share(title=article.title, desc=article.description, img=article.cover_url) | safe }}
  </article>
{% endblock %}
```

---

## 附录：缓存机制

- **categories 走 mtime 文件缓存**：`categories_tree()` / `categories()` / `category_select()` 首次查询存 `storages/runtime/categories.msgpack`，后续请求 stat 文件修改时间，未变则返回内存缓存（~2μs）。后台增删改栏目后自动删除缓存文件，下次查询重建。跨多 worker 即时一致。
- **tag_select / special_select 直接查库**：数据量小、调用少，不缓存。
- **article_select 直接查库**：参数化查询，结果随参数变化，不适合缓存。

> 模板中多次调用 `categories_tree()` 只会产生一次数据库查询（缓存命中后零查询）。
