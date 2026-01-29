# 添削結果の出力フォーマット改善：問題点と解決策

## 📌 現状の問題点

### 問題1: before/after表示の不統一

#### 現状
添削ポイントで**全文表示**と**一部表示**が混在している：

**全文表示の例:**
```
❌ A study showed that repetitive learning are effective for consolidating memory.
→
✅ A study showed that repetitive learning is effective in consolidating memory.
1文目: A study showed that repetitive learning is effective in consolidating memory.
```

**一部表示の例:**
```
❌ were divide into
→
✅ were divided into
1文目: In the study, the participants were divided into three different groups.
```

#### 問題点
- ユーザーが混乱する（どのような基準で全文/一部が決まるのか不明）
- 一部表示だと文脈が分かりにくい
- 統一感がない

#### 理想の形
**全文表示に統一:**
```
❌ The participants were divide into three groups.
→
✅ The participants were divided into three groups.
1文目: The participants were divided into three groups.
```

---

### 問題2: 日本語訳の表示位置

#### 現状
日本語訳が修正後の英文（✅の部分）の説明に含まれている：

```
❌ A study showed that repetitive learning are effective for consolidating memory.
→
✅ A study showed that repetitive learning is effective in consolidating memory.
1文目: A study showed that repetitive learning is effective in consolidating memory.
（ある研究では、反復学習が記憶の定着に有効であることが示された。）
                                    ↑ ここに日本語訳
```

#### 問題点
- どの文の修正なのか、日本語訳を見るまで分からない
- 修正前の英文（❌）と日本語訳が離れている
- 視認性が悪い

#### 理想の形
**beforeの行に日本語訳を表示:**
```
❌ A study showed that repetitive learning are effective for consolidating memory.
→
✅ A study showed that repetitive learning is effective in consolidating memory.
1文目: （ある研究では、反復学習が記憶の定着に有効であることが示された。）
      ↑ beforeの行に日本語訳を移動
```

さらに改善案：
```
1文目: （ある研究では、反復学習が記憶の定着に有効であることが示された。）
❌ A study showed that repetitive learning are effective for consolidating memory.
→
✅ A study showed that repetitive learning is effective in consolidating memory.
```

---

### 問題3: 💡（改善提案）の扱い

#### 現状
添削ポイントに3種類のレベルがある：
- ❌ **明確な間違い**（減点対象）
- ✅ **正しい表現**（模範解答）
- 💡 **改善提案**（より良い表現）

**💡の例:**
```
💡 Group A tended to improve their concentration
→
✅ Group A showed an improvement in concentration
4文目: Group A showed an improvement in concentration.
（Aグループは集中力が向上する傾向が見られた。）
improve（動詞：向上する：質や能力が増す）／showed an improvement（動詞句：向上が見られた：改善が示された）で、具体的な向上を示す文脈です。
```

#### 問題点
1. **ユーザーの英文を尊重していない**
   - `Group A tended to improve their concentration`は間違いではない
   - 単なる好みの問題で改善を強要している
   - ユーザーの表現の自由を奪っている

2. **ロジックが複雑**
   - 「減点レベルか」「改善提案か」の判定が難しい
   - プロンプトが複雑化する
   - LLMが一貫した判定をできない

3. **混乱を招く**
   - 💡なのに✅（正しい表現）が混在
   - ユーザーは「これは直すべきなのか？」と迷う

#### 設計思想
> **【ユーザーの英文を尊重し、好みの問題による改善提案は絶対にしない】**

- 減点レベルの明確な間違いのみ指摘する
- 文法的に正しい表現は尊重する
- より良い表現があっても、押し付けない

#### 理想の形
**💡（改善提案）を完全廃止し、❌と✅のみにする:**

**減点レベルの間違いのみ指摘:**
```
❌ were divide into
→
✅ were divided into
1文目: （その研究では、参加者は3つの異なるグループに分けられた。）
理由: divide（動詞：分ける）／divided（過去分詞：分けられた）で、過去分詞形が必要です。
```

**正しい表現はそのまま:**
```
✅ Group A tended to improve their concentration
1文目: （Aグループは集中力が向上する傾向が見られた。）
理由: tended to improve は文法的に正しく、意味も明確です。
```

---

## 🔍 問題の根本原因分析

### プロンプト設計の問題

#### 現状のプロンプト（推測）
```
学生の英文を添削し、以下のレベルで分類してください：
1. ❌ 文法的な間違い
2. ✅ 正しい表現
3. 💡 より良い表現への改善提案
```

#### 問題点
1. **曖昧な基準**
   - 「より良い表現」の定義が不明確
   - LLMが主観で判断してしまう
   - 一貫性がない

2. **before/afterの抽出基準が不明**
   - 全文を抽出する場合と一部を抽出する場合の区別がない
   - LLMが勝手に決めている

