# LiteCMS Project Instructions

Litestar CMS — server-rendered content management system with AdvancedAlchemy, HTMX, and daisyUI.

## Project

- **Stack:** Litestar, AdvancedAlchemy, SQLAlchemy ORM, Jinja2, HTMX, Alpine.js, Tailwind CSS, daisyUI v5
- **Python:** 3.14+
- **Package manager:** uv (see `uv.lock`)
- **Entry point:** `application/__init__.py` → `create_app()` returns a `Litestar` instance
- **Run command:** `litestar run` (from project root)

## Commands

```sh
litestar run                        # Start dev server
litestar run --reload               # Start with auto-reload
litestar run --debug                # Debug mode with debug toolbar
litestar database upgrade           # Run pending migrations (AdvancedAlchemy)
litestar database downgrade         # Rollback last migration
litestar database revision --create "message"  # Create new migration
uv add <package>                    # Add dependency
uv sync                             # Install dependencies from lockfile
```

Migrations use AdvancedAlchemy's Alembic integration — never run `alembic` directly.

**Layer flow:** Route Handler → Service → Repository → Model

**Key modules:**
- `plugins.py` — `PluginRegistry` with cached properties, keeps plugin config centralized
- `database.py` — SQLite WAL+optimizations, PostgreSQL pool_pre_ping, JSON via Litestar encoders
- `htmx.py` — `HTMXMixin` base for controllers; `HXLocationTrigger` for toast + redirect combos
- `mixins.py` — `PaginationServiceMixin` adds `.paginate()` to any service; `SoftDeleteServiceMixin` overrides `.delete()`
- `router.py` — All admin controllers under `/admin` with `inject_admin_menus_hook` before_request

## Conventions

### Style
- `from __future__ import annotations` at top of every Python file
- Models inherit `UUIDv7AuditBase` or `UUIDv7Base` from AdvancedAlchemy
- Table names: `snake_case_plural` (e.g. `accounts_users`, `contents_items`)
- Route names: `module:action` (e.g. `dashboard:index`, `settings:save`)

### Controllers
- Extend `HTMXMixin` + `Litestar Controller`
- Use `create_service_provider(ServiceClass)` for DI dependencies
- Accept `data: URLEncodedBody` for POST form data (never msgspec DTOs for forms)
- Accept `db_session: Session` for direct database access (injected by plugin)
- GET → render template; POST → validate → redirect (or re-render with errors)
- Use `self.htmx_render()` for HTMX-aware partial responses
- Use `self.htmx_success()` / `self.htmx_error()` for toast + redirect combos

### Forms
- WTForms for all form handling (never msgspec schemas for user input)
- Initialize with `FormClass(data=data)` where `data` is `URLEncodedBody`
- Validate with `form.validate()` before passing `form.data` to the service layer
- Display validation errors in templates via `form.field(...)` calls

### Services
- Extend `SQLAlchemySyncRepositoryService[ModelType]`
- Define a sibling `Repository` class extending `SQLAlchemySyncRepository[ModelType]`
- Mix in `PaginationServiceMixin` for `.paginate()` support
- Mix in `SoftDeleteServiceMixin` for soft-delete support
- Override `to_model_on_create()` / `to_model_on_update()` for relationship wiring
- Use `schema_dump()` from AdvancedAlchemy for msgspec-to-dict conversion

### Database
- SQLite: WAL mode, foreign keys ON, busy_timeout=30s, BEGIN IMMEDIATE
- Never create sessions or engines manually

### Templates
- Jinja2 with `HTMXBlockTemplate` for partial page renders
- Macros in `templates/_macros/` (form helpers, pagination, table, wrapper)
- Admin layout: `templates/admin.html` + `admin_header.html` + `admin_menu.html`
- Form fields use `{{ form.field(class_="...") }}` with Tailwind CSS classes

### Auth
- `SessionAuth` with `ServerSideSessionBackend`
- User ID stored in session under key `"user"`
- `retrieve_user_handler` loads user from DB on each request
- `NotAuthorizedException` → redirect to login via `not_authorized_handler`
- Superuser check: `user.is_superuser` grants wildcard `["*"]` permissions
- Permission check: `user.has_permission(name)` iterates through role permissions

### Frontend
- Full SSR — no SPA, no React/Vue, no client-side routing
- HTMX for partial updates, Alpine.js for client interactivity
- daisyUI v5 components (prefer over custom CSS)
- Tailwind CSS for utilities (avoid inline styles)
- `x-show` + `x-transition` for all visibility toggles

## Forbidden

Never generate:
- SPA, React, Vue, client-side routing, API-first frontend architecture
- Client-side state management
- Direct Alembic CLI usage or manual alembic env config
- Pseudo code, TODO placeholders, omitted implementation
- JSON form submissions, REST endpoints (unless explicitly requested)
- Global sessions, business logic inside routes
- Unnecessary DTO, unnecessary abstraction, excessive DI

## Documentation References

- Litestar: https://docs.litestar.dev/
- AdvancedAlchemy: https://docs.advanced-alchemy.litestar.dev/
- SQLAlchemy: https://docs.sqlalchemy.org/
- daisyUI: https://daisyui.com/llms.txt
- HTMX: https://htmx.org/docs/
- Alpine.js: https://alpinejs.dev/start-here
- WTForms: https://wtforms.readthedocs.io/

## Notes

(Reserved for quick additions.)
