import logging
import os
import sys

from .bot import ExchangeBot
from .db import Store


def main():
    logging.basicConfig(level=logging.INFO)
    env = os.environ
    for k in ("DISCORD_TOKEN", "GUILD_ID", "ADMIN_PASSWORD"):
        if not env.get(k):
            sys.exit(f"環境変数 {k} が未設定です (.env を確認してください)")
    os.makedirs(env.get("DATA_DIR", "data"), exist_ok=True)
    store = Store(os.path.join(env.get("DATA_DIR", "data"), "bot.db"))
    bot = ExchangeBot(store, int(env["GUILD_ID"]), env.get("ADMIN_USER", "admin"),
                      env["ADMIN_PASSWORD"], int(env.get("WEB_PORT", "8080")))
    bot.run(env["DISCORD_TOKEN"])


if __name__ == "__main__":
    main()
