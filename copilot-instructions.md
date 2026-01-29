# Copilot指示書 - 宮崎大学医学部 英作文特訓システム

## プロジェクト概要
- **プロジェクト名**: 宮崎大学医学部 英作文特訓講座（100字指定）
- **サービス名**: みや塾 英作文特訓講座 宮崎大学医学部（100字指定）
- **対象**: 宮崎大学医学部受験生
- **形式**: 100字指定の英作文問題

## システム構成
- **Backend**: Flask + OpenAI 減点されるほどの修正がない場合はユーザの英文は正解とする。もっといい表現などがあれば、解説で紹介する。
減点されるほどの修正がない場合はユーザの英文は正解とする。もっといい表現などがあれば、解説で紹介する。
PT-4o
- **Frontend**: Vanilla JavaScript
- **Database**: SQLite (miyazaki_igaku_eisakubun.db)
- **Port**: 8001
- **Host**: 0.0.0.0

## 重要な設定
### ポート番号
- **開発環境**: 8001
- **本番環境**: 8001 (環境変数 `PORT` で変更可能)

### データベース
- **ファイル名**: `data/miyazaki_igaku_eisakubun.db`
- **過去問JSON**: `data/past_questions.json`

### 環境変数
- `OPENAI_API_KEY`: OpenAI APIキー（必須）
- `PORT`: サーバーポート（デフォルト: 8001）
- `DEBUG`: デバッグモード（デフォルト: true）

## 大学名の扱い
### 表示名
- **日本語**: 宮崎大学医学部
- **英語**: Miyazaki University School of Medicine
- **略称**: 宮崎医学部

### 避けるべき表現
- ❌ 鹿児島大学
- ❌ kagoshima
- ❌ 九州大学
- ❌ kyudai

## コーディング規約
### ファイル命名
- データベース: `miyazaki_igaku_*`
- 設定ファイル: `config.py`, `.env`
- スクリプト: `*_server.sh`

### コメント
- 全てのPythonファイルの先頭に以下を記載:
```python
"""
[モジュール名]
宮崎大学医学部英作文特訓システム
"""
```

### ポート番号の参照
- 常に `config.PORT` から取得
- ハードコードしない

## Git管理
### リモートリポジトリ
- **GitHub URL**: https://github.com/fumichuki/miyazaki_igaku_100words
- **ブランチ**: main

### 重要: 絶対に避けること
⚠️ **このプロジェクトは kagoshima_100words からコピーされました**

#### ❌ 絶対にやってはいけないこと
1. **kagoshima_100words リポジトリに push しない**
2. 鹿児島大学関連の文言を残さない
3. ポート8002を使用しない

#### ✅ 正しいリポジトリ
- `https://github.com/fumichuki/miyazaki_igaku_100words`

## デプロイ時の確認事項
### 変更が必要なファイル
- [x] config.py (APP_NAME, PORT, DB_PATH)
- [x] database.py (DB_PATH)
- [x] llm_service.py (大学名)
- [x] templates/index.html (タイトル、ヘッダー)
- [x] *.sh (ポート番号)
- [x] .env (PORT)
- [x] README.md (プロジェクト名、ポート)

### チェックリスト
- [ ] ポート8001で起動できるか
- [ ] 大学名が全て「宮崎大学医学部」になっているか
- [ ] データベースが`miyazaki_igaku_eisakubun.db`に設定されているか
- [ ] GitHubリポジトリが正しいか確認

## 開発コマンド
```bash
# サーバー起動
bash start_server.sh

# サーバー再起動
bash restart_server.sh

# サーバー停止
bash stop_server.sh

# サーバー状態確認
bash check_server.sh
```

## アクセスURL
- **開発環境**: http://localhost:8001
- **本番環境**: (環境により異なる)

## 参考資料
- [DEPLOY.md](DEPLOY.md) - デプロイ手順
- [README.md](README.md) - プロジェクト概要
