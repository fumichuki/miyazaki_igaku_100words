# 🚨 不具合レポート: 文分割とLLM出力の深刻な問題

## 報告日時
2026年1月29日

## 影響範囲
**重大度: HIGH（システムの主要機能が正常動作していない）**

---

## 🔴 不具合1: 文分割が過剰に行われる（最重要）

### 現象
ユーザーが入力した英文が、意図しない箇所で分割されて6文になってしまう。

### ユーザー入力（実際の英文）
```
According to a recent survey.Japan is getting older, and the demand for nursing home are increasing very fast.As the number of elderly people increase, care service cannot keep up, and many facilities are full by people
so a lot of families cannot get in.this situation is a big problem for local communities,and the government must act fast.If there was more staff, the services will be enough.
```

### 期待される動作
- **日本語原文が3文**なので、**英訳も3文**に分割されるべき
- 原文:
  1. 最近の調査によれば、日本の高齢化が進む中で、介護施設の需要が急増していることが判明した。
  2. 高齢者人口の増加に伴い、介護サービスの提供が追いつかず、多くの施設が満員状態となっている。
  3. この状況は、地域社会や政府にとって大きな課題となっており、迅速な対応が求められている。

### 実際の動作（不具合）
- **6文に過剰分割**されてしまう:
  1. `According to a recent survey.`
  2. `Japan is getting older, and the demand for nursing home are increasing very fast.`
  3. `As the number of elderly people increase, care service cannot keep up, and many facilities are full by people.`
  4. `so a lot of families cannot get in.`
  5. `this situation is a big problem for local communities,and the government must act fast.`
  6. `If there was more staff, the services will be enough.`

### 根本原因
**問題箇所**: `points_normalizer.py` の `normalize_user_input()` および `split_into_sentences()`

#### 原因1: ピリオド直後にスペースがない箇所で誤って分割
- ユーザーは「survey.Japan」「fast.As」「in.this」のように、**ピリオドの後にスペースを入れ忘れている**
- `normalize_user_input()` は、この箇所にスペースを挿入する（正しい）:
  - `survey.Japan` → `survey. Japan`
  - `fast.As` → `fast. As`
  - `in.this` → `in. this`
- **しかし**、`split_into_sentences()` が、このスペース挿入を「新しい文の開始」と誤認識して分割してしまう

#### 原因2: 改行の途中で文が切れている
- ユーザーの入力には改行が含まれる:
  ```
  ...full by people
  so a lot of families...
  ```
- 改行前に句読点がないため、本来は1文だが、改行後の「so」が小文字であるにもかかわらず新しい文として扱われている

#### 原因3: 小文字で始まる文を許容している
- `split_into_sentences()` は小文字始まりの文に対応している（line 157）:
  ```python
  parts = re.split(r'([.!?])\s*(?=[A-Za-z0-9"\'\(])', protected)
  ```
- これにより、「so a lot」「this situation」のような小文字始まりの文も分割されてしまう
- **意図**: モバイル入力での小文字始まりに対応
- **副作用**: 実際には継続している文を誤って分割

### 影響
1. **文番号のズレ**: 
   - LLMは「3文目」として処理すべき内容を、実際には別の文として判定
   - 出力で「3文目: （高齢者人口の増加に伴い...）」と表示されるが、実際には入力の3文目とは異なる内容
   
2. **添削の信頼性低下**:
   - 文が細切れになることで、文脈が失われる
   - 長い文の構造的な問題を検出できない

---

## 🔴 不具合2: LLMが未提出の文に対して無関係な解説を生成

### 現象
出力された項目2と3で、以下の問題が発生:
```
2
✅ (未提出：原文第2文)
→
✅ According to a recent survey, as Japan ages, the demand for nursing homes is rapidly increasing

appropriate（形容詞：適切な・ふさわしい）／suitable（形容詞：適した・好都合な）で、appropriateは状況や文脈に合っていること、suitableは目的に合っていることを意味します。
【参考】be appropriate for A（Aに適切である）／be suitable for A（Aに適している）
例：This method is appropriate for beginners. (この方法は初心者に適切です。)／This tool is suitable for the task. (この道具はその作業に適しています。)
```

### 問題点
1. **「未提出」と表示しているのに、LLMが勝手に英文を生成**
   - `(未提出：原文第2文)` → ユーザーは提出していない
   - なのに `According to a recent survey, as Japan ages...` という英文が生成されている
   
