# 添削出力の根本問題と修正方針

## 📅 作成日
2026年1月29日

## 🎯 目的
添削システムで発生している致命的な問題（文番号崩壊、未提出誤爆、エラー検出漏れ、フォーマット不統一）の根本原因を特定し、修正方針を明確化する。

---

## 1. 症状（バグ報告）

### 1-1. 文番号が崩壊

**症状:**
- 本来 3文目/4文目のはずが、出力で「5文目」「6文目」などが出現
- その結果、「どの日本文に対応する誤りなのか」が見えなくなる

**実例（1回目出力）:**
```
2
❌ As a result, the group that took a nap scored higher...
→
✅ As a result, the group that took a nap scored higher...
5文目: （その結果、昼寝を取ったグループは...）  ← 実際は3文目
3文目: As a result, ...
```

### 1-2. "未提出" が誤って発生

**症状:**
- ユーザーは4文すべて提出しているのに、「✅ (未提出：原文第4文)」のような架空の未提出ポイントが出現
- さらに内容も不適切（appropriate/suitable の比較など、今回の文脈と無関係）

**実例（1回目出力）:**
```
4
✅ (未提出：原文第4文)  ← 4文全て提出済みなのに誤判定
→
✅ The participants were first divided into...
4文目: (未提出のため補足)
（参加者はまず、昼寝を30分取るグループと...）
appropriate（形容詞：適切な・ふさわしい）／suitable...  ← 文脈と無関係
```

### 1-3. エラー検出の抜け

**症状:**
- `The experiment began on 2 p.m.` は **前置詞が誤り（at が自然）** なのに、誤りとして拾えていない
- `didn't napped` のような明確ミスは拾えているので、拾えるべきミスが取りこぼされている

**期待される検出:**
```
❌ The experiment began on 2 p.m., and...
→
✅ The experiment began at 2 p.m., and...
前置詞の誤り: 時刻には at を使う
```

### 1-4. 出力フォーマットが統一されていない

**ユーザー要望:**
- 全文表示に統一
- ❌/✅ は "断片" ではなく **必ず全文（文全体）** で表示する
- 文番号行は 日本語だけに統一

**期待表示:**
```
❌ (英文フル)
→
✅ (英文フル)
1文目:（日本語フル）
```

**現状の問題:**
- 「1文目: 英文...」の行が重複して見づらい
- 断片表示が混在している

---

## 2. 再現手順

### テストデータ（1回目：昼寝の研究）

**日本語原文（4文）:**
```
1. 参加者はまず、昼寝を30分取るグループと、昼寝をしないグループに分けられた。
2. 実験は午後2時に開始され、昼寝を取ったグループはその後、記憶テストを受けた。
3. その結果、昼寝を取ったグループは昼寝をしなかったグループよりも、記憶テストで高い成績を収めた。
4. 特に、短期記憶の向上が顕著に見られた。
```

**ユーザー提出英文（4文）:**
```
1. The participants was first divided into a group that took a 30-minute nap and a group that did not take a nap.
2. The experiment began on 2 p.m., and the nap group then took a memory test afterwards.
3. As a result, the group that took a nap scored higher on the memory test than the group that didn't napped.
4. In particular, a marked improvement in short-term memory was observed.
```

### 期待される検出ミス

1. **文法ミス:** `was` → `were` (主語の数一致)
2. **前置詞ミス:** `on 2 p.m.` → `at 2 p.m.` (時刻の前置詞)
3. **文法ミス:** `didn't napped` → `didn't nap` (did + 原形)

### 実際の出力（問題あり）

**項目1:** ✅ 正常（was → were を検出）

**項目2:** ❌ 問題
```
5文目: （その結果...）  ← 実際は3文目
3文目: As a result, ...
```
- 文番号が崩壊
- `on 2 p.m.` のミスが未検出

**項目3:** ✅ 正常（didn't napped → didn't nap を検出）

**項目4:** ❌ 重大問題
```
✅ (未提出：原文第4文)  ← 全文提出済み
appropriate vs suitable の説明  ← 無関係
```

---

## 3. 根本原因（コード解析）

