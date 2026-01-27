# 英作文特訓システム - 鹿児島大学版

## 特徴
- **GPT-4o**搭載で高品質な添削
- 大学過去問の類似問題生成
- AI添削（文法・表現・内容）
- 鹿児島大学の英作文対策に最適化

## 技術スタック
- **Backend**: Flask + OpenAI GPT-4o
- **Frontend**: Vanilla JS + Bootstrap

## セットアップ

### 1. 環境変数設定
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### 2. パッケージインストール
```bash
pip install -r requirements.txt
```

### 3. サーバー起動
```bash
python app.py
```

→ http://localhost:8002 でアクセス

## 九州大学版との違い
| 項目 | 九州大学版 | 鹿児島大学版 |
|------|-----------|-------------|
| AIモデル | GPT-4o | GPT-4o |
| ポート | 8001 | 8002 |
| テーマカラー | グリーン | パープル |
| 過去問データ | 九州大学 | 鹿児島大学 |

## API仕様

### 問題生成
```
POST /api/generate-question
Body: {"question_id": 1}
```

### 添削
```
POST /api/grade
Body: {
  "question": "問題文",
  "answer": "ユーザー回答",
  "reference_answer": "模範解答（任意）"
}
```
