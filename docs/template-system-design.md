# 模板系统设计文档

> ✅ **实现状态**: 已完成（后端 API + 前端表单 + 目录结构）

## 概述

本文档描述 LiteCMS 模板系统的设计方案，支持栏目模板、专题模板、推荐位模板和多站点首页模板。

## 目录结构

```
templates/
├── categories/                 # 栏目模板（含文章）
│   ├── category.html           # 默认栏目列表页模板
│   ├── article.html            # 默认文章详情页模板
│   ├── auto.html               # auto 栏目模板
│   ├── auto.article.html       # auto 文章模板
│   ├── tech.html               # tech 栏目模板
│   └── tech.article.html       # tech 文章模板
│
├── topics/                     # 专题模板
│   ├── topic.html              # 默认专题模板
│   ├── spring-sale.html        # 自定义专题模板
│   └── year-end.html
│
├── features/                   # 推荐位模板
│   ├── feature.html            # 默认推荐位模板
│   ├── rss.xml                 # RSS 输出模板
│   └── hot-list.html
│
├── domains/                    # 站点首页模板
│   ├── index.html              # 默认首页模板
│   ├── baidu.com.html          # baidu.com 站点首页
│   └── google.com.html         # google.com 站点首页
│
├── 404.html                    # 404 页面
└── home.html                   # 其他全局模板
```

## 模块说明

### 1. Categories（栏目模板）

栏目使用模板模式，一个模板对应栏目和文章两个模板文件。

**数据模型字段**：
- `template: str` - 模板名称，如 "auto"、"tech"（**必填，NOT NULL**）

**目录规则**：
- 栏目模板：`templates/categories/{template}.html`
- 文章模板：`templates/categories/{template}.article.html`

**渲染逻辑**：
```python
def get_category_template(template: str) -> str:
    """
    获取栏目模板
    
    Args:
        template: 模板名，如 "auto"、"tech"
    
    Returns:
        模板路径
    """
    return f"categories/{template}.html"


def get_article_template(template: str) -> str:
    """
    获取文章模板
    
    Args:
        template: 模板名，如 "auto"、"tech"
    
    Returns:
        模板路径
    """
    return f"categories/{template}.article.html"
```

**示例**：

| 栏目 template | 渲染栏目页 | 渲染文章页 |
|--------------|-----------|-----------|
| `"auto"` | `categories/auto.html` | `categories/auto.article.html` |
| `"tech"` | `categories/tech.html` | `categories/tech.article.html` |
| `"category"` | `categories/category.html` | `categories/category.article.html` |

### 2. Topics（专题模板）

专题使用独立模板模式，每个专题必须指定模板文件。

**数据模型字段**：
- `template: str` - 模板文件名，如 "spring-sale.html"（**必填，NOT NULL**）

**目录规则**：
- 模板文件：`templates/topics/{template}`

**渲染逻辑**：
```python
def get_topic_template(template: str) -> str:
    """
    获取专题模板
    
    Args:
        template: 模板文件名，如 "spring-sale.html"
    
    Returns:
        模板路径
    """
    return f"topics/{template}"
```

### 3. Features（推荐位模板）

推荐位使用独立模板模式，支持 HTML 和 XML 等多种格式。

**数据模型字段**：
- `template: str` - 模板文件名，如 "rss.xml"（**必填，NOT NULL**）

**目录规则**：
- 模板文件：`templates/features/{template}`

**渲染逻辑**：
```python
def get_feature_template(template: str) -> str:
    """
    获取推荐位模板
    
    Args:
        template: 模板文件名，如 "rss.xml"
    
    Returns:
        模板路径
    """
    return f"features/{template}"
```

### 4. Domains（站点首页模板）

多站点首页模板，根据域名自动匹配。

**目录规则**：
- 模板文件：`templates/domains/{domain}.html`
- 根目录的 `index.html` 作为默认兜底

**渲染逻辑**：
```python
def get_domain_template(domain: str | None) -> str:
    """
    获取站点首页模板
    
    Args:
        domain: 域名，如 "baidu.com"、"google.com"、None/""
    
    Returns:
        模板路径
    """
    if domain:
        domain_template = f"domains/{domain}.html"
        if exists(domain_template):
            return domain_template
    
    return "domains/index.html"
```