### 3-1. points_normalizer.py の英文分割が致命的

**問題コード:**
```python
def split_into_sentences(text: str) -> List[str]:
    pattern = re.compile(r'[.!?]+\s+')  # ← これが致命的
    sentences = pattern.split(text)
    return [s.strip() for s in sentences if s.strip()]
```

**問題点:**
- `[.!?]+\s+` パターンはピリオドが出た瞬間に無条件で分割
- `2 p.m.` が `2 p.` と `m.` に分裂
- 英文の文数が水増しされる（4文 → 5文以上）

**影響:**
1. **文番号ズレ** → 5文目/6文目化
2. **"未提出" の誤発生** → 英文数 > 日本文数 と誤判定
3. **before/after が断片のまま** → 正規化失敗

### 3-2. required_points 判定側も .split('.') 依存で水増しリスク

**問題箇所:**
```python
# llm_service.py の determine_required_points()
user_answer.split('.')  # ← p.m. で文数が増える
```

**問題点:**
- 雑な分割により文数カウントが不正確
- 未提出判定や不足ポイント補完の誤作動に繋がる

---

## 4. 修正方針（実装タスク）

### Task A: 英文の文分割を "省略形耐性あり" に置き換え（最優先）

**要件:**
- `p.m.` / `a.m.` / `e.g.` / `i.e.` / `U.S.` などを文末扱いで分割しない
- 小数 `3.14` を分割しない
- 文末の `.` `?` `!` は保持する（勝手に `.` を付与しない）

**実装方針: protect→split→restore方式**

```python
# points_normalizer.py
import re

_ABBR = [
    "a.m.", "p.m.", "e.g.", "i.e.", "etc.",
    "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.",
    "U.S.", "U.K."
]
_DOT_TOKEN = "<DOT>"

def _protect_abbreviations(text: str) -> str:
    """省略形のピリオドを一時的に保護"""
    t = text
    for abbr in _ABBR:
        # 大文字小文字ゆれも守る
        pattern = re.compile(re.escape(abbr), re.IGNORECASE)
        t = pattern.sub(lambda m: m.group(0).replace(".", _DOT_TOKEN), t)
    # "A.B." みたいなイニシャルも保護
    t = re.sub(r"\b([A-Za-z])\.(?=[A-Za-z]\.)", r"\1" + _DOT_TOKEN, t)
    return t

def _restore_abbreviations(text: str) -> str:
    """保護したピリオドを復元"""
    return text.replace(_DOT_TOKEN, ".")

def split_into_sentences(text: str) -> List[str]:
    """省略形に対応した文分割"""
    t = _protect_abbreviations(text.strip())
    if not t:
        return []
    
    # 文末記号の直後が 空白+次文開始 か 末尾 のときだけ区切る
    # 次が大文字/数字/引用符/括弧で始まる場合のみ分割
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", t)
    parts = [p.strip() for p in parts if p.strip()]
    parts = [_restore_abbreviations(p) for p in parts]
    return parts
```

**重要:** `p.m.` が割れないこと

### Task B: required_points の算出も同じ分割関数に寄せる

**修正箇所:**
```python
# llm_service.py の determine_required_points()
# ❌ 修正前
user_sentences = user_answer.split('.')

# ✅ 修正後
from points_normalizer import split_into_sentences
user_sentences = split_into_sentences(user_answer)
```

**効果:**
- 不足判定→"未提出"誤爆が止まる
- 文数カウントの一貫性が保たれる

### Task C: "未提出" を出す条件を厳格化（誤爆防止）

**ルール:**
1. 英文が本当に不足している（頑健分割で、英文文数 < 日本文文数）が確認できた場合のみ "未提出" を出す
2. それ以外は "未提出" を出さない（誤爆をゼロにする）

**"未提出" を出す場合の内容:**
```python
before: "(未提出)"
after: 模範解答の該当英文（フル）
reason: "未提出のため減点"  # 固定
level: "❌"
```

**禁止事項:**
- `appropriate/suitable` みたいな無関係比較はしない
- 実際に提出されている文に対して "未提出" と表示しない