3. **japanese_sentenceの活用不足**
   - 日本語原文を持っているのに、表示位置が不適切
   - beforeとの対応関係が分かりにくい

---

## 💡 解決策

### 解決策1: before/after表示の統一

#### 実装方法
**プロンプトに明記:**
```
【before/after表示ルール】
- beforeには必ず**完全な文**を表示すること
- 一部だけを抽出しない
- 文の区切りは . ! ? で判定
```

#### 実装箇所
- `prompts_translation_simple.py`: CORRECTION_PROMPT_MIYAZAKI_TRANSLATION
- 修正箇所: beforeの生成ルール部分

---

### 解決策2: 日本語訳の表示位置変更

#### 実装方法A（プロンプトで指示）
```
【日本語訳の表示位置】
- japanese_sentenceは1文目の直後に表示
- フォーマット: "1文目: （日本語訳）"

出力例:
1文目: （その研究では、参加者は3つの異なるグループに分けられた。）
❌ were divide into
→
✅ were divided into
```

#### 実装方法B（フロントエンド変更）
- `static/main.js`で表示順序を変更
- `japanese_sentence`を最初に表示
- その後にbefore/afterを表示

---

### 解決策3: 💡（改善提案）の完全廃止

#### 新しいルール
**2レベルのみに単純化:**
1. **❌ 減点レベルの明確な間違い**
   - 文法エラー
   - 語法エラー
   - スペルミス
   - 主語述語の不一致

2. **✅ 正しい表現（変更不要）**
   - 文法的に正しい
   - 意味が通る
   - 改善提案はしない

#### 判定基準（明確化）
**❌（減点レベル）の例:**
- 三単現のsがない: `He go` → `He goes`
- 時制の一致: `He said he is` → `He said he was`
- 受動態の形: `were divide` → `were divided`
- 冠詞の誤り: `a informations` → `information`

**✅（正しい表現）の例:**
- `tend to improve` ← 文法的に正しい
- `show an improvement` ← こちらも正しい
- **どちらも正解として扱い、改善提案しない**

#### プロンプトの修正
```
【重要】💡での改善提案は一切行わない

以下の場合のみ❌として指摘する：
1. 文法的に明確に間違っている
2. 語法として不自然で減点される
3. 意味が不明確になる

以下は❌として指摘しない：
1. より良い表現があるが、現在の表現も正しい
2. 好みや文体の違い
3. ネイティブならこう言う、という類の提案
```

---

## 📝 実装計画

### Phase 1: プロンプト修正（最優先）

#### ファイル: `prompts_translation_simple.py`

**修正箇所1: 💡の廃止**
```python
# 【修正前】
"""
添削ポイントのレベル:
- ❌ 文法的な間違い
- ✅ 正しい表現
- 💡 より良い表現への改善提案
"""

# 【修正後】
"""
添削ポイントのレベル（2レベルのみ）:
- ❌ 減点レベルの明確な間違い（文法エラー、語法エラー、主述不一致など）
- ✅ 正しい表現（変更不要）

【重要】好みや文体の違いによる改善提案は一切行わない。
学生の表現が文法的に正しく意味が通る場合、そのまま✅として扱う。
"""
```

**修正箇所2: before/after表示ルール**
```python
"""
【before/after表示ルール】
- beforeには必ず完全な文を表示すること
- 一部だけを抽出しない（例: "were divide into" ではなく "The participants were divide into three groups."）
- 文の区切りは . ! ? で判定
"""
```

**修正箇所3: 日本語訳の表示位置**
```python
"""
【日本語訳の表示位置】
- japanese_sentenceは添削ポイントの最初に表示
- フォーマット: "N文目: （日本語訳）"

出力例:
1文目: （その研究では、参加者は3つの異なるグループに分けられた。）
❌ The participants were divide into three groups.
→
✅ The participants were divided into three groups.
理由: divide（動詞：分ける）／divided（過去分詞：分けられた）で、過去分詞形が必要です。
"""
```

---

### Phase 2: バリデーション強化（中優先）

#### ファイル: `llm_service.py`

**追加機能: 💡ポイントの自動除外**
```python
def filter_correction_points(points: List[CorrectionPoint]) -> List[CorrectionPoint]:
    """
    💡レベルのポイントを除外する
    
    Args:
        points: 添削ポイントリスト
    
    Returns:
        ❌と✅のみのリスト
    """
    filtered = []
    for point in points:
        if point.level == "💡改善提案":
            logger.info(f"Filtered out suggestion: {point.before} -> {point.after}")
            continue
        filtered.append(point)
    
    return filtered
```

**適用箇所:**
```python
# correct_translation() 内
correction_result = CorrectionResponse(**data)

# 💡ポイントを除外
correction_result.points = filter_correction_points(correction_result.points)

return correction_result
```

---

### Phase 3: モデル調整（低優先）