**说明**：
- 域名从 Category 的 `domain` 字段获取（已有字段）
- 渲染首页时根据请求域名自动匹配

## API 设计

### 获取模板选项

**端点**：`GET /api/templates/options`

**查询参数**：
- `type`（可选）：模板类型，可选值 `categories`、`topics`、`features`、`domains`

**响应格式**：

不传 `type` 时返回全部：
```json
{
  "categories": ["auto", "tech", "category"],
  "topics": ["topic.html", "spring-sale.html", "year-end.html"],
  "features": ["feature.html", "rss.xml", "hot-list.html"],
  "domains": ["index.html", "baidu.com.html", "google.com.html"]
}
```

传 `type=categories` 时只返回对应类型：
```json
{
  "items": ["auto", "tech", "category"]
}
```

**说明**：
- `categories` 返回模板名（从文件名提取，如 `auto.html` → `auto`）
- `topics`、`features`、`domains` 返回完整文件名

## 数据模型汇总

| 模块 | 字段 | 类型 | 值示例 | 选项来源 |
|------|------|------|--------|----------|
| Category | `template` | `str` (NOT NULL) | `"auto"` | `categories/` 下的模板名 |
| Topic | `template` | `str` (NOT NULL) | `"spring-sale.html"` | `topics/` 下的文件名 |
| Feature | `template` | `str` (NOT NULL) | `"rss.xml"` | `features/` 下的文件名 |
| Domain | 自动匹配 | - | - | `domains/` 下的文件名 |

## 前端表单设计

### Category 表单
```tsx
<form.SelectField
  name="template"
  label="模板"
  options={templateOptions}  // ["auto", "tech", "category"]
  placeholder="请选择模板"
/>
```

### Topic 表单
```tsx
<form.SelectField
  name="template"
  label="专题模板"
  options={topicTemplateOptions}  // ["topic.html", "spring-sale.html"]
  placeholder="请选择模板"
/>
```

### Feature 表单
```tsx
<form.SelectField
  name="template"
  label="推荐位模板"
  options={featureTemplateOptions}  // ["feature.html", "rss.xml"]
  placeholder="请选择模板"
/>
```

## 实现状态

### 后端 ✅

1. **模板目录结构** ✅
   - 创建 `categories/`、`topics/`、`features/`、`domains/` 目录
   - 创建模板文件

2. **API 端点** ✅
   - `GET /api/templates/options` - 获取模板选项列表
   - `GET /api/templates/options?type=xxx` - 获取指定类型选项

3. **数据模型** ✅
   - Category：`template: str` (NOT NULL)
   - Topic：`template: str` (NOT NULL)
   - Feature：`template: str` (NOT NULL)

### 前端 ✅

1. **缓存配置** ✅
   - 添加 `templateOptions` 缓存 key

2. **表单组件** ✅
   - Category 表单：模板选择（Select，必填）
   - Topic 表单：模板选择（Select，必填）
   - Feature 表单：模板选择（Select，必填）

3. **API 调用** ✅
   - `template.options()` - 获取全部选项
   - `template.optionsByType(type)` - 获取指定类型选项

### 待实现

1. **渲染逻辑**
   - 实现模板查找机制

## 注意事项

1. **必填字段**：`template` 字段在 Category、Topic、Feature 中都是必填的，创建时必须选择模板
2. **模板文件命名**：避免使用特殊字符，建议使用小写字母、数字、连字符
3. **性能考虑**：模板选项可以在前端缓存，减少 API 请求

## 当前目录结构

```
templates/
├── categories/
│   ├── category.html           # 默认栏目模板
│   ├── article.html            # 默认文章模板
│   ├── auto.html               # auto 栏目模板
│   ├── auto.article.html       # auto 文章模板
│   ├── tech.html               # tech 栏目模板
│   └── tech.article.html       # tech 文章模板
├── topics/
│   ├── topic.html              # 默认专题模板
│   └── gyszbyc.html            # 自定义专题模板
├── features/
│   ├── feature.html            # 默认推荐位模板
│   └── rss.xml                 # RSS 模板
├── domains/
│   └── index.html              # 默认首页模板
├── 404.html
├── home.html
└── ...
```