### Task D: 出力フォーマットを「全文表示」に統一（仕様）

**要件:**
1. ❌ と ✅ は **必ず文全体を表示**（断片禁止）
2. 表示は以下に固定：

```
❌ {before_full_sentence}
→
✅ {after_full_sentence}
{sentence_no}文目:（{japanese_sentence_full}）
```

3. **「{sentence_no}文目: 英文フル」をもう一度出す行は削除**（重複でノイズ）

**実装箇所:**
- `static/main.js` の表示ロジック修正
- 英文の重複行を削除

### Task E: 改善提案（💡）を廃止し、減点レベルの誤りだけに限定

**仕様変更:**
- 💡カテゴリ（減点ではない改善提案）は **出力しない**
- 出力は「明確に減点される誤り」だけ

**実装方法:**
1. LLMプロンプトに「減点対象のみ抽出」「改善提案禁止」を明記
2. 返却JSONに `severity: "error" | "suggestion"` を入れさせる
3. サーバ側で `suggestion` は破棄（プロンプトだけでは漏れるため）

**理由:**
- ユーザーの英語表現を尊重する設計思想
- 💡は過去の実装で廃止済みだが、完全に除去されていない

---

## 5. テスト項目

### Unit Test: sentence splitter

**テストケース1:**
```python
input = "The experiment began at 2 p.m., and the nap group then took a test."
expected = ["The experiment began at 2 p.m., and the nap group then took a test."]
result = split_into_sentences(input)
assert len(result) == 1  # p.m. で割れない
```

**テストケース2:**
```python
input = "We live in the U.S. It is big."
expected = ["We live in the U.S.", "It is big."]
result = split_into_sentences(input)
assert len(result) == 2  # U.S. 内で割れない
```

**テストケース3:**
```python
input = "The value is 3.14. The result is clear."
expected = ["The value is 3.14.", "The result is clear."]
result = split_into_sentences(input)
assert len(result) == 2  # 小数で割れない
```

### Integration Test: 今回の昼寝データ再現

**入力:**
- 日本語原文: 4文
- ユーザー英文: 4文（`2 p.m.` を含む）

**期待結果:**
1. ✅ 文番号は 1〜4（5文目/6文目は出ない）
2. ✅ "未提出" が出ない
3. ✅ `on 2 p.m.` が誤りとして拾われる
4. ✅ 出力フォーマットが全文表示で統一

**実行方法:**
```bash
python3 test_correction_format.py
```

---

## 6. 完了条件（Acceptance Criteria）

### 必須条件

- [ ] `p.m.` を含む英文が文分割で増殖しない
- [ ] 文番号は常に 1..N（N=日本文数）に収まる
- [ ] "未提出" は本当に未提出のときだけ
- [ ] ❌/✅ は全文表示に統一
- [ ] 文番号行は日本語のみで統一（英文の重複行なし）
- [ ] 💡改善提案は出力されない（減点誤りのみ）

### 最低限拾うべき減点ミス（今回の「昼寝」英文）

- [ ] `The participants was` → `were`（主語一致）
- [ ] `began on 2 p.m.` → `began at 2 p.m.`（前置詞）
- [ ] `didn't napped` → `didn't take a nap` / `didn't nap`（did + 原形）

---

## 7. 実装ログ

### 修正履歴

| 日時 | 修正内容 | ファイル | コミット |
|------|---------|---------|---------|
| 2026-01-29 | ドキュメント作成 | CORRECTION_OUTPUT_ANALYSIS_ISSUE.md | - |
| - | Task A実装予定 | points_normalizer.py | - |
| - | Task B実装予定 | llm_service.py | - |
| - | Task C実装予定 | llm_service.py | - |
| - | Task D実装予定 | static/main.js | - |
| - | Task E実装予定 | prompts_translation_simple.py | - |

---

## 8. 参考資料

### 関連ファイル

- [points_normalizer.py](points_normalizer.py) - 文分割・正規化ロジック
- [llm_service.py](llm_service.py) - メインロジック
- [prompts_translation_simple.py](prompts_translation_simple.py) - 添削プロンプト
- [static/main.js](static/main.js) - フロントエンド表示

