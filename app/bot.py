import logging

import discord
from aiohttp import web
from discord import app_commands

from .db import Store
from .web import make_app

log = logging.getLogger("exchange-bot")


class ExchangeBot(discord.Client):
    def __init__(self, store: Store, guild_id: int, admin_user: str, admin_password: str, web_port: int):
        super().__init__(intents=discord.Intents.none())
        self.store, self.guild = store, discord.Object(id=guild_id)
        self.admin = (admin_user, admin_password, web_port)
        self.tree = app_commands.CommandTree(self)
        self._cmd = self._build_command()

    def _build_command(self):
        @app_commands.command(name="exchange", description="交換ワードを送信する")
        @app_commands.describe(word="交換ワード")
        async def exchange(interaction: discord.Interaction, word: str):
            # 無効時は本来登録されないが、反映遅延に備えて何も教えない
            if not self.store.is_enabled():
                await interaction.response.send_message("このコマンドは現在使えません。", ephemeral=True)
                return
            status, fragment = self.store.exchange(
                str(interaction.user.id), str(interaction.user), word)
            if status == "ok":
                # 同じチャンネルに公開で返信 (断片は公開してよい仕様)
                await interaction.response.send_message(
                    f"{interaction.user.mention} 断片: {fragment}")
            elif status == "already":
                await interaction.response.send_message(
                    "あなたはすでに交換を行っています。交換は1人1回までです。", ephemeral=True)
            else:
                await interaction.response.send_message(
                    "その交換ワードでは何も起きませんでした。(回数は消費されていません)", ephemeral=True)
        return exchange

    async def apply_state(self, enabled: bool) -> None:
        """有効時のみスラッシュコマンドを登録する(無効中はコマンド一覧にも出ない)。"""
        self.tree.clear_commands(guild=self.guild)
        if enabled:
            self.tree.add_command(self._cmd, guild=self.guild)
        await self.tree.sync(guild=self.guild)

    async def setup_hook(self):
        user, pw, port = self.admin
        app = make_app(self.store, user, pw, on_toggle=self.apply_state)
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", port).start()
        log.info("admin site on :%s", port)
        await self.apply_state(self.store.is_enabled())
