# 問題点の詳細分析：model_answer_explanation生成エラー

## 1. 問題の概要

### 現在の症状
```
💡 文法・表現のポイント解説（1項目）
1
💡 学生の表現
→
✅ より良い表現
添削処理中にエラーが発生しました。再度お試しください。
```

### 期待される出力
```
💡 文法・表現のポイント解説（3項目）

1文目: John's job was to investigate the identity of people who died lonely deaths and to conduct their funerals.
（ジョンの仕事は、孤独死した人の身元を調査し、葬儀を執り行うことだった。）
investigate（動詞：詳細に調査する）／identify（動詞：身元を特定する）で、investigateは調査プロセス全体、identifyは特定の結果を指します。
例：Police investigate crimes.「警察は犯罪を調査する。」／They identified the suspect.「彼らは容疑者を特定した。」

2文目: I was deeply moved by his meticulous work.
（彼の丁寧な仕事ぶりに胸を打たれた。）
meticulous（形容詞：細部にまで気を配る）／careful（形容詞：注意深い）で、meticulousは非常に注意深く細部にまでこだわること、carefulは全体的な注意を指します。
例：She is meticulous about her work.「彼女は仕事に細心の注意を払っている。」／He is careful when driving.「彼は運転時に注意深い。」

3文目: The expression on John's face was comforting.
（主人公の表情が心地よかった。）
expression（名詞：表情）／emotion（名詞：感情）で、expressionは外見に表れるもの、emotionは内面にあるものを指します。
例：Her expression was one of surprise.「彼女の表情は驚きそのものだった。」／He couldn't hide his emotions.「彼は感情を隠せなかった。」
```

---

## 2. 問題の発生箇所

### 現在の実装フロー
```
1. ユーザーが英文を提出
2. llm_service.py の correct_answer() が呼ばれる
3. 添削プロンプト（CORRECTION_PROMPT_MIYAZAKI_TRANSLATION）でLLM呼び出し
   → JSON応答: {original, corrected, word_count, points}
4. 模範解答プロンプト（MODEL_ANSWER_PROMPT_MIYAZAKI_TRANSLATION）でLLM呼び出し
   → JSON応答: {model_answer, model_answer_explanation}
5. 2つの応答を結合してフロントエンドに返す
```

### 問題が発生するステップ
- **ステップ4**: 模範解答生成でエラーが発生
- `model_answer_explanation`が正しく生成されず、フォールバック応答になっている
- フォールバック応答:
  ```json
  {
    "before": "学生の表現",
    "after": "より良い表現",
    "reason": "添削処理中にエラーが発生しました。再度お試しください。",
    "level": "💡改善提案"
  }
  ```

---

## 3. 根本原因の分析

### 原因1: プロンプトの問題
- `MODEL_ANSWER_PROMPT_MIYAZAKI_TRANSLATION`が古い形式のまま
- prompts_translation_simple.pyで簡潔化したのは`CORRECTION_PROMPT`のみ
- `MODEL_ANSWER_PROMPT`は元のprompts_translation.pyから使用しているため、長すぎる可能性
- **結果**: LLMが適切なJSON応答を生成できない

### 原因2: JSON応答の不一致
- 模範解答生成が失敗し、JSONパースエラー
- clean_json_response()でクリーンアップしても修正できない形式
- llm_service.pyの_generate_fallback_correction()が呼ばれている

### 原因3: model_answer_explanationの形式指定が不明確
- 現在のプロンプトでは「文法・表現のポイント解説」の形式が詳細に指定されていない
- kagoshima風の形式（単語比較、【参考】、例文2つ）が指定されていない
- **期待される形式**:
  ```
  N文目: [英文]
  （[日本語訳]）
  [語A]（品詞：意味：文脈）／[語B]（品詞：意味：文脈）で、[違いの説明]。
  【参考】[文法パターン]
  例：[例文1]「[日本語訳1]」／[例文2]「[日本語訳2]」
  ```

---

## 4. 現在のコード構造

### llm_service.py の correct_answer() 関数
```python
# Line 1217: 添削実行
response = call_openai_with_retry(correction_prompt, is_model_answer=True)

# Line 1260-1280: 模範解答生成
model_answer_prompt = prompts['model_answer'].format(
    question_text=question_text,
    user_answer=normalized_answer,
    word_count=word_count
)
model_response = call_openai_with_retry(model_answer_prompt, is_model_answer=True)
```

### 問題点
1. `prompts['model_answer']`が存在しない（prompts_translation_simple.pyで定義していない）
2. 元のprompts_translation.pyから読み込もうとするが、そこでも適切に定義されていない
3. 模範解答生成のプロンプトが適切に機能していない
4. model_answer_explanationの形式指定が不十分

