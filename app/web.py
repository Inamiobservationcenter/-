"""Password-protected admin site (HTTP Basic auth + CSRF token)."""
import base64
import hashlib
import hmac
from pathlib import Path

import jinja2
from aiohttp import web

from .db import Store

_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(Path(__file__).parent.parent / "templates"),
    autoescape=True)


def make_app(store: Store, user: str, password: str, on_toggle=None) -> web.Application:
    csrf = hmac.new(password.encode(), b"csrf", hashlib.sha256).hexdigest()

    @web.middleware
    async def guard(request: web.Request, handler):
        h = request.headers.get("Authorization", "")
        ok = False
        if h.startswith("Basic "):
            try:
                u, _, p = base64.b64decode(h[6:]).decode().partition(":")
                ok = hmac.compare_digest(u, user) & hmac.compare_digest(p, password)
            except Exception:
                ok = False
        if not ok:
            return web.Response(status=401, headers={"WWW-Authenticate": 'Basic realm="admin"'})
        if request.method == "POST":
            data = await request.post()
            if not hmac.compare_digest(str(data.get("csrf", "")), csrf):
                return web.Response(status=403, text="bad csrf token")
        return await handler(request)

    routes = web.RouteTableDef()

    @routes.get("/")
    async def index(request):
        words = store.list_words()
        ex = store.list_exchanges()
        html = _env.get_template("admin.html").render(
            enabled=store.is_enabled(), words=words, exchanges=ex, csrf=csrf,
            msg=request.query.get("msg", ""))
        return web.Response(text=html, content_type="text/html")

    def back(msg=""):
        raise web.HTTPSeeOther("/" + (f"?msg={msg}" if msg else ""))

    @routes.post("/toggle")
    async def toggle(request):
        data = await request.post()
        on = data.get("enabled") == "1"
        store.set_enabled(on)
        if on_toggle:
            try:
                await on_toggle(on)
            except Exception as e:  # report sync problems on the page
                back(f"状態は保存しましたがDiscordへの反映に失敗: {e}")
        back("有効にしました" if on else "無効にしました")

    @routes.post("/word")
    async def word(request):
        d = await request.post()
        try:
            store.upsert_word(str(d.get("word", "")), str(d.get("fragment", "")), str(d.get("label", "")))
        except ValueError:
            back("交換ワードと断片は必須です")
        back("保存しました")

    @routes.post("/word/delete")
    async def word_delete(request):
        store.delete_word(str((await request.post()).get("word", "")))
        back("削除しました")

    @routes.post("/bulk")
    async def bulk(request):
        """Lines of `word,fragment` or `word<TAB>fragment` (first separator splits)."""
        text = str((await request.post()).get("text", ""))
        n = 0
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            sep = "\t" if "\t" in line else ","
            w, _, f = line.partition(sep)
            try:
                store.upsert_word(w, f)
                n += 1
            except ValueError:
                pass
        back(f"{n}件を取り込みました")

    @routes.post("/reset")
    async def reset(request):
        uid = str((await request.post()).get("user_id", ""))
        if uid == "*":
            store.reset_all()
        else:
            store.reset_user(uid)
        back("リセットしました")

    app = web.Application(middlewares=[guard])
    app.add_routes(routes)
    return app
