# 新規バグレポート：プロンプトフォーマットエラー

## 📌 発生日時
2026-01-29 02:09:39

## 🚨 問題の概要

品質修正実装後、実際の英文でテストしたところ、以下のエラーが発生：

```
KeyError: '\n  "before"'
```

**結果:**
- 「添削処理中にエラーが発生しました」
- 💡 文法・表現のポイント解説（0項目）

---

## 📋 再現手順

### テストケース
- **テーマ**: 時事
- **日本語原文**: 3文
  ```
  日本では、ワクチン接種が進んでいるにもかかわらず、一部の地域で感染者数が再び増加している。
  特に都市部では、人々の移動が活発になることで感染拡大のリスクが高まっている。
  この状況により、医療機関の負担がさらに増していることが懸念されている。
  ```

- **ユーザーの英文**: 43 words（途中まで入力）
  ```
  Even though vaccination has been progressing in Japan, the number of infected people has started to rise again in some regions. This is especially true in urban areas, where increased movement and travel among people heighten the risk of further spread. There are
  ```

- **required_points**: 3（正常に計算された）

---

## 🔍 エラーログ分析

### エラー発生箇所

```python
File "/workspaces/miyazaki_igaku_100words/llm_service.py", line 1259, in correct_answer
    correction_prompt = prompts['correction'].format(
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
KeyError: '\n  "before"'
```

### エラーの原因

`prompts['correction'].format()` で、プロンプトテンプレート内の `{...}` がフォーマット対象として認識されている。

**問題のあるプロンプト箇所:**
```python
【出力形式（必須）】
```json
{{
  "points": [
    {{
      "before": "学生の表現 または (未提出：原文第N文)",
      "after": "改善後の表現 または 模範解答の該当文",
      "reason": "N文目: 英文\\n（日本語訳）\\n語彙比較A／B...\\n【参考】...\\n例：...",
      "level": "✅ 正しい表現 または ❌ 文法ミス"
    }}
  ]
}}
```
```

**問題点:**
- `{{` は `.format()` でエスケープされて `{` になる
- しかし、`"before"` などは `.format()` のキーとして解釈されようとする
- 結果: `KeyError: '\n  "before"'`

---

## 🔧 根本原因

### プロンプトの構造的問題

プロンプトテンプレート内に以下の2種類の `{...}` が混在している：

1. **フォーマット変数（.format() で置換する）**
   - `{question_text}`
   - `{user_answer}`
   - `{word_count}`
   - `{required_points}`

2. **JSON例示のための文字列（.format() で置換しない）**
   - `{"before": "...", "after": "...", ...}`
   - これらは `.format()` で誤って解釈されてエラーになる

### 発生タイミング

品質修正実装で追加したkagoshima風の出力例に、JSON例が多数含まれており、それが原因。

---

## 💡 解決策

### 解決策1: JSON例示部分を `.format()` でエスケープ（推奨）

**修正方法:**
- JSON例示の `{` を `{{` に、`}` を `}}` に変更
- これにより、`.format()` 実行後に正しく `{` `}` になる

**修正箇所:**
- `prompts_translation_simple.py` の reasonフォーマット例
- 再プロンプトの出力例（`llm_service.py`）

### 解決策2: プロンプトを文字列結合に変更（非推奨）

**修正方法:**
- `.format()` を使わず、f-string や `+` での文字列結合に変更
- デメリット: 可読性が下がる

### 解決策3: JSON例示を別変数に分離（複雑）

**修正方法:**
- JSON例示部分を別の文字列変数として定義
- プロンプト本体と文字列結合
- デメリット: コードが複雑になる

---

## 🎯 推奨修正手順

### ステップ1: prompts_translation_simple.py の修正

**修正箇所1:** reasonフォーマットのJSON例示

```python
# 修正前（エラーの原因）
**出力例1（a number of / the number of）:**
```
"reason": "1文目: A number of students submitted the form online.\\n（多くの学生がその用紙をオンラインで提出した。）\\na number of（名詞句：多くの～）／the number of（名詞句：～の数）で、a number of は「たくさん」という量、the number of は「数そのもの」という数量を表します。a number of は後ろが複数名詞なので動詞も複数になりやすい（A number of students are …）。the number of は「数」が主語なので単数扱い（The number of students is …）。\\n【参考】a number of + 複数名詞（多くの～）／the number of + 複数名詞（～の数）\\n例：A number of people were absent. (多くの人が欠席した。)／The number of people was increasing. (人の数が増えていた。)"
```

# 修正後（エスケープ）
**出力例1（a number of / the number of）:**
```
"reason": "1文目: A number of students submitted the form online.\\n（多くの学生がその用紙をオンラインで提出した。）\\na number of（名詞句：多くの～）／the number of（名詞句：～の数）で、a number of は「たくさん」という量、the number of は「数そのもの」という数量を表します。a number of は後ろが複数名詞なので動詞も複数になりやすい（A number of students are …）。the number of は「数」が主語なので単数扱い（The number of students is …）。\\n【参考】a number of + 複数名詞（多くの～）／the number of + 複数名詞（～の数）\\n例：A number of people were absent. (多くの人が欠席した。)／The number of people was increasing. (人の数が増えていた。)"
```
```

**重要:** JSON例示部分の `{` `}` は全て `{{` `}}` にエスケープする

**修正箇所2:** 未提出プレースホルダのJSON例

```python
# 修正前
```json
{
  "before": "(未提出：原文第4文)",
  "after": "This method helps in converting short-term memory into long-term memory.",
  ...
}
```

# 修正後
```json
{{
  "before": "(未提出：原文第4文)",
  "after": "This method helps in converting short-term memory into long-term memory.",
  ...
}}
```
```

### ステップ2: llm_service.py の再プロンプト部分の修正

**修正箇所:** 再プロンプト1と再プロンプト2のJSON例示

```python
# 修正前
reprompt = f"""
...
```json
{{
  "points": [
    {{
      "before": "...",
      "after": "...",
      ...
    }}
  ]
}}
```
...
"""

# 修正後（f-stringなのでエスケープ不要だが、念のため確認）
# f-stringの場合、{{ }} は既にエスケープされているので問題ない
```

---

## 🧪 テスト計画

### 修正後のテスト項目

1. **基本テスト:**
   - ユーザーが報告した英文で再テスト
   - エラーが発生しないことを確認

2. **エッジケーステスト:**
   - 途中まで入力（不完全な英文）
   - 0 words
   - 非常に長い英文（200 words超）

3. **品質テスト:**
   - reasonがkagoshima風になっているか確認
   - 項目数がN個になっているか確認

---

## 📝 修正の優先度

### 🔴 最優先（即座に修正）

**理由:**
- サーバーが全く動作しない致命的なバグ
- 全ての添削リクエストが失敗する

**修正時間:** 10分以内

---

## 🎯 期待される結果

### 修正後

1. エラーが発生せず、正常に添削が実行される
2. reasonがkagoshima風で出力される
3. 項目数がN個になる
4. ユーザーが提出していない英文を添削しない

---

## 📋 関連ドキュメント

- [QUALITY_ISSUE_REPORT.md](QUALITY_ISSUE_REPORT.md): 元の品質問題レポート
- [QUALITY_VERIFICATION.md](QUALITY_VERIFICATION.md): 品質修正実装の検証ログ

---

## 🚀 次のステップ

1. `prompts_translation_simple.py` のJSON例示をエスケープ
2. `llm_service.py` の再プロンプトのJSON例示を確認
3. サーバー再起動
4. ユーザーが報告した英文で再テスト
5. 品質修正が正しく動作することを確認