2. **reasonの内容が完全に無関係**
   - 生成された英文には「appropriate」も「suitable」も含まれていない
   - まったく関係ない語彙解説（appropriate/suitable）が表示されている
   - これは明らかにLLMのハルシネーション（幻覚）

3. **日本語訳が表示されない**
   - フォーマット要件では「N文目: （日本語訳）」が必須
   - しかし `(未提出：原文第2文)` という表記のみで、日本語訳が欠落

### 根本原因
**問題箇所**: `prompts_translation_simple.py` のプロンプト設計

#### 原因1: 「未提出」の定義が曖昧
- プロンプトには「未提出」の文に対する明確な指示がない
- LLMが「未提出」をどう扱うべきか理解していない:
  - オプション1: その文をスキップして何も出力しない
  - オプション2: 模範解答を生成する
  - オプション3: エラーメッセージを表示する
  
- 現状、LLMはオプション2（模範解答生成）を選択しているが、reasonの内容が無関係

#### 原因2: 文分割の不具合が連鎖的に影響
- 前述の「不具合1」により、入力が6文に分割される
- しかし日本語原文は3文のみ
- LLMは原文第2文、第3文に対応する英文がないと判断し「未提出」とマークするが、実際には文分割が間違っているだけ

### 影響
1. **ユーザーの混乱**:
   - 提出していない文に対して解説が表示される
   - 解説内容が無関係なため、信頼性が失われる
   
2. **学習効果の低下**:
   - 正しい添削結果でないため、学習に使えない

---

## 🔴 不具合3: 日本語訳の表示が不完全

### 現象
項目1では正しく表示されるが、項目2と3では表示されない:

**項目1（正しい）:**
```
3文目: （高齢者人口の増加に伴い、介護サービスの提供が追いつかず、多くの施設が満員状態となっている。）
```

**項目2と3（不具合）:**
```
✅ (未提出：原文第2文)
✅ (未提出：原文第3文)
```

### 根本原因
これは**不具合2の副作用**:
- 「未提出」の場合、日本語訳を表示する仕組みが機能していない
- プロンプトでは「N文目: （日本語訳）」が必須と指定しているが、「未提出」の場合の例外処理が明記されていない

---

## 📊 テスト結果の詳細

### normalize_user_input() の処理結果
```
入力: According to a recent survey.Japan is getting older, and the demand for nursing home are increasing very fast.As the number of elderly people increase, care service cannot keep up, and many facilities are full by people
so a lot of families cannot get in.this situation is a big problem for local communities,and the government must act fast.If there was more staff, the services will be enough.

出力: According to a recent survey. Japan is getting older, and the demand for nursing home are increasing very fast. As the number of elderly people increase, care service cannot keep up, and many facilities are full by people. so a lot of families cannot get in. this situation is a big problem for local communities,and the government must act fast. If there was more staff, the services will be enough.
```

**変更点**:
- `survey.Japan` → `survey. Japan` （スペース挿入）
- `fast.As` → `fast. As` （スペース挿入）
- `people\nso` → `people. so` （改行後にピリオド挿入）
- `in.this` → `in. this` （スペース挿入）
- `fast.If` → `fast. If` （スペース挿入）

### split_into_sentences() の処理結果
6文に分割:
1. `According to a recent survey.`
2. `Japan is getting older, and the demand for nursing home are increasing very fast.`
3. `As the number of elderly people increase, care service cannot keep up, and many facilities are full by people.`
4. `so a lot of families cannot get in.`
5. `this situation is a big problem for local communities,and the government must act fast.`
6. `If there was more staff, the services will be enough.`

---

## 🔧 推奨される修正方針

### 修正1: 文分割ロジックの改善（最優先）

**問題**: ユーザーが意図的に句読点を省略している場合と、単なるタイプミスを区別できていない

**解決策A - 保守的アプローチ（推奨）**:
1. **改行を文の区切りとして優先**
   - ユーザーが改行で区切っている場合は、その改行を尊重
   - ただし、改行の末尾に句読点がない場合は、次の行と結合
   
2. **小文字始まりの文を新しい文として扱わない**
   - 「so」「this」などの小文字始まりは、前の文の継続と見なす
   - 例外: ピリオド + 大文字の後に小文字が来る場合のみ分割
   
