# 交換BOT (ATGT2026TB 最終問題用)

Discordで `/exchange <交換ワード>` を送ると「断片」が返るBOT。管理はWebサイトから行います。

## 仕様

- 交換機能は管理画面で**有効にするまで無効**。無効中は `/exchange` コマンドがDiscord上に存在せず、告知にもなりません(有効化した時点でコマンドが登録されます)。
- **1ユーザーにつき交換できるのは1回だけ**(どのワードでも可)。
- 存在しない交換ワードでは回数を消費しません(本人にだけ見えるメッセージ)。
- 成功時は**コマンドを受信したチャンネルにそのまま公開で**返信(どのチャンネルでも動作)。エラーは本人にだけ表示。
- 交換ワードは全角半角・大文字小文字・前後空白を区別しません。
- 交換ワード/断片は管理画面で追加・編集・削除でき、問題数が未定でも対応できます。

## 管理画面でできること

交換機能のON/OFF、交換ワードと断片の追加・編集・削除・一括取り込み(`ワード,断片` を1行ずつ)、交換済みユーザー一覧、ユーザー個別/全員のリセット。

## セットアップ

### 1. Discord BOTを作る
1. https://discord.com/developers/applications で **New Application**
2. **Bot** タブ → **Reset Token** でトークンを控える(他人に見せない)。特権インテントは不要。
3. **OAuth2 → URL Generator**: scopes に `bot` と `applications.commands`、権限は `View Channels` / `Send Messages`。生成URLでサーバーに招待。
4. Discordの設定で開発者モードを有効にし、サーバーを右クリック→**IDをコピー**(= `GUILD_ID`)。

### 2. VPSを用意する
Ubuntu等のVPSを借り、80/443番ポートを開けます。管理画面用ドメインのAレコードをVPSのIPに向けてください(Basic認証を平文HTTPで使わないためHTTPS前提です)。

VPSにDockerとgitを入れ(Docker公式の手順に従う)、次を実行します。

```bash
git clone https://github.com/Inamiobservationcenter/-.git exchange-bot
cd exchange-bot
cp .env.example .env
nano .env        # DISCORD_TOKEN / GUILD_ID / ADMIN_PASSWORD / DOMAIN を設定
docker compose up -d --build
docker compose logs -f bot
```

### 3. 運用
1. `https://<DOMAIN>/` を開き、`ADMIN_USER` / `ADMIN_PASSWORD` でログイン。
2. 交換ワードと断片を登録(事前に別サーバーでテスト推奨)。
3. 最終問題の開始時に **「有効にする」** を押す → `/exchange` が使えるようになる。
4. 終了後は「無効にする」。データは `./data/bot.db`(バックアップはこのファイルをコピー)。

更新: `git pull && docker compose up -d --build`

## 開発・テスト
```bash
pip install -r requirements-dev.txt
pytest
```
