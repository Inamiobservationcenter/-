# 導入手順書

交換BOTを、レンタルしたVPSに設置してDiscordサーバーで使えるようにするまでの手順です。上から順に進めてください。所要時間の目安は1〜2時間です(ドメイン反映待ちを除く)。

## 0. 用意するもの

| もの | 備考 |
|---|---|
| Discordアカウントと、BOTを入れるサーバーの管理権限 | サーバーの所有者か「サーバー管理」権限が必要 |
| VPS | Ubuntu 22.04/24.04、メモリ1GB以上(参加者40人程度なら十分) |
| ドメイン | 管理画面用。例: `admin.example.com`。VPS会社やドメイン会社で取得 |

> 本番の前に、テスト用のDiscordサーバーを1つ作って一通り動かすことを強くおすすめします。

---

## 1. Discord BOTを作る

1. https://discord.com/developers/applications を開き、**New Application** → 名前(例: 交換BOT)を入力して作成。
2. 左メニュー **Bot**
   - **Reset Token** を押してトークンを表示し、メモ帳などに控える。**トークンは他人に見せない・Gitに載せない**(漏れたらここで再発行)。
   - 特権インテント(Privileged Gateway Intents)は**すべてオフのまま**でよい。
3. 左メニュー **OAuth2 → URL Generator**
   - **SCOPES**: `bot` と `applications.commands` にチェック
   - **BOT PERMISSIONS**: `View Channels`、`Send Messages` にチェック
   - 画面下に出る **GENERATED URL** をブラウザで開き、BOTを入れるサーバーを選んで認証。
4. サーバーIDを調べる
   - Discord の **ユーザー設定 → 詳細設定 → 開発者モード** をオンにする。
   - サーバーアイコンを右クリック → **サーバーIDをコピー**。これが `GUILD_ID`。

ここまでで控えたもの: **BOTトークン** と **サーバーID**。

> BOTを入れた直後はオフラインに見えます。VPSで起動すると、オンラインになります。

---

## 2. VPSを借りる

1. 好みのVPS会社でUbuntuのVPSを契約する(国内ならさくら、ConoHa、Xserver VPS など。海外なら Vultr、Hetzner など。どれでも可)。
2. 契約後に控えるもの: **VPSのIPアドレス**、**rootまたはユーザーのSSHログイン情報**。
3. VPS会社のファイアウォール(パケットフィルタ)の設定画面がある場合は、次のポートを**許可**する。
   - 22 (SSH)、80 (HTTP)、443 (HTTPS)

## 3. ドメインをVPSに向ける

ドメインのDNS設定で、管理画面用のホスト名に**Aレコード**を追加します。

- 名前: `admin`(= `admin.example.com`)
- 種類: A
- 値: VPSのIPアドレス

反映には数分〜数時間かかります。`ping admin.example.com` でVPSのIPが返ればOKです。

---

## 4. VPSにDockerを入れる

自分のPCからVPSにSSHでログインします(WindowsはPowerShell、MacはターミナルでOK)。

```bash
ssh root@<VPSのIPアドレス>
```

