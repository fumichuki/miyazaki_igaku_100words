# 添削品質に関するフィードバック (2026-01-30)

## 問題のある添削例

### 1文目の問題
**日本語原文**: このように、この映画のラストシーンは観客に深い感動を与えた。

**ユーザーの英訳**: The scene of this movie gave the audience a deep emotion.

**問題点**: "ラストシーン (last scene)" が訳されていない

**添削結果**: ✅ 正しいと判定されてしまった

**期待される添削**:
```
❌ The scene of this movie gave the audience a deep emotion.
→ ✅ The last scene of this movie gave the audience deep emotion.

reason: "ラストシーン"を"last scene"と訳す必要があります。また、"deep emotion"は"deep emotions"（複数形）または"deep impression"の方が自然です。
```

---

### 2文目の問題
**日本語原文**: 主人公が過去の過ちを乗り越え、再生への道を歩み始める姿は、多くの人々に希望と勇気を与えるだろう。

**ユーザーの英訳**: The main character overcame his past mistakes and started to walk the road to reborn, so it will give many people hope and courage

**問題点**: 
- "road to reborn" は文法的に誤り（rebornは動詞なので "road to rebirth" または "path to recovery/redemption"）
- ピリオドがない

**添削結果**: ピリオドを追加しただけで、"road to reborn"の誤りが指摘されていない

**期待される添削**:
```
❌ The main character overcame his past mistakes and started to walk the road to reborn, so it will give many people hope and courage
→ ✅ The main character overcame his past mistakes and started to walk the road to rebirth, so it will give many people hope and courage.

reason: "reborn"は動詞なので、"road to reborn"は文法的に誤りです。"road to rebirth"（名詞）または"path to recovery"が正しい表現です。
```

---

### 3文目の問題
**日本語原文**: 特に、彼が静かに微笑むシーンは、人生の困難を乗り越えた者だけが持つ安堵感を見事に表現している。

**ユーザーの英訳**: Especially, where he smiles quietly shows the relief that only someone who has overcome hard times can feel.

**問題点**: "where he smiles quietly" は不完全な関係詞節（"the scene where" または "when" が必要）

**添削結果**: before と after が全く同じで、修正されていない

**期待される添削**:
```
❌ Especially, where he smiles quietly shows the relief that only someone who has overcome hard times can feel.
→ ✅ Especially, the scene where he smiles quietly shows the relief that only someone who has overcome hard times can feel.

reason: "where he smiles quietly"は不完全です。"the scene where"のように先行詞が必要です。または"when he smiles quietly"と書くこともできます。
```

---

## 根本原因

現在のシステムでは、LLM (GPT-4o) が以下のような誤りを見逃す傾向があります：

1. **語彙の抜け落ち** (例: "ラストシーン" → "last scene" の "last" が抜けている)
2. **品詞の誤り** (例: "reborn" (動詞) を名詞として使用)
3. **不完全な文構造** (例: 関係詞節に先行詞がない)

## 対策案

### 短期対策
プロンプトに以下の指示を追加：

```
🚨【重要】以下の点を必ずチェックすること🚨
1. **語彙の抜け**: 日本語原文の全ての重要語彙が英訳されているか
   - 例: "ラストシーン" → "last scene" (lastが必要)
2. **品詞の誤り**: 動詞を名詞として、形容詞を動詞として使っていないか
   - 例: "road to reborn" → reborn は動詞なので "road to rebirth" が正しい
3. **不完全な文構造**: 関係詞節に先行詞があるか、接続詞の後に節があるか
   - 例: "where he smiles" → "the scene where he smiles" が必要
```

### 中長期対策
- LLMモデルのファインチューニング
- より詳細な文法チェックルールの実装
- 人間による品質チェックとフィードバックループの構築