---

## 5. 懸念事項と柔軟な対応

### 懸念1: ユーザが日本語4文に対して3文を送信する場合
- **シナリオ**: 日本語原文は4文あるが、ユーザーは3文に要約して提出
- **対応**: ピリオド区切りで実際の英文数を判定し、その数だけ解説を生成
- **実装**: `sentences = [s.strip() for s in user_answer.split('.') if s.strip()]`

### 懸念2: 日本語2文を、whichなどで1文として記載し送信する場合
- **シナリオ**: 
  - 日本語: 「Aがある。それはBである。」
  - 英文: 「There is A, which is B.」（1文に統合）
- **対応**: 
  - 実際の英文のピリオド数で判定（この場合1文）
  - 1文として解説を生成
  - 日本語原文2文分の内容を含んでいることを認識

### 基本方針
**ピリオド区切りで英文を分解し、各英文ごとに解説を生成する**

---

## 6. 理想的な実装方針

### 新しいプロンプト設計
```python
MODEL_ANSWER_EXPLANATION_PROMPT = """
あなたは和文英訳の文法・表現解説の専門家です。

【出力形式】
学生が提出した英文を1文ずつ解説してください。

**必須要件**:
1. 各文ごとに番号を付ける（1文目:、2文目:、3文目:）
2. 各文の日本語訳を（）内に記載
3. 重要な語彙・文法を1つ選んで比較解説
4. 【参考】セクションで文法パターンを記載
5. 例文を2つ記載

**解説フォーマット（厳守）**:
```
N文目: [英文]
（[日本語訳]）
[語A]（品詞：意味：文脈）／[語B]（品詞：意味：文脈）で、[違いの説明]。
【参考】[文法パターン]
例：[例文1]「[日本語訳1]」／[例文2]「[日本語訳2]」
```

**解説例**:
```
1文目: The participants were divided into two groups.
（参加者は2つのグループに分けられた。）
divide（動詞：分ける・分割する：物や人を複数に分ける文脈）／split（動詞：分割する・分裂する：より具体的に分ける動作の文脈）で、divideは一般的な分割を示し、splitはしばしば物理的に分けることを指します。
【参考】divide A into B（AをBに分ける）／split A into B（AをBに分ける）
例：The teacher divided the class into two groups.「先生はクラスを2つのグループに分けた。」／They split the class into two groups.「彼らは（ぱっと）クラスを2つに分けた。」
```

学生の英文:
{user_answer}

日本語原文:
{question_text}

上記のフォーマットで、各文を解説してください。
"""
```

### 実装フロー
```python
# 1. 英文をピリオドで分解
sentences = [s.strip() for s in user_answer.split('.') if s.strip()]
sentence_count = len(sentences)

# 2. 解説生成プロンプトを作成
explanation_prompt = MODEL_ANSWER_EXPLANATION_PROMPT.format(
    user_answer=user_answer,
    question_text=question_text,
    sentence_count=sentence_count
)

# 3. LLM呼び出し（テキスト形式で返す、JSONではない）
explanation_text = call_openai_with_retry(explanation_prompt, is_model_answer=False)

# 4. テキストをそのまま返す
return {
    "model_answer_explanation": explanation_text,
    # ... 他のフィールド
}
```

---

## 7. 具体的な問題点のまとめ

| 項目 | 現状 | 期待 | 優先度 |
|------|------|------|--------|
| model_answer_explanation生成 | フォールバックエラー | kagoshima風の詳細解説 | 🔴 最高 |
| プロンプトの場所 | prompts_translation.py（長すぎ） | prompts_translation_simple.pyに簡潔版を追加 | 🔴 最高 |
| 文数対応 | 固定的 | 柔軟（3文でも4文でも対応） | 🟡 高 |
| 解説形式 | 不明確 | 単語比較、【参考】、例文2つ | 🔴 最高 |
| エラーハンドリング | 汎用的なフォールバック | 適切なエラーメッセージ | 🟡 高 |
| JSON vs テキスト | JSONで返そうとして失敗 | テキスト形式で返す方が安全 | 🔴 最高 |

---

## 8. 修正すべきファイル

### 1. prompts_translation_simple.py
- **追加**: `MODEL_ANSWER_EXPLANATION_PROMPT`を新規作成
- **形式**: テキスト形式の出力を明確に指定
- **柔軟性**: 文数に依存しない設計