### 過去の関連修正

- Commit 4ae05ed: フラグメント→全文変換、💡削除
- Commit 9a97a09: excerpt_typeバイアス修正

### 設計思想

- ユーザーの英語表現を尊重（減点対象のみ指摘）
- 全文表示による明確性の確保
- 文番号の一貫性による学習効率向上

### 問題1: 項目4の「未提出」表記

**出力内容:**
```
4
✅ (未提出：原文第4文)
→
✅ The participants were first divided into a group that took a 30-minute nap and a group that did not take a nap
4文目: (未提出のため補足)
（参加者はまず、昼寝を30分取るグループと、昼寝をしないグループに分けられた）
```

**問題点:**
- ユーザーは4文全て提出しているにも関わらず「未提出」と表示
- 「未提出のため補足」という説明は完全に誤り
- この動作は設計意図にない

**期待される動作:**
- ユーザーが提出した4文全てを分析
- 未提出の文に対する補足は不要

---

### 問題2: 項目1と項目4の重複

**項目1 (before/after):**
```
❌ The participants was first divided into a group that took a 30-minute nap and a group that did not take a nap.
→
✅ The participants were first divided into a group that took a 30-minute nap and a group that did not take a nap.
```

**項目4 (before/after):**
```
✅ (未提出：原文第4文)
→
✅ The participants were first divided into a group that took a 30-minute nap and a group that did not take a nap
```

**問題点:**
- afterの内容が完全に同一（ピリオドの有無だけの違い）
- 同じ文に対して2つの指摘項目が存在
- 項目4のレベルは✅なので解説項目として不適切

**期待される動作:**
- 同じ文に対する指摘は1つのみ
- ✅レベルの項目は通常解説に含めない

---

### 問題3: sentence_noの不整合

**日本語原文の構成:**
1. 参加者はまず、昼寝を30分取るグループと、昼寝をしないグループに分けられた。
2. 実験は午後2時に開始され、昼寝を取ったグループはその後、記憶テストを受けた。
3. その結果、昼寝を取ったグループは昼寝をしなかったグループよりも、記憶テストで高い成績を収めた。
4. 特に、短期記憶の向上が顕著に見られた。

**ユーザーの英文提出:**
1. The participants was first divided into... (原文1に対応)
2. The experiment began on 2 p.m., and... (原文2に対応)
3. As a result, the group that took a nap scored higher... (原文3に対応)
4. In particular, a marked improvement in short-term memory was observed. (原文4に対応)

**出力されたsentence_no:**

| 項目 | 表示されたsentence_no | 実際の対応文 | 正しいsentence_no |
|------|----------------------|-------------|-------------------|
| 1 | "1文目" → "1文目" | 原文1文目 | 1 ✅ |
| 2 | "5文目" → "3文目" | 原文3文目 | 3 ✅ |
| 3 | "6文目" → "4文目" | 原文4文目 | 4 ✅ |
| 4 | "4文目" | 原文1文目（重複） | - ❌ |

**問題点:**
- 項目2で「5文目」と表示されているが、原文は4文しかない
- 日本語原文のsentence_no（5文目、6文目）と英文のsentence_no（3文目、4文目）が不整合
- 項目4が「4文目」となっているが内容は1文目と同じ

**期待される動作:**
- 日本語原文と英文のsentence_noは常に一致すべき
- 英文が4文なら、sentence_noは1〜4のみ

---

### 問題4: 無関係な説明内容

**項目4の説明:**
```
appropriate（形容詞：適切な・ふさわしい）／suitable（形容詞：適した・好都合な）で、appropriateは状況や文脈に合っていること、suitableは目的に合っていることを意味します。
【参考】be appropriate for A（Aに適切である）／be suitable for A（Aに適している）
例：This method is appropriate for beginners. (この方法は初心者に適切です。)／This tool is suitable for the task. (この道具はその作業に適しています。)
```

**before/after:**
```
✅ (未提出：原文第4文)
→
✅ The participants were first divided into a group that took a 30-minute nap and a group that did not take a nap
```

