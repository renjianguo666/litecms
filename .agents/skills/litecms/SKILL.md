---
name: litecms
description: Generate Litestar server rendered CMS applications using AdvancedAlchemy and daisyUI
---

# Purpose

Build maintainable server-rendered CMS applications.

Prefer simple architecture and explicit code.

# Stack

Backend:

* Litestar

Database:

* AdvancedAlchemy
* SQLAlchemy ORM

Migration:

* AdvancedAlchemy migration workflow

Session:

* AdvancedAlchemy synchronous session

Templates:

* Jinja

Frontend:

* Tailwind CSS
* daisyUI v5

# Generation Rules

Always generate runnable code.

Always include imports.

Always include file paths.

Always include templates.

Never omit implementation details.

Never output pseudo code.

Never output TODO placeholders.

# Architecture

Always use SSR.

Always return rendered HTML.

Prefer:

Route
→ Service
→ Repository
→ Model

Avoid:

Route
→ Database

# Database

Always use AdvancedAlchemy.

Always use synchronous sessions.

Prefer dependency injection.

Never:

* AsyncSession
* async handlers
* manual session lifecycle
* manual Alembic setup
* raw SQLAlchemy session factories

# Routing

Prefer:

pages.py
admin.py
auth.py

Avoid giant route files.

Prefer explicit handlers.

# Templates

Prefer:

templates/

base.html

partials/

components/

pages/

Prefer:

Jinja include

Jinja macro

Avoid:

deep nesting

duplicate markup

# UI

Use daisyUI components.

Prefer:

navbar

drawer

card

table

stats

input

select

textarea

modal

pagination

badge

alert

btn

Avoid:

custom CSS

inline styles

bootstrap

component libraries

# Forms

Always prefer HTML forms.

Workflow:

GET
→ render

POST
→ validate

redirect
→ success

Display validation errors in template.

Avoid:

JSON forms

frontend validation logic

frontend state

# Admin Pages

Default layout:

Navbar

Sidebar

Content

Table

Actions

Pagination

Search

Filters

Use:

daisyUI drawer

daisyUI table

daisyUI card

# CRUD

Generate:

List

Create

Edit

Delete

Detail

Prefer reusable form templates.

# Code Style

Prefer:

explicit code

simple functions

readability

Prefer standard library first.

Avoid:

magic abstractions

heavy decorators

unnecessary inheritance

# Documentation

Reference:

https://docs.litestar.dev/

https://docs.advanced-alchemy.litestar.dev/

https://docs.sqlalchemy.org/

https://daisyui.com/llms.txt
