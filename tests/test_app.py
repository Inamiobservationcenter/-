import base64

import pytest

from app.db import Store
from app.web import make_app

AUTH = {"Authorization": "Basic " + base64.b64encode(b"admin:pw").decode()}


def test_exchange_rules(tmp_path):
    s = Store(str(tmp_path / "t.db"))
    s.upsert_word("ＡＢＣ", "frag1")
    s.upsert_word("def", "frag2")
    assert s.exchange("1", "u", "nope") == ("unknown", None)   # invalid does not consume
    assert s.exchange("1", "u", " abc ") == ("ok", "frag1")    # normalized
    assert s.exchange("1", "u", "def") == ("already", None)    # only one ever
    assert s.exchange("2", "v", "abc") == ("ok", "frag1")      # others may reuse the word
    s.reset_user("1")
    assert s.exchange("1", "u", "def") == ("ok", "frag2")
    assert s.is_enabled() is False
    s.set_enabled(True)
    assert s.is_enabled() is True


async def test_web(aiohttp_client, tmp_path):
    s = Store(str(tmp_path / "t.db"))
    calls = []

    async def on_toggle(on):
        calls.append(on)

    c = await aiohttp_client(make_app(s, "admin", "pw", on_toggle))
    assert (await c.get("/")).status == 401
    r = await c.get("/", headers=AUTH)
    assert r.status == 200
    html = await r.text()
    token = html.split('name="csrf" value="')[1].split('"')[0]
    bad = await c.post("/toggle", data={"enabled": "1", "csrf": "x"}, headers=AUTH, allow_redirects=False)
    assert bad.status == 403
    ok = await c.post("/toggle", data={"enabled": "1", "csrf": token}, headers=AUTH, allow_redirects=False)
    assert ok.status == 303 and calls == [True] and s.is_enabled()
    await c.post("/bulk", data={"text": "a,x\nb\ty,z\n", "csrf": token}, headers=AUTH)
    assert {w["word"]: w["fragment"] for w in s.list_words()} == {"a": "x", "b": "y,z"}