**問題点:**
- before/after文に "appropriate" も "suitable" も含まれていない
- 説明が文脈と完全に無関係
- GPTが無理やり説明を生成した可能性

**期待される動作:**
- before/afterに含まれる単語や文法ポイントを説明
- 文脈に合った適切な説明

---

### 問題5: ✅レベルの項目が解説に含まれる

**項目3:**
```
3
✅ In particular, a marked improvement in short-term memory was observed.
6文目: （特に、短期記憶の向上が顕著に見られた。）
4文目: In particular, a marked improvement in short-term memory was observed.
（特に、短期記憶の向上が顕著に見られた。）
marked（形容詞：著しい：目立つ程度）／significant（形容詞：重要な：意味や価値を示す程度）...
```

**項目4:**
```
4
✅ (未提出：原文第4文)
→
✅ The participants were first divided into a group that took a 30-minute nap and a group that did not take a nap
4文目: (未提出のため補足)
（参加者はまず、昼寝を30分取るグループと、昼寝をしないグループに分けられた）
appropriate（形容詞：適切な・ふさわしい）／suitable（形容詞：適した・好都合な）...
```

**問題点:**
- ✅レベルは「正しい表現」を意味する
- 正しい表現なのに解説項目として表示されるのは矛盾
- 以前の改善で「✅の場合はbefore==afterに統一」したはずだが、ここでは異なる

**期待される動作:**
- ✅レベルの項目は基本的に解説から除外
- もしくは「補足説明」として別枠で表示

---

## 🔧 2回目の出力との比較

### 2回目の出力（運動の研究）の状況

**項目5に同様の問題:**
```
5
❌ (未提出：原文第5文)
→
✅ However, there was little change in the group that did not exercise.
5文目: （運動をしなかったグループにはほとんど変化がなかった。）
5文目: (未提出のため補足)
（運動をしなかったグループにはほとんど変化がなかった。）
little（形容詞：ほとんどない）／much（形容詞：多くの）...
```

**特徴:**
- 原文5文目は「一方、運動をしなかったグループにはほとんど変化がなかった。」
- ユーザーの英文提出では4文で終了（5文目は提出していない）
- システムが5文目を「補足」として生成

**問題点:**
- beforeが「❌ (未提出：原文第5文)」となっているのは不自然
- afterは✅レベルなのにbeforeは❌という矛盾
- ユーザーが提出していない文を勝手に生成して指摘項目に含めている

**重要な発見:**
- 2回目の方がより正確に動作している（実際に未提出の文を補足）
- しかし1回目は全文提出済みなのに「未提出」と誤判定

---

## 💡 推定される原因

### 原因1: normalize_points()のロジック問題

**仮説:**
```python
# points_normalizer.py の normalize_points() が以下を誤判定している可能性
1. ユーザー提出文とbefore/afterの照合ミス
2. 日本語原文とユーザー英文の文数不一致を誤検出
3. 「未提出」判定ロジックの誤動作
```

**検証が必要な箇所:**
- `normalize_points()` 関数全体
- 特に sentence_no の割り当てロジック
- 日本語と英語の文数照合ロジック

---

### 原因2: GPTプロンプトの問題

**仮説:**
```
prompts_translation.py または prompts_translation_simple.py が以下を指示している可能性：
1. 「未提出の文があれば補足せよ」という指示
2. 「全ての文に対して解説を生成せよ」という指示
3. ✅レベルの項目も含めよという指示
```

**検証が必要な箇所:**
```python
# prompts_translation.py
- correction_points の生成指示
- 未提出文への対応指示
- ✅レベルの扱いに関する指示

# prompts_translation_simple.py
- 同上
```

---

### 原因3: llm_service.pyの統合ロジック問題

**仮説:**
```python
# llm_service.py の generate_question() が以下を誤処理している可能性
1. GPTレスポンスの correction_points を normalize_points() に渡す前の検証不足
2. normalize後の valid_points の検証不足
3. 日本語原文とユーザー英文の文数不一致時の処理ミス
```