3. **ピリオド直後の大文字のみを文の開始と見なす**
   - 現在: `[.!?]\s*(?=[A-Za-z0-9"\'\(])`
   - 変更後: `[.!?]\s+(?=[A-Z"\'\(])`（大文字のみ、スペース必須）

**解決策B - 日本語原文の文数に合わせる（積極的）**:
1. 日本語原文の文数を取得（例: 3文）
2. ユーザーの英文を3文になるよう強制分割
3. メリット: 文数のズレが発生しない
4. デメリット: 実装が複雑、誤分割の可能性

### 修正2: 「未提出」の処理を明確化

**prompts_translation_simple.py** に以下を追加:

```python
### 未提出の文の処理【重要】

原文にある文だが、ユーザーが英訳を提出していない場合:
- level: "✅"
- before: "(未提出)"
- after: "(未提出)"
- reason: "N文目: （未提出）\n（日本語訳: [原文をそのまま記載]）\nこの文は提出されていません。"
- 模範解答を勝手に生成しない
- 無関係な語彙解説を出さない
```

### 修正3: 日本語訳の必須化を徹底

**prompts_translation_simple.py** の出力例を全て見直し:
- ✅の場合も必ず「N文目: （日本語訳）」を含める
- 「未提出」の場合も「（日本語訳: ...）」を含める
- LLMが省略できないよう、例を追加

---

## 🧪 検証方法

### テストケース1: ピリオド直後にスペースなし
```
Input: "I like apples.She likes oranges."
Expected: 2文 ["I like apples.", "She likes oranges."]
Actual: 2文（正しい）
```

### テストケース2: 改行途中で文が切れている
```
Input: "I like apples\nbut she likes oranges."
Expected: 1文 ["I like apples but she likes oranges."]
Actual: 2文（不具合）
```

### テストケース3: 小文字始まり
```
Input: "I like apples. so does she."
Expected: 1文または2文（文脈による）
Actual: 2文（split_into_sentencesは分割する）
```

---

## 📝 関連ファイル

### 主要ファイル
- `points_normalizer.py` (lines 70-180)
  - `normalize_user_input()`: ピリオド後にスペース挿入
  - `split_into_sentences()`: 文分割ロジック
  
- `prompts_translation_simple.py` (lines 200-280)
  - reasonフォーマットの定義
  - 出力例

- `llm_service.py` (lines 150-250)
  - LLM呼び出しロジック
  - 文分割の実行

### テストファイル
- `test_sentence_split_debug.py` （新規作成）
  - 今回の不具合を再現するテスト
  - 実行: `python test_sentence_split_debug.py`

---

## ⚠️ 優先度

1. **P0 (最優先)**: 文分割ロジックの修正
   - 影響範囲: 全てのユーザー入力
   - 修正しない限り、システムが正常に機能しない
   
2. **P1 (高優先)**: 「未提出」の処理明確化
   - 影響範囲: 文数が合わない場合（頻繁に発生）
   - ユーザーの混乱を招く
   
3. **P2 (中優先)**: 日本語訳の表示徹底
   - 影響範囲: ✅の項目
   - 学習効果に影響

---

## 📌 次のステップ

1. ✅ 不具合を再現するテストを作成（完了）
2. ⏳ 文分割ロジックの修正案を実装
3. ⏳ 「未提出」処理のプロンプト追加
4. ⏳ 全テストケースで検証
5. ⏳ GitHub にコミット

---

## 補足: GPTへの投げ方

このレポートをGPT-4に投げる際は、以下のファイルも添付してください:

### 必須ファイル
```
points_normalizer.py       # 文分割ロジック
constraint_validator.py    # 句読点正規化
prompts_translation_simple.py  # プロンプト定義
llm_service.py            # LLM呼び出し
test_sentence_split_debug.py  # 不具合再現テスト
```

### プロンプト例
```
以下の不具合レポートと関連コードを確認してください。

【不具合レポート】
（このファイルの内容を貼り付け）

【質問】
1. 文分割ロジックの修正案を3つ提案してください（保守的・中間・積極的）
2. 「未提出」の処理を明確化するプロンプトの追加箇所と内容を提案してください
3. 日本語訳の表示を徹底するための修正案を提案してください

【制約条件】
- 既存のテストケースは全て通過すること
- 新しい不具合を導入しないこと
- パフォーマンスへの影響は最小限にすること
```

---

**報告者**: GitHub Copilot  
**最終更新**: 2026年1月29日