#### ファイル: `models.py`

**CorrectionPointのlevel定義を変更:**
```python
class CorrectionPoint(BaseModel):
    """添削ポイント"""
    japanese_sentence: Optional[str] = Field(None, description="対応する日本語の原文（翻訳形式）")
    before: str = Field(..., min_length=1, description="修正前の表現（完全な文）")
    after: str = Field(..., min_length=1, description="修正後の表現（完全な文）")
    reason: str = Field(..., min_length=1, description="修正理由")
    level: Optional[str] = Field(None, description="レベル（❌減点対象、✅正しい表現）")
    alt: Optional[str] = Field(None, description="別の表現（オプション）")
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v):
        """levelが❌または✅のみ許可"""
        if v and v not in ["❌減点対象", "✅正しい表現"]:
            raise ValueError(f"level must be '❌減点対象' or '✅正しい表現', got: {v}")
        return v
```

---

## 🧪 テストケース

### テストケース1: before/after表示の統一

**入力:**
```
学生の英文: The participants were divide into three groups.
```

**期待される出力:**
```
1文目: （参加者は3つのグループに分けられた。）
❌ The participants were divide into three groups.
→
✅ The participants were divided into three groups.
理由: divide（動詞：分ける）／divided（過去分詞：分けられた）で、過去分詞形が必要です。
```

**NG例（一部表示）:**
```
❌ were divide into
→
✅ were divided into
```

---

### テストケース2: 💡の除外

**入力:**
```
学生の英文: Group A tended to improve their concentration.
```

**期待される出力（💡廃止後）:**
```
✅ Group A tended to improve their concentration.
1文目: （Aグループは集中力が向上する傾向が見られた。）
理由: 文法的に正しく、意味も明確です。
```

**NG例（💡がある）:**
```
💡 Group A tended to improve their concentration
→
✅ Group A showed an improvement in concentration
```

---

### テストケース3: 減点レベルの判定

**正しく❌とすべき例:**
```
❌ A study showed that repetitive learning are effective.
      （単数主語に複数動詞 → 減点対象）
```

**❌としてはいけない例（文法的に正しい）:**
```
✅ I think this method is useful.
   （"I believe"の方が良いかもしれないが、文法的には正しい）
```

---

## 📊 実装の優先順位

| Phase | タスク | 優先度 | 理由 |
|-------|--------|--------|------|
| 1 | プロンプト修正（💡廃止） | 🔴 最高 | 問題の根本原因 |
| 1 | before/after全文表示 | 🔴 最高 | ユーザー体験に直結 |
| 1 | 日本語訳位置変更 | 🟡 高 | 視認性向上 |
| 2 | バリデーション追加 | 🟢 中 | 保険として有用 |
| 3 | モデル調整 | 🔵 低 | 任意（プロンプトで十分） |

---

## 🎯 期待される効果

### 効果1: ユーザー体験の向上
- 統一された表示で混乱がなくなる
- 日本語訳が見やすくなる
- 不要な改善提案がなくなる

### 効果2: システムの単純化
- 💡の判定ロジックが不要になる
- プロンプトがシンプルになる
- LLMの判断が一貫する

### 効果3: 設計思想の実現
- **「ユーザーの英文を尊重」** が徹底される
- 減点対象のみに集中できる
- より公平な添削

---

## 📝 GPTへの相談ポイント

### 質問1: プロンプト設計
💡（改善提案）を完全廃止し、❌（減点対象）と✅（正しい表現）の2レベルのみにする場合、どのようにプロンプトを修正すべきか？

**特に知りたいこと:**
- 「減点レベル」の明確な定義方法
- LLMが主観で改善提案をしないようにする強制方法
- 一貫した判定を保証する方法

### 質問2: before/after表示の統一
beforeに完全な文を表示させるための効果的なプロンプト指示は？

**特に知りたいこと:**
- 一部抽出を防ぐ方法
- 文の区切りを正確に判定させる方法

### 質問3: 日本語訳の表示位置
日本語訳を添削ポイントの最初に表示させる方法は？

**選択肢:**
A) プロンプトで出力順序を指定
B) フロントエンドで表示順序を変更
C) LLMの出力をパース後に並び替え

**どれが最も確実か？**

---

## 📂 関連ファイル

| ファイル | 役割 | 修正箇所 |
|---------|------|---------|
| `prompts_translation_simple.py` | 添削プロンプト定義 | 💡廃止、before/after全文表示、日本語訳位置 |
| `llm_service.py` | 添削処理ロジック | 💡フィルタリング、バリデーション |
| `models.py` | データモデル | CorrectionPoint.levelの定義 |
| `static/main.js` | フロントエンド | 表示順序の調整（オプション） |

---

**作成者**: fumichuki  
**作成日**: 2026年1月29日  
**目的**: GPTへの相談用・実装計画書