**検証が必要な箇所:**
```python
# llm_service.py (lines 1360-1378)
japanese_sentences = [s.strip() for s in question_text.replace('。', '.').split('.') if s.strip()]

valid_points = normalize_points(
    points=valid_points,
    normalized_answer=normalized_answer,
    japanese_sentences=japanese_sentences
)
```

---

### 原因4: 文の分割ロジックの問題

**仮説:**
```python
# points_normalizer.py の split_into_sentences() が以下を誤判定している可能性
1. 複文を複数文として誤認識
2. "2 p.m." のようなピリオドを文の区切りと誤判定
3. 結果として実際よりも多い文数をカウント
```

**検証が必要な箇所:**
```python
def split_into_sentences(text: str) -> List[str]:
    # Split by [.!?]+\s+ という正規表現が不適切な可能性
    pattern = re.compile(r'[.!?]+\s+')
    sentences = pattern.split(text)
    return [s.strip() for s in sentences if s.strip()]
```

**例:**
```
"The experiment began on 2 p.m., and the nap group then took a memory test afterwards."
→ "2 p.m." のピリオドで分割される可能性
→ 実際は1文だが2文とカウントされる可能性
```

---

## 🎯 解決すべき課題

### 優先度1: 「未提出」誤判定の修正

**課題:**
- 全文提出済みなのに「未提出」と表示される
- 2回目では実際に未提出の文を正しく検出しているので、1回目の判定ロジックに問題

**解決策の方向性:**
1. ユーザー提出文とbefore/afterの照合ロジックを見直す
2. 日本語原文とユーザー英文の文数比較を正確に行う
3. 「未提出」判定の条件を明確化

---

### 優先度2: sentence_noの不整合修正

**課題:**
- 日本語原文と英文のsentence_noが一致しない
- 存在しない「5文目」「6文目」が表示される

**解決策の方向性:**
1. 日本語原文と英文の対応を1:1で正確に保つ
2. sentence_noは常にユーザー提出英文を基準にする
3. 表示時に日本語と英語の番号を統一

---

### 優先度3: 重複指摘の排除

**課題:**
- 同じ文に対して複数の指摘項目が生成される
- 項目1と項目4が同じ内容

**解決策の方向性:**
1. normalize_points() で重複をチェック
2. before/afterが同一の項目を除外
3. ✅レベルの項目を解説から除外（または別枠表示）

---

### 優先度4: 無関係な説明の防止

**課題:**
- before/afterに含まれない単語の説明が生成される
- 文脈と無関係な内容

**解決策の方向性:**
1. GPTプロンプトで「before/afterに含まれる単語のみ説明せよ」と明示
2. 生成後の検証で無関係な説明を検出・除外
3. 説明内容とbefore/afterの関連性をチェック

---

### 優先度5: ✅レベル項目の扱い

**課題:**
- ✅レベル（正しい表現）が解説項目に含まれる
- 設計上は✅はbefore==afterとなるはずだが、実際は異なる

**解決策の方向性:**
1. ✅レベルは基本的に解説から除外
2. もしくは「補足説明」として別セクションで表示
3. ✅レベルでbefore≠afterの場合は❌に変更

---

## 📊 問題の影響範囲

### ユーザー体験への影響

1. **混乱:** 「未提出」と表示されるが実際は提出済み
2. **不信感:** sentence_noが不整合で信頼性が低下
3. **冗長性:** 同じ指摘が重複して表示
4. **無関係な情報:** 文脈と関係ない説明で学習効率が低下

### システムの信頼性への影響

1. **正確性の低下:** 誤った判定が頻発
2. **一貫性の欠如:** 1回目と2回目で動作が異なる
3. **予測不可能性:** いつ問題が発生するか不明

---

## 🔍 検証手順の提案

### ステップ1: ログ出力の追加

```python
# llm_service.py に以下を追加
logger.info(f"[DEBUG] 日本語原文の文数: {len(japanese_sentences)}")
logger.info(f"[DEBUG] ユーザー英文の文数: {len(split_into_sentences(normalized_answer))}")
logger.info(f"[DEBUG] GPT返却のcorrection_points数: {len(valid_points)}")
logger.info(f"[DEBUG] normalize後のvalid_points数: {len(valid_points)}")

for i, point in enumerate(valid_points):
    logger.info(f"[DEBUG] Point {i+1}: sentence_no={point.sentence_no}, level={point.level}")
    logger.info(f"[DEBUG]   before: {point.before[:50]}...")
    logger.info(f"[DEBUG]   after: {point.after[:50]}...")
```

