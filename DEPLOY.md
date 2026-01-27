# 🚀 Renderデプロイ手順

## 📋 前提条件
- Render Professional プラン契約済み ($19/月)
- GitHubアカウント
- OpenAI API Key

## 🔧 デプロイ手順

### 1️⃣ GitHubリポジトリの準備

```bash
# Gitリポジトリ初期化（まだの場合）
git init
git add .
git commit -m "Initial commit: Kagoshima Eisakubun System"

# GitHubにリポジトリを作成してプッシュ
git remote add origin https://github.com/YOUR_USERNAME/kagoshima_general.git
git branch -M main
git push -u origin main
```

### 2️⃣ Renderでサービス作成

1. [Render Dashboard](https://dashboard.render.com/) にログイン
2. **New** → **Web Service** をクリック
3. GitHubリポジトリを接続
4. 以下の設定を入力：

| 項目 | 値 |
|-----|-----|
| **Name** | `kagoshima-eisakubun` |
| **Region** | `Oregon (US West)` または `Singapore (East Asia)` |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn -c gunicorn_config.py app:app` |
| **Plan** | **Starter** ($19/月) |

### 3️⃣ 環境変数の設定

Render Dashboard の **Environment** セクションで以下を追加：

```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxx
FLASK_ENV=production
PYTHON_VERSION=3.11.0
```

### 4️⃣ ディスク永続化の設定

**Settings** → **Disks** で新規ディスクを追加：

| 項目 | 値 |
|-----|-----|
| **Name** | `data` |
| **Mount Path** | `/opt/render/project/src/data` |
| **Size** | `1 GB` |

### 5️⃣ デプロイ開始

**Manual Deploy** → **Deploy latest commit** をクリック

ビルドログを確認し、以下が表示されればデプロイ成功：

```
==> Starting service with 'gunicorn -c gunicorn_config.py app:app'
[INFO] Booting worker...
```

### 6️⃣ 動作確認

デプロイされたURLにアクセス（例: `https://kagoshima-eisakubun.onrender.com`）

---

## 🔍 トラブルシューティング

### デプロイが失敗する場合

1. **Build failed**
   - requirements.txt の依存関係を確認
   - Python バージョンを確認（3.11.0 推奨）

2. **Application timeout**
   - gunicorn_config.py の `timeout` を確認（現在120秒）
   - OpenAI API の応答時間が長い可能性

3. **Database error**
   - Disk が正しくマウントされているか確認
   - `/opt/render/project/src/data` にアクセス権があるか確認

### ログの確認

Render Dashboard → **Logs** で以下を確認：

```bash
# アプリケーションログ
tail -f /var/log/render/app.log

# エラーログ
tail -f /var/log/render/error.log
```

---

## 📊 本番運用チェックリスト

- [ ] OpenAI API使用量をモニタリング
- [ ] Render Professional プラン課金確認
- [ ] データベースバックアップ（定期的に）
- [ ] SSL証明書の確認（Render自動）
- [ ] カスタムドメインの設定（必要に応じて）

---

## 💰 コスト概算

| 項目 | 月額コスト |
|-----|---------|
| Render Professional | $19 |
| OpenAI API (4-5人 × 2時間/日) | $10-20 |
| **合計** | **$29-39** |

---

## 🎓 受験生へのURL案内

デプロイ完了後、以下のURLを受験生に案内：

```
https://kagoshima-eisakubun.onrender.com
```

> **✅ Professional プラン利用により、スリープなし・即座にアクセス可能**