Docker公式の手順(https://docs.docker.com/engine/install/ubuntu/)に従ってDocker Engineを入れます。公式の簡易スクリプトを使う場合:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
docker compose version     # バージョンが表示されれば成功
```

## 5. BOTを設置する

```bash
git clone https://github.com/Inamiobservationcenter/-.git exchange-bot
cd exchange-bot
cp .env.example .env
nano .env
```

`.env` を次のように埋めて保存します(nano は `Ctrl+O` → Enter で保存、`Ctrl+X` で終了)。

```
DISCORD_TOKEN=手順1で控えたBOTトークン
GUILD_ID=手順1で控えたサーバーID
ADMIN_USER=admin
ADMIN_PASSWORD=推測されにくい長いパスワード
DOMAIN=admin.example.com
```

- `ADMIN_PASSWORD` は必ず自分で決めて設定してください(未設定だと起動しません)。
- `.env` はGitに含まれません。他人に渡さないでください。

起動します。

```bash
docker compose up -d --build
docker compose logs -f bot       # 確認後 Ctrl+C で抜ける(BOTは動き続ける)
```

ログにエラーが出ず、DiscordでBOTがオンラインになれば成功です。

## 6. 管理画面にログインする

ブラウザで `https://admin.example.com/` を開き、`ADMIN_USER` / `ADMIN_PASSWORD` でログインします。初回はHTTPS証明書の取得に少し時間がかかることがあります(1分ほど待って再読み込み)。

画面の見方:

- **交換機能**: 有効/無効の切り替え。最初は**無効**。
- **交換ワードと断片**: 1行ずつ編集・追加・削除。「一括取り込み」に `交換ワード,断片` を1行ずつ貼り付けても登録できます。
- **交換済みユーザー**: 誰がどのワードを交換したか。個別リセット/全員リセットが可能。

## 7. 動作確認(テスト)

テスト用サーバーで次を確認します。

1. 管理画面でテスト用の交換ワードと断片を登録する。
2. 機能が**無効**のとき、Discordで `/exchange` と入力してもコマンド候補に出ないこと。
3. 管理画面で **有効にする** を押す。数秒後、`/exchange` が候補に出ること(出ない場合はDiscordアプリを再読み込み: `Ctrl+R` / スマホは再起動)。
4. `/exchange word:登録したワード` を雑談チャンネルなどで送り、**同じチャンネルに断片が返る**こと。
5. もう一度送ると「すでに交換を行っています」と本人にだけ表示されること。
6. 管理画面の「交換済みユーザー」からリセットし、再度交換できること。
7. テスト後、**全員リセット**で履歴を空にし、テスト用ワードを削除する。

## 8. 本番の運用

1. 本番サーバーでも手順1のBOT招待をして、`.env` の `GUILD_ID` を本番サーバーのIDにする。変更後は `docker compose up -d` で反映。
2. 本番の交換ワードと断片を登録する(事前に)。
3. 最終問題の開始時に、管理画面で **有効にする** を押す。告知は不要です(有効化するまで `/exchange` は存在しません)。
4. 終了後は **無効にする**。

### 運営が知っておくこと

- 1人が交換できるのは**1回だけ**。間違ったワード(存在しないワード)は回数を消費しません。
- 断片は交換した本人だけでなく、そのチャンネルの全員に見えます(仕様どおり)。
- 運営がヒントや断片を直接出さないため、断片が足りないときは、参加者に人数を集めるよう促すことになります。
- 誤操作で交換してしまった人は、管理画面の「リセット」で救済できます。

### 保守コマンド(VPS上の `exchange-bot` ディレクトリで)

| やりたいこと | コマンド |
|---|---|
| ログを見る | `docker compose logs -f bot` |
| 再起動 | `docker compose restart bot` |
| 停止 | `docker compose down` |
| 更新 | `git pull && docker compose up -d --build` |
| バックアップ | `cp data/bot.db bot-backup.db` |

データは `data/bot.db` に保存され、更新や再起動では消えません。

---

## トラブルシューティング

| 症状 | 確認すること |
|---|---|
| BOTがオフラインのまま | `docker compose logs bot` を確認。`DISCORD_TOKEN` の誤りが多い。トークンを再発行して `.env` を直し、`docker compose up -d` |
| 起動直後に「環境変数が未設定」 | `.env` の `DISCORD_TOKEN` / `GUILD_ID` / `ADMIN_PASSWORD` が空になっていないか |
| 管理画面が開けない | DNSのAレコードがVPSのIPか、80/443が開いているか(VPS会社のFWも)、`DOMAIN` の綴り |
| 管理画面で「Discordへの反映に失敗」 | BOT招待時に `applications.commands` を選んだか、`GUILD_ID` が正しいか。招待し直して再度ON |
| `/exchange` が候補に出ない | ONにした直後は数秒待つ。Discordを再読み込み。BOTがそのチャンネルを見られる権限(View Channels)があるか |
| パスワードを変えたい | `.env` の `ADMIN_PASSWORD` を直して `docker compose up -d` |