### ステップ2: 1回目の問題を再現

```bash
# 同じ問題文で再度テスト
python3 test_api_phase1.py

# ログを確認して以下をチェック：
# 1. 文数のカウントが正しいか
# 2. sentence_noの割り当てが正しいか
# 3. 重複が発生していないか
```

### ステップ3: プロンプトの見直し

```python
# prompts_translation.py を確認
# 以下の指示が含まれていないかチェック：
# - 「未提出の文を補足せよ」
# - 「全ての文に対して解説を生成せよ」
# - ✅レベルも含めよ」
```

### ステップ4: normalize_points()の検証

```python
# points_normalizer.py をテスト
# 以下のケースで正しく動作するかチェック：
# 1. 全文提出の場合
# 2. 一部未提出の場合
# 3. 複文を含む場合
# 4. "2 p.m." のような略語を含む場合
```

---

## 📝 GPTへの相談内容案

### 質問1: 「未提出」判定ロジック

```
【質問】
ユーザーが4文全て提出しているにも関わらず、出力で「未提出：原文第4文」と表示されます。
以下のロジックで何が問題でしょうか？

【コード】
- points_normalizer.py の normalize_points()
- llm_service.py の文数カウント
- プロンプトでの指示

【期待される動作】
全文提出済みの場合は「未提出」と表示されないこと
```

### 質問2: sentence_noの不整合

```
【質問】
日本語原文は4文ですが、出力で「5文目」「6文目」と表示されます。
以下のどこで文数カウントがずれていますか？

【コード】
- split_into_sentences() の正規表現
- japanese_sentences の生成ロジック
- sentence_noの割り当てロジック

【期待される動作】
日本語と英語のsentence_noが常に一致すること
```

### 質問3: 重複と✅レベルの扱い

```
【質問】
同じ文に対して2つの指摘（項目1と項目4）が生成され、しかも項目4は✅レベルです。
以下のどこで重複が発生し、✅が解説に含まれるのでしょうか？

【コード】
- normalize_points() の重複チェック
- ✅レベルのフィルタリング
- プロンプトでの✅の扱い指示

【期待される動作】
- 同じ文への指摘は1つのみ
- ✅レベルは解説から除外（または別枠）
```

---

## 🎬 まとめ

### 発見された問題

1. ✅ **「未提出」誤判定** - 全文提出済みなのに未提出と表示
2. ✅ **sentence_no不整合** - 日本語と英語の文番号が不一致
3. ✅ **重複指摘** - 同じ文に対して複数項目
4. ✅ **無関係な説明** - 文脈と関係ない単語の説明
5. ✅ **✅レベルの誤表示** - 正しい表現が解説項目に含まれる

### 優先的に対応すべき問題

1. **最優先:** 「未提出」誤判定と重複指摘の修正
2. **高優先:** sentence_noの不整合修正
3. **中優先:** ✅レベルの扱いの明確化
4. **低優先:** 無関係な説明の防止

### 次のステップ

1. **ログ出力追加** → 問題箇所の特定
2. **GPTに相談** → ロジックの見直し提案
3. **修正実装** → 優先度順に対応
4. **再テスト** → 同じケースで検証

---

## 📎 参考情報

### 関連ファイル

- `points_normalizer.py` (225行) - フラグメント正規化
- `llm_service.py` (1673行) - メインロジック
- `prompts_translation.py` (1096行) - 問題生成プロンプト
- `prompts_translation_simple.py` (338行) - 添削プロンプト
- `models.py` (235行) - データモデル

### 前回の改善内容

- Commit 4ae05ed: フラグメント→全文変換、💡削除
- Commit 9a97a09: excerpt_typeバイアス修正

### テスト環境

- Python 3.13
- Flask + OpenAI GPT-4o
- Port: 8001
- Database: SQLite