### 2. llm_service.py
- **修正箇所**: `correct_answer()` 関数の模範解答生成部分
- **変更点**:
  - 英文をピリオドで分解
  - 新しいプロンプトを使用
  - JSON応答ではなくテキスト応答を期待
  - エラーハンドリングの改善

### 3. models.py（必要に応じて）
- `CorrectionResponse`モデルの確認
- `model_answer_explanation`フィールドの型確認（str型であることを確認）

---

## 9. 実装の詳細設計

### Step 1: prompts_translation_simple.pyに新プロンプトを追加
```python
MODEL_ANSWER_EXPLANATION_PROMPT = """
あなたは和文英訳の文法・表現解説の専門家です。

【重要】以下のフォーマットで、学生が提出した英文を1文ずつ解説してください。

**解説フォーマット（厳守）**:
```
N文目: [英文そのまま]
（[日本語訳]）
[語A]（品詞：意味）／[語B]（品詞：意味）で、[違いの説明]。
【参考】[文法パターンや使い分けのヒント]
例：[例文1]「[日本語訳1]」／[例文2]「[日本語訳2]」
```

**必須ルール**:
1. 学生の英文をピリオド（.）で区切って、実際の文数を数える
2. 各文に対して上記フォーマットで解説を作成
3. 語彙は重要なものを1つ選び、類似語と比較
4. 【参考】には文法パターンや使い分けを記載
5. 例文は必ず2つ、日本語訳付きで記載

学生の英文:
{user_answer}

日本語原文（参考）:
{question_text}

上記のフォーマットで解説を生成してください。JSONではなく、プレーンテキストで出力してください。
"""
```

### Step 2: llm_service.pyの修正
```python
# correct_answer() 関数内

# 模範解答の解説を生成
try:
    # 英文を分解して文数を確認
    sentences = [s.strip() for s in normalized_answer.split('.') if s.strip()]
    sentence_count = len(sentences)
    
    logger.info(f"Generating explanation for {sentence_count} sentences")
    
    # 解説生成プロンプト
    explanation_prompt = MODEL_ANSWER_EXPLANATION_PROMPT.format(
        user_answer=normalized_answer,
        question_text=question_text
    )
    
    # LLM呼び出し（テキスト形式）
    explanation_response = call_openai_with_retry(
        explanation_prompt, 
        is_model_answer=False  # JSON形式を期待しない
    )
    
    model_answer_explanation = explanation_response.strip()
    
except Exception as e:
    logger.error(f"Failed to generate explanation: {e}")
    model_answer_explanation = "文法・表現のポイント解説の生成中にエラーが発生しました。"
```

---

## 10. テストケース

### ケース1: 正常（4文 → 4文）
- **日本語**: 4文の原文
- **英文**: 4文の翻訳
- **期待**: 4つの解説

### ケース2: 要約（4文 → 3文）
- **日本語**: 4文の原文
- **英文**: 3文に要約
- **期待**: 3つの解説（各文が複数の日本語内容を含む）

### ケース3: 統合（2文 → 1文）
- **日本語**: 「Aがある。それはBである。」
- **英文**: "There is A, which is B."
- **期待**: 1つの解説（whichで統合されたことを認識）

---

## 11. 次のアクションステップ

### 優先順位1（即実行）
1. ✅ `prompts_translation_simple.py`に`MODEL_ANSWER_EXPLANATION_PROMPT`を追加
2. ✅ `llm_service.py`の`correct_answer()`関数を修正
3. ✅ サーバーを再起動してテスト

### 優先順位2（検証）
1. 正常ケース（4文→4文）でテスト
2. 要約ケース（4文→3文）でテスト
3. 統合ケース（2文→1文）でテスト
4. エラーケースでフォールバックを確認

### 優先順位3（最適化）
1. プロンプトの微調整（必要に応じて）
2. エラーメッセージの改善
3. デバッグログの追加

---

## 12. 参考：kagoshimaの成功例

kagoshima_100wordsでは、`model_answer_explanation`が正しく生成されている理由:
1. プロンプトが簡潔で明確
2. テキスト形式の出力を期待
3. JSONではなく、直接テキストを返す
4. 文数に柔軟に対応

miyazakiでも同様のアプローチを採用すべき。

---

## 結論

**問題の本質**: 
模範解答の解説生成プロンプトが長すぎ＋形式が不明確 → LLMがJSON生成に失敗 → フォールバック

**解決策**: 
新しい簡潔なプロンプトを作成し、テキスト形式で出力させる。文数は動的に判定。

**実装方針**: 
prompts_translation_simple.pyに新プロンプト追加 + llm_service.py修正 → テスト
