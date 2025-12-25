import html
import traceback
from typing import MutableMapping, Type, Union

from jinja2 import TemplateError
from litestar import MediaType, Request, Response
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR
from litestar.types import ExceptionHandler

from application.config import config

__all__ = ["exception_handler"]


def plain_html_exception_handler(request: Request, exc: Exception) -> Response:
    if not config.debug:
        # 生产环境：简单错误页面
        return Response(
            content="服务器内部错误，请稍后重试",
            status_code=500,
            media_type=MediaType.HTML,
        )

    s_err, s_msg, s_tb = (
        html.escape(type(exc).__name__),
        html.escape(str(exc)),
        html.escape(traceback.format_exc()),
    )
    s_method, s_path = html.escape(request.method), html.escape(request.url.path)
    s_ip = html.escape(request.client.host if request.client else "Unknown")

    loc_html = ""
    try:
        tb = traceback.extract_tb(exc.__traceback__)
        if tb:
            tf = tb[-1]
            t_name = str(getattr(exc, "name", "") or getattr(exc, "filename", "") or "")
            if isinstance(exc, TemplateError) and t_name:
                for f in reversed(tb):
                    if str(f.filename).endswith(t_name) or str(f.filename).endswith(
                        ".html"
                    ):
                        tf = f
                        break
            elif "site-packages" in tf.filename:
                for f in reversed(tb):
                    if "site-packages" not in f.filename:
                        tf = f
                        break

            ctx = "Global / Top Level" if tf.name == "<module>" else tf.name
            s_f, s_c, s_ctx = (
                html.escape(tf.filename),
                html.escape(tf.line or ""),
                html.escape(ctx),
            )

            loc_html = f"""<div class="error-location-card">
                <div class="loc-row"><span class="loc-label">FILE:</span><span class="loc-value file-path">{s_f}</span></div>
                <div class="loc-row mult-items">
                    <div class="loc-group"><span class="loc-label">LINE:</span><span class="loc-value line-number">{tf.lineno}</span></div>
                    <div class="loc-group"><span class="loc-label">CONTEXT:</span><span class="loc-value">{s_ctx}</span></div>
                </div><div class="code-snippet">{s_c}</div></div>"""
    except Exception:
        pass  # Fixed: E722 Do not use bare `except`

    return Response(
        content=f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Server Error (500)</title><style>
        *{{box-sizing:border-box}}body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background-color:#eaeff2;color:#333;margin:0;padding:30px}}
        .container{{width:100%;max-width:1280px;margin:0 auto;background:#fff;border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,.1);overflow:hidden}}
        .header{{background:linear-gradient(135deg,#d32f2f 0%,#b71c1c 100%);color:#fff;padding:30px}}
        .header h1{{margin:0;font-size:1.8rem;font-weight:700;letter-spacing:.5px}}.header .subtitle{{margin-top:12px;font-family:"SFMono-Regular",Consolas,Monaco,monospace;font-size:1rem;background:rgba(0,0,0,.25);padding:8px 12px;border-radius:6px;display:inline-block;word-break:break-all;line-height:1.4}}
        .error-location-card{{margin-top:25px;background:rgba(255,255,255,.98);color:#333;padding:20px;border-radius:8px;box-shadow:0 4px 15px rgba(0,0,0,.2)}}
        .loc-row{{display:flex;align-items:baseline;flex-wrap:wrap;gap:8px;margin-bottom:8px;font-size:.95rem}}.loc-row.mult-items{{gap:25px}}
        .loc-group{{display:inline-flex;align-items:baseline;white-space:nowrap}}.loc-label{{font-weight:700;font-size:.8rem;color:#666;margin-right:8px;text-transform:uppercase;letter-spacing:.5px}}
        .loc-value{{font-family:Consolas,monospace;word-break:break-all}}.file-path{{color:#0277bd;font-weight:600}}.line-number{{color:#d32f2f;font-weight:800;font-size:1.2rem}}
        .code-snippet{{margin-top:12px;background:#212121;color:#a5d6a7;padding:12px 15px;border-radius:6px;font-family:Consolas,monospace;font-size:.9rem;border-left:5px solid #d32f2f;overflow-x:auto;white-space:pre-wrap;word-wrap:break-word}}
        .meta{{background-color:#f8f9fa;padding:15px 30px;border-bottom:1px solid #e0e0e0;display:flex;flex-wrap:wrap;gap:20px;align-items:center}}
        .meta-item{{font-size:.9rem;color:#546e7a;background:#eceff1;padding:6px 12px;border-radius:20px;display:flex;align-items:center}}.meta-item strong{{color:#263238;margin-right:8px;font-weight:700;font-size:.8rem}}
        .content{{padding:30px}}h3{{margin-top:0;font-size:1.2rem;color:#37474f;margin-bottom:15px;display:flex;align-items:center}}h3::before{{content:"";display:inline-block;width:6px;height:20px;background:#d32f2f;margin-right:10px;border-radius:3px}}
        pre{{background:#263238;color:#eceff1;padding:20px;border-radius:8px;font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;font-size:.9rem;line-height:1.6;box-shadow:inset 0 2px 10px rgba(0,0,0,.3);white-space:pre-wrap;word-wrap:break-word;overflow-x:hidden}}
        </style></head><body><div class="container"><div class="header"><h1>Internal Server Error</h1><div class="subtitle">{s_err}: {s_msg}</div>{loc_html}</div>
        <div class="meta"><div class="meta-item"><strong>Path</strong> {s_path}</div><div class="meta-item"><strong>Method</strong> {s_method}</div><div class="meta-item"><strong>Client IP</strong> {s_ip}</div></div>
        <div class="content"><h3>Traceback Details</h3><pre>{s_tb}</pre></div></div></body></html>""",
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        media_type=MediaType.HTML,
    )


ExceptionConfig = MutableMapping[Union[int, Type[Exception]], ExceptionHandler]

exception_handler: ExceptionConfig = {
    Exception: plain_html_exception_handler,
}
