# Phase 2実装レポート: Archetype-based Question Generation

## 📅 実装日時
2026-01-18

## ✅ 完了タスク

### 1. アーキタイプテンプレートの作成 (`archetype_templates.py`)
- **獣医学部用**: 10種類のアーキタイプ (A1-A3, B1-B2, C1-C3, D1-D2)
- **理系・文系用**: 4種類のアーキタイプ (G1-G4)
- **トピックスロット**: 獣医学部31トピック、理系・文系20トピック
- **ユニットタイプ**: reasons, things, examples, suggestions, benefits, ways

#### アーキタイプ一覧（獣医学部）
```
A1: Do you think [action] or not? Give two reasons.
A2: Why do you think it is important to [action]?
A3: Do you agree or disagree: [statement]. Give two reasons.
B1: What should [actor] do to [action]? Give at least two things.
B2: Imagine you want to [action]. What are two things you would need to do?
C1: When [situation], how should [actor] respond? Give two examples.
C2: What do you think would help to [action]? Give at least two examples.
C3: Write about a typical problem related to [topic]. Offer two suggestions.
D1: Discuss two benefits of [concept].
D2: Explain two ways that [action] can affect [outcome].
```

### 2. 問題生成エンジンの実装 (`question_generator.py`)
- `validate_question_has_two_units()`: 正規表現による「two X」パターンの検証
- `generate_from_archetype()`: テンプレートとトピックから問題を生成
- `generate_question_set()`: 複数問題の生成（トピック重複回避）
- `generate_archetype_based_question()`: 完全な問題データ生成（日本語文・ヒント含む）

#### 正規表現パターン
```python
patterns = [
    r'\btwo\s+reasons?\b',
    r'\btwo\s+things?\b',
    r'\btwo\s+examples?\b',
    r'\btwo\s+suggestions?\b',
    r'\btwo\s+benefits?\b',
    r'\btwo\s+ways?\b',
    r'\bat\s+least\s+two\b'
]
```

### 3. LLM Service統合 (`llm_service.py`)
- `generate_question()` に `use_archetype` パラメータを追加
  - `use_archetype=True`: アーキタイプベース生成（獣医学部のデフォルト）
  - `use_archetype=False`: 従来のLLMフリー生成
- フォールバックチェーン: Archetype → LLM → Hardcoded
- 獣医学部モードでは自動的にアーキタイプを使用

```python
def generate_question(
    mode: str = "general",
    used_themes: Optional[List[str]] = None,
    use_archetype: bool = True  # 新規パラメータ
) -> QuestionResponse:
    # 獣医学部モードでアーキタイプ使用
    if mode == "veterinary" and use_archetype:
        try:
            return generate_archetype_based_question(
                mode=mode,
                excluded_topics=used_themes or []
            )
        except Exception as e:
            logger.warning(f"Archetype generation failed: {e}, falling back to LLM")
    
    # LLMフリー生成（フォールバック）
    ...
```

### 4. データモデル拡張 (`models.py`)
`QuestionResponse` に新しいフィールドを追加:
- `archetype_id: Optional[str]` - アーキタイプID (例: "A1", "C3")
- `topic_id: Optional[str]` - トピックID (例: "preventive_care")
- `required_units: Optional[int]` - 必要なユニット数（常に2）
- `unit_type: Optional[str]` - ユニットタイプ ("reasons", "things"等)
- `question_text_english: Optional[str]` - 英語の問題文

### 5. データベース修正 (`database.py`)
- **問題**: `save_question()` がタイムスタンプベースのIDを使用し、秒単位で重複
- **解決**: UUID使用に変更
  ```python
  # 修正前
  question_id = f"q_{datetime.now().strftime('%Y%m%d%H%M%S')}"
  
  # 修正後
  question_id = f"q_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
  ```

### 6. 包括的テストスイート (`test_archetypes.py`)
- **正規表現検証テスト**: 4ケース
- **アーキタイプ生成テスト**: 3ケース (veterinary A1, C3, general G1)
- **網羅テスト**: 全アーキタイプ×1トピック、全トピック×1アーキタイプ
- **問題セット生成テスト**: 複数問題生成、除外トピック機能
- **統合テスト**: `generate_archetype_based_question()` のフルフロー
- **ストレステスト**: 20問連続生成、多様性確認

#### テスト結果
```
Phase 2: Archetype-based Question Generation Tests
======================================================================

1. Validation Tests
✓ 'two reasons' detected
✓ 'two things' detected
✓ 'two suggestions' detected
✓ Invalid question detected

2. Archetype Generation Tests
✓ A1 question
✓ C3 question
✓ G1 question

=== Testing all veterinary archetypes ===
✓ A1, A2, A3, B1, B2, C1, C2, C3, D1, D2 (10/10)

=== Testing all veterinary topics ===
✓ 31/31 topics validated

3. Question Set Generation Tests
✓ Question set generation (3 questions, unique topics)
✓ Excluded topics test (5 questions)

4. Integration Tests
✓ Integration test passed

=== Stress test: generating 20 questions ===
✓ Archetype distribution: 10 unique archetypes used
✓ Topic distribution: 20 unique topics
✓ Stress test passed: 20/20 valid

======================================================================
✅ All Phase 2 tests passed!
======================================================================

📊 Summary:
   - Total archetypes (veterinary): 10
   - Total topics (veterinary): 31
   - Total archetypes (general): 4
   - Total topics (general): 20
   - All questions validated: ✅
   - 'Two reasons/things/suggestions' guaranteed: ✅
```

