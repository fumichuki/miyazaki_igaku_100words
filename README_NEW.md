# 英作文特訓システム - 鹿児島大学版

鹿児島大学の英作文問題に特化したWebサービスです。GPT-4oを使用して、高品質な問題生成と添削を提供します。

## 🎯 主な機能

### 1. 鹿児島大学特化の問題生成
- 口語的な日本語（〜だよ/〜ね）を含む短文問題
- 主語の補いが必要な自然な英訳が求められる問題
- テーマの重複を自動回避（直近10問）

### 2. 詳細な添削と採点
- **5項目評価**（各5点満点、合計25点）
  - 内容点: 日本文の意味を正確に伝えているか
  - 構成点: 文の流れが自然で論理的か
  - 語彙点: 適切で自然な語彙選択ができているか
  - 文法点: 文法的に正しいか
  - 語数点: 目標語数に収まっているか

- **添削ポイント解説**
  - 語数100語未満: 最低5項目
  - 語数100語以上: 最低10項目
  - 修正前→修正後の対比表示
  - 修正理由を日本語で明確に説明
  - 別の表現の提案

### 3. 見やすい結果表示
- あなたの英文 vs 修正版の並列表示
- 採点表（項目別スコアとコメント）
- 文法・表現のポイント解説（番号付き）

### 4. データ管理
- SQLiteデータベースで問題・提出履歴を管理
- 統計情報の取得（平均スコア、最高スコアなど）
- 既出テーマの記録と回避

## 🚀 セットアップ

### 1. 環境準備
```bash
# 依存パッケージをインストール
pip install -r requirements.txt
```

### 2. 環境変数の設定
`.env`ファイルを作成して、OpenAI APIキーを設定：
```bash
OPENAI_API_KEY=your_openai_api_key_here
PORT=8002
```

### 3. サーバー起動
```bash
python app.py
```

ブラウザで `http://localhost:8002` を開きます。

## 📋 API仕様

### POST /api/question
**問題を生成**

**Request:**
```json
{
  "difficulty": "intermediate",
  "excluded_themes": ["環境問題", "技術"]
}
```

**Response:**
```json
{
  "question_id": "q_20260116123456",
  "theme": "週休3日制",
  "japanese_sentences": ["...", "..."],
  "hints": [
    {"en": "workload", "ja": "仕事量", "kana": "しごとりょう"}
  ],
  "target_words": {"min": 80, "max": 120},
  "model_answer": "...",
  "alternative_answer": "...",
  "common_mistakes": ["..."]
}
```

### POST /api/correct
**英作文を添削**

**Request:**
```json
{
  "question_id": "q_20260116123456",
  "japanese_sentences": ["...", "..."],
  "user_answer": "If we have one more day off...",
  "target_words": {"min": 80, "max": 120}
}
```

**Response:**
```json
{
  "submission_id": "s_20260116123456789",
  "original": "...",
  "corrected": "...",
  "word_count": 58,
  "score": {
    "content": 5,
    "structure": 4,
    "vocabulary": 4,
    "grammar": 4,
    "word_count_penalty": 5
  },
  "total": 22,
  "comments": {
    "content": "...",
    "structure": "...",
    "vocabulary": "...",
    "grammar": "...",
    "word_count_penalty": "..."
  },
  "points": [
    {
      "before": "one more day off",
      "after": "an additional day off",
      "reason": "...",
      "alt": "another day off"
    }
  ]
}
```

### GET /api/history?limit=50
**提出履歴を取得**

### GET /api/statistics
**統計情報を取得**

## 🧪 テスト

```bash
# テストを実行
pytest test_models.py -v

# すべてのテストを実行
pytest -v
```

## 📂 ファイル構成

```
eisakubun-kagoshima/
├── app.py                  # Flaskアプリケーション
├── models.py               # Pydanticモデル定義
├── llm_service.py          # OpenAI API呼び出しとリトライ処理
├── database.py             # SQLiteデータベース管理
├── test_models.py          # テスト
├── requirements.txt        # 依存パッケージ
├── .env.example            # 環境変数の例
├── data/                   # データディレクトリ
│   ├── kagoshima_eisakubun.db  # SQLiteデータベース
│   └── past_questions.json     # 過去問データ（レガシー）
├── static/                 # 静的ファイル
│   ├── main.js             # フロントエンドJavaScript
│   └── style.css           # CSS
└── templates/              # HTMLテンプレート
    └── index.html          # メインページ
```

## 🎓 鹿児島大学の英作文問題の特徴

1. **口語的な日本語**
   - 「〜だよ」「〜ね」「〜かもしれない」などの表現
   - 自然な会話風の文体

2. **主語の補い**
   - 日本語では省略されている主語を英語で明示する必要がある
   - we / people / it などの適切な主語選択が重要

3. **直訳の回避**
   - 直訳では不自然になる表現が多い
   - 自然な英語表現への変換能力が評価される

4. **短文構成**
   - 2〜4文程度の短い問題
   - 各文が独立しているが、全体で一つのテーマを形成

## 💡 技術スタック

- **Backend**: Flask + Python 3.11+
- **AI**: OpenAI GPT-4o
- **Validation**: Pydantic 2.10+
- **Database**: SQLite3
- **Frontend**: Vanilla JavaScript + CSS
- **Testing**: pytest

## 📊 品質保証

### JSONスキーマの厳格な管理
- Pydanticによる型チェックとバリデーション
- LLM出力の自動リトライ（最大3回）
- 不正なJSON形式の自動修正

### テストカバレッジ
- モデルバリデーションテスト
- スコア計算の正確性テスト
- 鹿児島大学風の問題フォーマットテスト
- 境界値テスト

## 📝 今後の拡張予定

- [ ] ユーザー認証機能
- [ ] 学習履歴のグラフ表示
- [ ] 弱点分析機能
- [ ] 模範解答の音声読み上げ
- [ ] 他大学の問題形式への対応

## 📄 ライセンス

MIT License

## 👥 開発者

GitHub Copilot + Human Collaboration

---

**🚀 さあ、英作文の特訓を始めましょう！**