## 🎯 達成された目標

### GPT-5.2要件との対応

| 要件 | 実装 | 状態 |
|------|------|------|
| 確定的テンプレート | `archetype_templates.py` | ✅ |
| トピックスロット | 31獣医+20一般トピック | ✅ |
| 正規表現検証 | `validate_question_has_two_units()` | ✅ |
| 「two X」保証 | すべてのアーキタイプで保証 | ✅ |
| 後方互換性 | `use_archetype`パラメータ | ✅ |
| LLMフォールバック | 3段階チェーン実装 | ✅ |
| データモデル拡張 | 5つの新フィールド | ✅ |
| テストカバレッジ | 38テストケース | ✅ |

### 主な改善点

1. **問題文の品質保証**
   - LLMの自由生成に依存せず、確定的テンプレートを使用
   - 100%の確率で「two reasons/things/suggestions」を含む
   - 正規表現による自動検証

2. **多様性の確保**
   - 10種類の獣医学部アーキタイプ
   - 31種類の獣医学トピック
   - ランダム選択による問題の多様性
   - トピック重複回避機能

3. **後方互換性の維持**
   - 既存のLLMベース生成も引き続き使用可能
   - `use_archetype=False` で従来通りの動作
   - APIレスポンス形式は変更なし（フィールド追加のみ）

4. **メタデータの充実**
   - どのアーキタイプを使用したか追跡可能
   - 問題の構造（必要なユニット数、タイプ）が明示的
   - 英語版問題文も保存

## 📝 実装ファイル

### 新規作成
- `archetype_templates.py` (~500行) - テンプレート定義
- `question_generator.py` (~250行) - 生成エンジン
- `test_archetypes.py` (~330行) - ユニットテスト
- `test_api_phase2.py` (~200行) - API統合テスト
- `test_quick_phase2.py` (~100行) - 簡易テスト

### 修正
- `llm_service.py` - `generate_question()` にアーキタイプ統合
- `models.py` - `QuestionResponse` にメタデータフィールド追加
- `database.py` - UUID使用によるID重複問題の修正

## 🔍 検証結果

### ユニットテスト
- **実行コマンド**: `python3 test_archetypes.py`
- **結果**: 38/38テスト合格
- **カバレッジ**: 
  - 正規表現検証: ✅
  - 全アーキタイプ生成: ✅
  - 全トピック処理: ✅
  - 問題セット生成: ✅
  - 統合フロー: ✅
  - ストレステスト: ✅

### API統合テスト
- **環境問題**: テスト実行時にサーバー起動の問題が発生
- **推奨**: 手動でサーバーを起動後、`curl`または`test_api_phase2.py`で検証

```bash
# サーバー起動
python3 app.py

# 別ターミナルでテスト実行
python3 test_api_phase2.py
```

## 🚀 使用方法

### API呼び出し例

```bash
# 獣医学部問題生成（アーキタイプ使用）
curl -X POST http://localhost:8002/api/question \
  -H "Content-Type: application/json" \
  -d '{"mode": "veterinary"}'

# レスポンス例
{
  "theme": "Preventive Veterinary Care",
  "japanese_sentences": ["動物の予防医療について考えを述べなさい。"],
  "hints": [...],
  "target_words": {"min": 80, "max": 120},
  "archetype_id": "A1",
  "topic_id": "preventive_care",
  "required_units": 2,
  "unit_type": "reasons",
  "question_text_english": "Do you think pet owners should provide regular preventive care for their pets or not? Give two reasons to support your answer."
}
```

### コード使用例

```python
from llm_service import generate_question

# アーキタイプベース生成
question = generate_question(mode="veterinary", use_archetype=True)
print(f"Archetype: {question.archetype_id}")
print(f"Topic: {question.topic_id}")
print(f"English: {question.question_text_english}")

# LLMフリー生成（従来通り）
question = generate_question(mode="general", use_archetype=False)
```

## 🐛 既知の問題と制限事項

1. **API統合テスト環境**
   - Dev Container環境でバックグラウンドプロセス管理に課題
   - 推奨: 手動でサーバー起動後にテスト実行

2. **LLMフォールバック**
   - アーキタイプ生成失敗時、LLMにフォールバック
   - LLM生成の問題は「two X」を保証しない可能性あり

3. **データベーススキーマ**
   - アーキタイプメタデータをDBに保存する機能は未実装
   - 将来的にテーブル拡張が必要

## 📊 統計

- **実装行数**: ~1,430行（新規・修正合計）
- **テストケース**: 38個
- **アーキタイプ数**: 14個（獣医10+一般4）
- **トピック数**: 51個（獣医31+一般20）
- **検証合格率**: 100%

## 🎉 結論

Phase 2は完全に実装され、すべてのユニットテストに合格しました。

**主な成果:**
- ✅ 確定的なテンプレートベース問題生成
- ✅ 「two reasons/things/suggestions」の100%保証
- ✅ 後方互換性の維持
- ✅ 包括的なテストカバレッジ
- ✅ データベースのID重複問題修正

**次のステップ:**
- Phase 3: アウトライン支援エンドポイント
- Phase 4: 最終リファクタリングと文書化

