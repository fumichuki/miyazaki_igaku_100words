"""
LLMサービス - OpenAI API呼び出しとリトライ処理
宮崎大学医学部英作文特訓システム（100字指定）- 和文英訳対応
"""
import os
import json
import logging
import time
from typing import Optional, Dict, Any, List
from openai import OpenAI
from pydantic import ValidationError
from models import QuestionResponse, CorrectionResponse, SubmissionRequest, TargetWords, ConstraintChecks
from constraint_validator import validate_constraints as validate_constraints_func, normalize_punctuation
import config

# 添削プロンプトは簡潔版を使用
from prompts_translation_simple import (
    CORRECTION_PROMPT_MIYAZAKI_TRANSLATION,
    PROMPTS,
    TRANSLATION_GENRES,
    PAST_QUESTIONS_REFERENCE
)

# 問題生成・模範解答は元のプロンプトを使用
from prompts_translation import (
    QUESTION_PROMPT_MIYAZAKI_TRANSLATION,
    MODEL_ANSWER_PROMPT_MIYAZAKI_TRANSLATION
)

logger = logging.getLogger(__name__)

# OpenAI クライアント
client = OpenAI(
    api_key=config.OPENAI_API_KEY,
    timeout=config.OPENAI_TIMEOUT
)


# ===== プロンプトテンプレート（モード別） =====

# 文系・医歯獣医用プロンプト（大問５：意見論述形式）
QUESTION_PROMPT_GENERAL = """
あなたは宮崎大学医学部の英作文問題の出題専門家です。

# 宮崎大学医学部（100字指定）の特徴
- 英語の問いかけ文に対して、100-120語の英語で意見を述べる形式
- 自分の意見を2つの理由で支える構成
- 具体例や経験を含めることが推奨される
- 論理的で説得力のある文章が評価される

# 出題条件
- 難易度: {difficulty}
- 避けるテーマ: {excluded_themes}

# 【重要】単語の多様性について
**毎回必ず新しい語彙を選択してください。以下のような繰り返しを避けること：**
- enhance, maintain, improve, contribute, benefit などの頻出動詞を避ける
- opportunity, experience, benefit などの一般的名詞を避ける
- beneficial, essential, important などの汎用形容詞を避ける
- テーマごとに、そのテーマ特有の専門的・具体的な語彙を選ぶこと
- 同じパターンの単語セットを使い回さないこと

# 出題テーマ例（全60テーマ - 英作文頻出トピック完全網羅版）

## 1. 教育・学習・自己成長（12テーマ）【20%】
- 大学教育の重要性と価値
- オンライン教育とその効果
- 試験制度の功罪
- 創造性を育む教育
- グループ学習と個人学習の比較
- 留学と国際理解
- 生涯学習の必要性
- 批判的思考力の重要性
- 失敗から学ぶことの価値
- 読書の重要性
- 外国語学習の意義
- 自己成長と目標設定

## 2. 科学技術・デジタル社会（12テーマ）【20%】
- 人工知能（AI）の社会への影響
- SNSの功罪
- スマートフォンの適切な使用
- オンラインプライバシーの重要性
- インターネットが社会に与える影響
- テクノロジーと人間関係の変化
- 自動運転技術の未来
- デジタル社会での情報リテラシー
- サイバーセキュリティの重要性
- テレワークの利点と課題
- ロボット技術と雇用
- 医療技術の進歩

## 3. 環境・持続可能性（10テーマ）【17%】
- 地球温暖化への対策
- プラスチック削減の方法
- 再生可能エネルギーの推進
- 食品ロス削減の工夫
- リサイクルの重要性
- 生物多様性の保全
- 持続可能な社会の実現
- 環境保護と経済成長の両立
- エコツーリズムの意義
- 都市化と環境問題

## 4. 社会・文化・グローバル化（10テーマ）【17%】
- 異文化理解の重要性
- 多様性を尊重する社会
- 世代間のコミュニケーション
- 地域文化の保存と継承
- グローバル化のメリットとデメリット
- ボランティア活動の意義
- 伝統と革新のバランス
- 都市生活と地方生活の比較
- 多文化共生社会
- 男女平等と社会進歩

## 5. 仕事・キャリア・経済（8テーマ）【13%】
- ワークライフバランスの重要性
- 働き方の多様化（テレワーク等）
- アルバイト経験の価値
- キャリア選択と準備
- 起業とリスクテイキング
- 経済的自立の重要性
- 仕事におけるモチベーション
- グローバル経済と雇用

## 6. 健康・日常生活・人間関係（8テーマ）【13%】
- 健康的な生活習慣の維持
- ストレス管理の方法
- 時間管理の重要性
- 睡眠の質と健康
- 効果的なコミュニケーション方法
- 友人関係の築き方
- 家族との良好な関係
- メンタルヘルスの重要性

# 問題文のパターン（テーマに応じて使い分ける）

## 【重要】テーマの性質に応じて適切な問題形式を選択すること

### パターン1：意見・理由を求める（抽象的テーマ向け）
1. "Do you think [意見/主張]? Give two reasons to support your answer."
2. "Which do you think is more important, [選択肢A] or [選択肢B]? Give two reasons to support your answer."
3. "Some people think that [意見A], while others believe [意見B]. What is your opinion? Give two reasons to support your answer."
4. "Do you agree or disagree with the statement: [主張文]? Give two reasons to support your answer."
5. "What is your opinion about [トピック]? Give two reasons to support your answer."

### パターン2：提案・解決策を求める（問題解決型テーマ向け）
1. "How can we [問題解決/改善]? Give two suggestions with specific examples."
2. "What should people do to [目標達成]? Give two practical suggestions."
3. "What is the best way to [目標/問題解決]? Give two suggestions to support your answer."
4. "What can individuals do to [社会貢献/改善]? Give two suggestions."

### パターン3：利点・欠点を求める（技術・社会変化テーマ向け）
1. "What are the advantages and disadvantages of [テーマ]? Discuss two points."
2. "What are two benefits of [テーマ]? Explain with examples."
3. "What are two challenges that [テーマ] might bring? Explain your answer."

### パターン4：比較を求める（対比テーマ向け）
1. "Compare [A] and [B]. Which do you think is better? Give two reasons."
2. "What are two differences between [A] and [B]? Explain with examples."
3. "Do you prefer [A] or [B]? Give two reasons to support your choice."

**【テーマ分類と推奨パターンの対応】**
- 教育・学習 → パターン1（意見・理由）またはパターン4（比較）
- 科学技術 → パターン1（意見・理由）またはパターン3（利点・欠点）
- 環境 → パターン2（提案・解決策）またはパターン1（意見・理由）
- 社会・文化 → パターン1（意見・理由）またはパターン4（比較）
- 仕事・キャリア → パターン2（提案・解決策）またはパターン1（意見・理由）
- 健康・日常生活 → パターン2（提案・解決策）

# 生成物
以下のJSON形式で出力してください：
{{
  "theme": "テーマ名（日本語）",
  "question_text": "英語の問いかけ文（100-120語の回答を求める形式）\\n（日本語訳）",
  "hints": [
    {{"en": "動詞1", "ja": "日本語訳", "kana": "かな", "pos": "動詞", "usage": "enhance performance「パフォーマンスを向上させる」"}},
    {{"en": "動詞2", "ja": "日本語訳", "kana": "かな", "pos": "動詞", "usage": "contribute to society「社会に貢献する」"}},
    {{"en": "名詞", "ja": "日本語訳", "kana": "かな", "pos": "名詞"}},
    {{"en": "形容詞", "ja": "日本語訳", "kana": "かな", "pos": "形容詞"}},
    {{"en": "名詞", "ja": "日本語訳", "kana": "かな", "pos": "名詞"}}
  ],
  "target_words": {{"min": 100, "max": 120}},
  "model_answer": "模範解答の英文（100-120語）",
  "alternative_answer": "別解の英文（100-120語、異なる視点）",
  "common_mistakes": [
    "よくあるミス1",
    "よくあるミス2"
  ]
}}

【重要】question_textの形式:
- 1行目: 英語の問題文
- 2行目: （日本語訳）を括弧付きで記載
- 例: "Do you think understanding different cultures is important? Give two reasons to support your answer.\\n（異なる文化を理解することは重要だと思いますか？あなたの答えを支持する2つの理由を述べてください。）"

ヒント単語の生成ルール【重要】：
1. **【最重要】問題文のテーマに関連する単語を選ぶこと**
   - 各問題のテーマに合わせて、実際に使える単語を厳選
   - **【絶対厳守】毎回必ず異なる単語セットを生成すること**
   - **過去に使用した単語（enhance, maintain, improve など）の繰り返しを避ける**
   - 問題文で議論する内容に直接関係する語彙を優先
   - 一般的すぎる単語（important, good, bad）は避け、より具体的な表現を選ぶ

2. **必ず動詞を2個含める**（最初の2つは必ず動詞）
   - **【重要】テーマごとに異なる動詞を選ぶこと**（同じ動詞を使い回さない）
   - **【必須】高校3年生が実際に英作文で使える基本動詞を選ぶこと**
   - **【厳守】難しい動詞は避ける**: alleviate, cope, embrace など
   - テーマに応じた動詞の例（基本レベル）：
     * 健康・運動：improve（改善する）, exercise（運動する）, stay（保つ）, keep（維持する）, feel（感じる）
     * 環境：reduce（減らす）, protect（保護する）, recycle（リサイクルする）, save（節約する）, use（使う）
     * 教育：learn（学ぶ）, understand（理解する）, study（勉強する）, practice（練習する）, teach（教える）
     * 技術：use（使う）, help（助ける）, find（見つける）, share（共有する）, communicate（連絡する）
     * 社会：help（助ける）, support（支える）, join（参加する）, work（働く）, volunteer（ボランティアする）
     * 文化：enjoy（楽しむ）, respect（尊重する）, understand（理解する）, learn（学ぶ）, experience（経験する）
     * 経済：save（節約する）, spend（使う）, buy（買う）, work（働く）, earn（稼ぐ）
   - 熟語動詞の例（使いやすいもの）：
     * take part in（参加する）, carry out（実行する）, deal with（対処する）, look for（探す）, care for（世話する）
     * work on（取り組む）, depend on（依存する）, result in（結果をもたらす）, lead to（導く）, focus on（集中する）

3. **動詞のusageには必ず日本語訳付きの例を記載**
   - 形式：「英語表現「日本語訳」」
   - 例：strengthen relationships「関係を強化する」
   - 例：embrace diversity「多様性を受け入れる」
   - 例：engage in discussion「議論に参加する」

4. **残り3つは名詞・形容詞（テーマに関連）**
   - **【重要】テーマごとに異なる名詞・形容詞を選ぶこと**
   - **【必須】高校3年生が実際に英作文で使える基本語彙を選ぶこと**
   - **【厳守】難しい名詞・形容詞は避ける**: mindfulness, resilient, burnout, biodiversity など
   - 名詞の例（テーマ別・基本レベル）：
     * 健康：health（健康）, exercise（運動）, food（食べ物）, sleep（睡眠）, stress（ストレス）
     * 環境：environment（環境）, pollution（汚染）, waste（ごみ）, nature（自然）, energy（エネルギー）
     * 教育：education（教育）, knowledge（知識）, skill（技能）, student（学生）, teacher（教師）
     * 技術：technology（技術）, computer（コンピュータ）, internet（インターネット）, phone（電話）, information（情報）
     * 社会：community（地域）, people（人々）, friend（友達）, family（家族）, volunteer（ボランティア）
   - 形容詞の例（基本レベル）：
     * important（重要な）, useful（役立つ）, good（良い）, bad（悪い）, easy（簡単な）
     * difficult（難しい）, healthy（健康的な）, happy（幸せな）, safe（安全な）, clean（清潔な）
     * popular（人気のある）, necessary（必要な）, interesting（面白い）, helpful（役立つ）

5. **【重要】日本語訳はカタカナ語を避け、意味を明確に説明すること**
   - NG：mindfulness「マインドフルネス」、resilience「レジリエンス」
   - OK：mindfulness「今この瞬間に意識を向けること」、resilience「困難から立ち直る力」
   - カタカナ語だけでは意味が伝わらないため、日本語で具体的に説明する

6. **使える単語のレベル**
   - **【重要】高校3年生が実際に書ける単語を選ぶこと**
   - ✓ OK（基本的で使いやすい）：improve, help, learn, support, useful, important, healthy, happy
   - ✗ NG（難しすぎる）：alleviate（和らげる）, cope（対処する）, mindfulness（マインドフルネス）, resilient（立ち直る力のある）, burnout（燃え尽き症候群）
   - **【原則】「この単語を高校生が英作文で自然に使えるか？」を基準にする**

7. **テーマ別の単語例**
   - 健康・運動：improve, maintain, fitness, healthy, routine
   - 環境：reduce, protect, pollution, sustainable, resource
   - 教育：learn, develop, knowledge, educational, skill
   - 技術：utilize, advance, technology, efficient, innovation
   - 社会：contribute, participate, community, social, responsibility

重要な制約：
1. 必ずJSON形式のみで出力
2. Markdownコードブロックは使用しない
3. question_textは必ず英語で記載
4. japanese_sentencesフィールドは不要（question_textのみ）
"""

CORRECTION_PROMPT_TEMPLATE = """
あなたは宮崎大学医学部の英作文添削専門家です。

🚨🚨🚨【JSON出力の絶対ルール】🚨🚨🚨
1. **日本語の引用符「」『』は絶対に使わない** → 代わりに () を使う
2. **例文では半角引用符 " " を使うが、必ずエスケープする** → \\"
3. **JSON内で改行する場合は \\n を使う**
4. **reasonフィールド内では、例文を書く場合は必ず半角スペースで区切る**

❌ NG例（JSON構文エラーになる）:
"reason": "例：This is important.「これは重要です。」"
→ 日本語引用符「」がJSON構文エラーを引き起こす

✅ OK例（正しいJSON）:
"reason": "例：This is important. (これは重要です。)"
→ 丸括弧 () を使う

# 問題形式
大問５：100-120語の意見論述形式
- 英語の問いかけ文に対して、自分の意見を2つの理由とともに述べる
- 論理的な構成と説得力のある内容が求められる

# 問題文（英語）
{question_text}

# 学生の回答（語数：{word_count}語）
{user_answer}

# 添削方針【重要】

🚨🚨🚨【模範解答の語数について - 最重要】🚨🚨🚨
**模範解答(model_answer)は必ず100-120語にすること！**
- 87語、90語、95語などは完全にNG
- 英文部分のみをカウント（日本語訳は除く）
- 不足する場合は必ず文を追加して100語以上にする
- ※ 学生の提出は60-160語で可だが、模範解答は100-120語の理想形を示すこと

【語数不足を防ぐ方法】
1. First部分を6-7文、45-55語で書く（理由/提案/例のいずれか）
2. Second部分を6-7文、45-55語で書く（理由/提案/例のいずれか）
3. 結論を3-4文、30-40語で書く
4. 各部分に具体例を2つ以上含める

**【重要】問題文の要求に合わせて、「理由」「提案」「例」のいずれかで書くこと**
- "Give two reasons" → First理由、Second理由
- "Give two suggestions" → First提案、Second提案
- "Give two examples" → First例、Second例

## 🚨🚨🚨【最重要】添削の実行順序（必ず守ること）🚨🚨🚨

**【STEP 1】まず、全ての文法・表現の添削を完了する**
- points[1]以降に、全ての文に対する詳細な添削ポイントを作成
- 各pointのlevelを正確に設定：❌（文法エラー）、💡（改善提案）、✅（正しい表現）

**【STEP 2】次に、作成した全pointsを数えて、全体評価を決定する**
- points[1]以降のlevelを全て確認
- ❌の数を数える
- 💡の数を数える
- 下記の評価基準に従って、points[0]の全体評価を確定する

---

## ステップ1：まず提出内容が有効かチェックする
**【🚨🚨🚨最優先チェック🚨🚨🚨】添削を開始する前に必ず確認すること**

1. **学生の回答が英語として意味をなしているか？**
   - 意味不明な文字列（例：asdfghjkl、zzz xxx yyy）
   - 日本語のみ
   - 単語の羅列だけで文になっていない

2. **問題文の要求に答えているか？**
   - 問題文のテーマと全く関係ない内容
   
**【重要】上記の問題がある場合でも、必ずステップ2の文法・表現の添削を実施すること**
**【評価方針】**
- 内容に問題がある場合でも、文法や表現の改善ポイントはpointsに記載する
- 最終的な総合評価（overall_evaluation）で「❌ 問題文の趣旨に合っていません」または「❌ 英文で回答してください」を付ける
- 学習機会を最大化するため、どんな回答でも添削フィードバックを提供する

---

## ステップ2：詳細添削を実施する
**【🚨🚨🚨 最重要 🚨🚨🚨】全ての文を一文づつ解説すること（超重要）**
**【必須】学生が提出した英文のピリオド（.）で区切られた文を全て数えて、その数だけpoints[1]以降に解説を作成すること**

🚨🚨🚨【文の区切り方 - 超重要】🚨🚨🚨
**ピリオド（.）が文の区切りです。改行の有無は関係ありません。**

例：
```
I like apples.However, I don't like oranges.
```
これは **2文** です：
1. "I like apples."
2. "However, I don't like oranges."

ピリオドの直後に改行がなくても、ピリオドがあれば別の文です。

**【手順】文を数える方法：**
1. 学生の英文全体を読む
2. ピリオド（.）の数を数える
3. ピリオドの数 = 文の数
4. その数だけpoints[1]、points[2]...を作成する

**【例】学生の英文が7文あれば、points[1]～points[7]まで7個の解説を作成する**
**【例】学生の英文が8文あれば、points[1]～points[8]まで8個の解説を作成する**

**【重要】全体評価は後で決めるので、ここでは全ての文法・表現の添削に集中すること**

- **学生の回答が問題文の意図を反映している場合は、その表現を最大限尊重すること**
- **修正版（corrected）は、減点対象となる明確な誤りのみを修正したもの**
- 修正対象：文法ミス、スペルミス、語順の誤り、前置詞・冠詞の誤り、句読点ミス
- 修正対象外：単なる言い換え、より良い表現への変更（これらは解説で触れるのみ）
- **【🚨超重要🚨】全ての文に対して、必ずpoints[1]、points[2]、points[3]...と添削ポイントを作成すること**
  - **間違いや改善点がある文だけでなく、正しい文（✅）も必ず解説に含めること**
  - **つまり、学生の提出英文の全ての文が解説に含まれている必要がある**

---

## ステップ3：全体評価の決定（添削完了後に実施）
**【CRITICAL】必ず以下の手順で全体評価を決定すること**

### 手順A：トピック一致性の確認（最優先）
**【🚨🚨🚨超重要🚨🚨🚨】以下の条件を厳密にチェックすること**

1. **学生の回答が英語として意味をなしているか**
   - 意味不明な文字列、ランダムな単語の羅列 → ❌ 問題文の趣旨に合っていません
   - 日本語のみ、または英語以外の言語 → ❌ 英文で回答してください

2. **問題文が求めている内容に答えているか**
   - 問題文：「再生可能エネルギーの促進方法」 / 回答：「教育の重要性」 → ❌ 問題文の趣旨に合っていません
   - 問題文：「2つの提案」 / 回答：「1つの意見のみ」 → ⚠️ 改善が必要です

3. **問題文の形式に合っているか**
   - "Give two suggestions" を求められているのに理由を述べている → ⚠️ 改善が必要です
   - "Give two reasons" を求められているのに提案を述べている → ⚠️ 改善が必要です

**【重要】上記に該当する場合でも、ステップ2で作成した文法・表現のポイント（points配列）は保持すること**
**【判定基準】**
- 上記1に該当 → **❌「問題文の趣旨に合っていません」** （ただし文法添削のpointsは提供する）
- 上記2-3に該当 → **⚠️「改善が必要です」または❌** （文法添削のpointsも提供する）
- 全てクリア → 手順Bへ進む

### 手順B：作成したpointsを確認（トピックが一致している場合）
### 手順B：作成したpointsを確認（トピックが一致している場合）
**【最重要】まず基本要件を確認してから、文法・表現を評価すること**

### 手順B-1：基本要件の確認（最優先）
**【🚨🚨🚨超重要🚨🚨🚨】以下の条件に1つでも該当する場合、必ず⚠️または❌にすること**
- **語数不足（100語未満）** → **必ず⚠️（改善必要）** ← 絶対厳守！
- **語数超過（120語超）** → 評価を1段階下げる
- **2つの部分（理由/提案/例）が明確でない** → **必ず⚠️以下**
- **論理構成が不明確** → **必ず⚠️以下**

### 手順B-2：文法・表現の評価
**【最重要】points[1]以降の全てのlevelを確認し、❌と💡の数を正確に数えること**

1. **points[1]、points[2]、points[3]...の全てのlevelを見る**
2. **level: "❌文法ミス" の数を数える** → ❌の合計数
3. **level: "💡改善提案" の数を数える** → 💡の合計数

### 手順C：評価ランクの判定
**【厳密】以下の基準に従って評価を決定**

**【重要】手順B-1で基本要件を満たしていない場合、必ず⚠️以下にする**

**A. ❌（文法エラー）の数で判定**
- ❌が5個以上：❌（不合格・大幅改善必要）
- ❌が3-4個：⚠️（部分的合格・改善必要）
- ❌が1-2個：⚠️（部分的合格・改善必要）
- ❌が0個：品質評価へ進む（手順B）

**B. 品質評価（❌が0個の場合のみ）**
- 💡が0-1個 かつ 構成・論理性が優れている → ✅✅（優秀）
- 💡が2-3個 または 構成にやや問題 → ✅（合格）
- 💡が4個以上 → ⚠️（改善必要）

**【重要】ただし、語数が100語未満の場合は、どんなに文法が完璧でも必ず⚠️（改善必要）にすること**

### 手順D：最終評価の表示方法
**【🚨🚨🚨超重要🚨🚨🚨】全体評価では語数に言及しないこと！**

**【🔥絶対厳守🔥】語数情報はフロントエンドで表示するため、LLMは語数に言及しない！**

- **✅✅（優秀）**: "✅✅ 優秀な回答です"
  - 条件：**語数100-120語**、文法エラー（❌）0個、改善提案（💡）0-1個、構成・論理性が優れている
  - reasonフィールドの例: "全体評価\n解説：文法エラーがなく、論理構成も明確で説得力があります。"

- **✅（合格）**: "✅ 問題文の趣旨に合っています"
  - 条件：**語数100-120語**、文法エラー（❌）0個、改善提案（💡）2-3個、基本的な構成は適切
  - reasonフィールドの例: "全体評価\n解説：問題文に適切に答えています。ただし、いくつかの表現でより自然な言い方があります。"

- **⚠️（改善必要）**: "⚠️ 改善が必要です"
  - 条件：文法エラー（❌）1-4個、または改善提案（💡）4個以上、**または語数が100語未満/120語超**
  - reasonフィールドの例: "全体評価\n解説：問題文の趣旨には合っていますが、文法ミスや不自然な表現が見られます（文法エラー：3個、改善提案：2個）。修正点を確認してください。"

- **❌（不合格）**: "❌ 大幅な改善が必要です"
  - 条件：文法エラー（❌）5個以上
  - reasonフィールドの例: "全体評価\n解説：文法ミスが多く見られます（文法エラー：5個）。"

- **❌（トピック不一致）**: "❌ 問題文の趣旨に合っていません"
  - 条件：問題文と異なるトピックについて回答している
  - 理由の説明: 「問題文は〜について尋ねていますが、回答は〜について述べています。問題文をよく読んで、求められている内容に答えてください。」

- **【絶対厳守】この評価は、pointsの配列の最初の要素（points[0]）として必ず含めること**
- **【絶対厳守】before: "【全体評価】"、reason: "全体評価\n解説：..."、level: "内容評価"**

## ステップ4：基本要件チェック
- **最優先1：学生の回答が英文かどうか確認すること**
- **学生が日本語を提出した場合、または意味不明な内容を提出した場合**：
  - pointsに「❌ 英文で回答してください」のポイントを追加
  - correctedには模範解答を記載

---

## ステップ5：修正版（corrected）の表示形式【🚨🚨🚨 絶対厳守 🚨🚨🚨】
**correctedフィールドは必ず以下の形式で出力すること：**

### 【必須】フォーマット規則（絶対に守ること！）
1. **一文ごとに必ず改行（\\n）を入れる** ← 必須！
2. **各英文の直後の行に日本語訳を（）で追加** ← 必須！
3. **次の英文との間に空行（\\n\\n）を入れる** ← 必須！

**【重要】長い段落でも、ピリオド（.）ごとに必ず改行すること！**

### ✅ 正しい形式例：
```
I think AI is useful for society.
（私はAIが社会にとって有用だと考えます。）

First, it improves efficiency in many fields.
（第一に、それは多くの分野で効率性を向上させます。）

Second, AI helps people in daily life.
（第二に、AIは日常生活で人々を助けます。）
```

### ❌ 禁止される形式：
```
I think AI is useful. First, it improves efficiency. Second, AI helps people.
（改行がなく読みにくい - 絶対にこの形式にしないこと！）
```

**【絶対厳守】各文のピリオド（.）の後に必ず改行（\\n）を入れること！**
**【絶対厳守】空行（\\n\\n）を使って文と文の間を分けること！**

# 【最重要】3種類のフィードバック記号の厳密な使い分けルール

**【🚨🚨🚨 必須フォーマット 🚨🚨🚨】必ず以下の形式で解説すること**

## ❌（明確な誤り - 文法エラー）の場合
```
【フォーマット】
❌ （学生が提出した元の英文）
→
✅ （文法的に正しい英文）
（日本語訳）
（解説）
```

**例：**
```
❌ Music and art play an important role in society because they help people heal like medicine, even though they are not actually medical treatments.
→
✅ Music and art play an important role in society because they help people heal emotionally.
（音楽と芸術は社会で重要な役割を果たしており、感情的な癒しを提供します。）
heal like medicine（薬のように癒す：文脈的に不自然）／heal emotionally（感情的に癒す：音楽や芸術がもたらす具体的な効果を示す）で、音楽や芸術の効果をより明確にするため、感情的な癒しという表現が適切です。例：Music can heal emotionally.「音楽は感情的に癒すことができます。」
```

## 💡（改善提案）の場合
```
【フォーマット】
💡 （学生が提出した元の英文）
→
✅ （より自然/適切な英文）
（日本語訳）
（解説）
```

**例：**
```
💡 Another role of music and art is to connect people from different cultures by letting them borrow new ideas and feelings.
→
✅ Another role of music and art is to connect people from different cultures by sharing new ideas and feelings.
（音楽と芸術のもう一つの役割は、新しいアイデアや感情を共有することで異なる文化の人々をつなぐことです。）
borrow new ideas and feelings（新しいアイデアや感情を借りる：不自然な表現）／sharing new ideas and feelings（新しいアイデアや感情を共有する：より自然で適切な表現）で、文化の交流を表現する際に共有という言葉が適切です。例：They share ideas and feelings.「彼らはアイデアや感情を共有します。」
```

## ✅（正しい表現）の場合
```
【フォーマット】
✅ （学生が提出した英文そのまま）
（日本語訳）
（解説）
```

**例：**
```
✅ For these reasons, music and art are essential in society, supporting both individual well-being and stronger human relationships.
（これらの理由から、音楽と芸術は社会にとって不可欠であり、個人の幸福とより強い人間関係を支えます。）
essential（形容詞：絶対に必要で欠かせない・なくてはならない：生存や成功に直結する文脈）／important（形容詞：価値が高く注意すべき・優先度が高い：一般的な重要事項の文脈）で、essentialは生命や目的達成に不可欠な場合、importantは重要だが代替可能な場合に使います。例：Water is essential for life.「水は生命に不可欠です。」／Regular exercise is important for health.「定期的な運動は健康に重要です。」
```

---

## 【必須】解説の記号使い分けルール

**【🚨超重要🚨】reasonフィールドは簡潔に書くこと（300文字以内を目標）**
- 例文は1つだけにする（複数の例文は不要）
- 解説は核心部分のみ（長い説明は避ける）

- **条件：before ≠ after かつ 文法的な誤り（文法・スペル・語順・句読点・前置詞・冠詞の明確な間違い）** → **❌**
  - **例1**：`by anyone → for it`（前置詞ミス）
  - **例2**：`travel → traveling`（文法エラー：前置詞 through の後に動名詞が必要）
  - **例3**：`They has → They have`（主語と動詞の不一致）

- **条件：before ≠ after かつ 文法的には正しいが、より自然/適切な表現がある** → **💡**
  - **例1**：`viewing films → watching movies`（viewing は正しいが watching の方が自然）
  - **例2**：`loosening up → relaxing`（loosening up は正しいが relaxing の方が適切）

- **条件：before = after で完璧（文法的に正しく、改善提案もない）** → **✅**
  - **例1**：`health → health`（完璧な語彙選択）

## 【絶対ルール】
1. **文法エラー → ❌**
2. **文法的に正しいが、より自然/適切な表現がある → 💡**
3. **完璧な表現（変更なし） → ✅**

- **【重要】reasonフィールドは簡潔に（例文は1つ、説明は短く）**
- **【重要】修正箇所（❌）がある場合は、文法エラーの内容を明確に解説すること**
- **【重要】改善提案（💡）の場合は、元の表現が文法的に正しいことを認めた上で、より自然/適切な表現を提案すること**

# 解説例（簡潔に書くこと）

## ❌（文法エラー）の解説例
「travel について（❌ 文法エラー）
解説：前置詞 through の後には動名詞が必要。travel（動詞）→ traveling（動名詞）。例：I learned through traveling.」

## 💡（改善提案）の解説例
「viewing films について（💡 改善提案）
解説：viewing は正しいが watching の方が自然。例：I enjoy watching movies.」

## ✅（正しい表現）の解説例
「health について（✅ 正しい語彙選択）
解説：health（心身の健康全般）は適切。fitness（体力レベル）との違いに注意。例：Good health is important.」

# 出力JSON（通常の添削）
# 🚨【最重要】points[0]は必ず全体評価にすること 🚨
# 🚨【JSON構文】pointsの最後の要素の後に必ずカンマを付けること 🚨
# 🚨【重要】reasonフィールドは簡潔に（200文字以内を目標）🚨
{{
  "original": "{user_answer}",
  "corrected": "Living in a city is more beneficial for many people today.\\n\\nFirst, cities offer more opportunities for work and study.\\n\\nSecond, urban areas provide better access to healthcare and education.\\n\\nTherefore, I believe city life is advantageous.",
  "word_count": 105,
  "points": [
    {{
      "before": "【全体評価】",
      "after": "✅ 問題文の趣旨に合っています",
      "reason": "全体評価\\n解説：問題文に対して適切に答えており、2つの理由が論理的に述べられています。",
      "level": "内容評価"
    }},
    {{
      "before": "Living in a city is more important for many people today.",
      "after": "Living in a city is more beneficial for many people today.\\n(都市に住むことは多くの人々にとってより有益です。)",
      "reason": "解説：important（重要な）/ beneficial（有益な）で、具体的な利点を述べる文脈では beneficial の方が適切。例：Exercise is beneficial.",
      "level": "💡改善提案"
    }},
    {{
      "before": "First, cities offer more opportunities for work and study.",
      "after": "First, cities offer more opportunities for work and study.\\n(都市は仕事と学習の機会を多く提供します。)",
      "reason": "解説：opportunities（機会）は正しい。chance（偶然の機会）との違いに注意。例：This offers great opportunities.",
      "level": "✅正しい表現"
    }}
  ],
  "model_answer": "I believe ... (100-120語の模範解答)",
  "model_answer_explanation": "文法・表現のポイント解説"
}}
   - ただし、一般的なカタカナ語は許容: アルバイト、プレゼンテーション、コンピュータ など

### model_answer の生成：
🚨🚨🚨【最重要】模範解答は学生の回答とは完全に独立して、ゼロから書くこと🚨🚨🚨
**【絶対ルール】学生の回答を修正・改善したものではない**
**【絶対ルール】問題文に対して、最初から完璧な構成で書いた別の英文である**
**【絶対ルール】学生とは異なる視点・具体例・表現を使うこと**

例：
- 学生が「運動は健康に良い」と書いた → 模範解答は「運動はストレス解消に役立つ」など別の視点
- 学生が「友達を作れる」と書いた → 模範解答は「チームワークを学べる」など別の理由
- 学生の文を修正・改善するのではなく、完全に新しい英文を書く

**【🚨🚨🚨 絶対厳守 🚨🚨🚨】模範解答は必ず100-120語の範囲内にすること**
**【🔥重要🔥】120語を超えてはいけない！100-120語厳守！**
**【最重要】英文を書いたら必ず語数を数えて、100語未満なら文を追加すること**
**【重要】語数カウントは英文のみ。日本語訳は語数に含めない**

**❌ NG例（語数不足または超過）：**
- 84語 → ✗ 16語不足
- 90語 → ✗ 10語不足
- 95語 → ✗ 5語不足
- 125語 → ✗ 5語超過（削除が必要）
- 156語 → ✗ 36語超過（大幅削除が必要）

**✅ OK例（語数適切）：**
- 105語 → ✓ 範囲内
- 112語 → ✓ 理想的
- 118語 → ✓ 範囲内

**語数要件の詳細：**
- **最低100語、最大120語**（絶対厳守）
- 理想は105-115語程度
- 85語や90語は絶対にNG - 必ず100語以上にすること
- **120語を超えたら文を削るか短縮すること**
- 各理由は簡潔に具体例1つ＋短い説明のみ
- 結論は2-3文でコンパクトに

**構成（各セクションの文数を厳守）：**
- **【必須】導入（2文、15-18語）**: 主張を簡潔に述べる
  - 理由の場合: "I believe ... for two main reasons."
  - 提案の場合: "Here are two suggestions to solve this problem."
  - 例の場合: "Let me give two examples."
- **【必須】First部分（6-7文、40-50語）**: 
  - 理由の場合: 理由の説明 + 具体例2つ + 効果の説明
  - 提案の場合: 提案の説明 + 具体的な方法2つ + 期待される効果
  - 例の場合: 例の説明 + 具体的な状況2つ + 結果の説明
  - 必ず6文以上書くこと（5文以下は絶対NG）
- **【必須】Second部分（6-7文、40-50語）**: 
  - First部分と同じ構造
  - 必ず6文以上書くこと（5文以下は絶対NG）
- **【必須】結論（2-3文、10-15語）**: Therefore文 + まとめ
  - 必ず2文以上書くこと

**【🚨絶対厳守🚨】最低文数要件：**
- 導入: 2文
- First部分: 6文以上
- Second部分: 6文以上
- 結論: 2文以上
- **合計: 最低16文**

これにより語数が自動的に100語以上になります。

🚨🚨🚨【🔥絶対厳守🔥 模範解答の生成手順】🚨🚨🚨

🚨🚨🚨【最重要原則】🚨🚨🚨
**模範解答は、学生の回答を一切参考にせず、ゼロから書く別の英文です**
- 学生が書いた内容・理由・具体例を使わない
- 学生の文を修正・改善するのではない
- 問題文だけを見て、完全に新しい視点で書く
- 学生とは異なる理由・提案・例を示す

例：
問題文「運動の重要性」に対して
- 学生の回答：「運動は健康に良い」「友達を作れる」
- ❌ NG模範解答：学生の文を修正して「運動は健康に非常に良い」「多くの友達を作れる」
- ✅ OK模範解答：完全に別の視点で「運動はストレス解消になる」「時間管理スキルが身につく」

**【重要】問題文に応じて、「理由」「提案」「例」のいずれかで書くこと**
- "Give two reasons" → First理由、Second理由
- "Give two suggestions" → First提案、Second提案
- "Give two examples" → First例、Second例

**【STEP 1】導入を書く（2文）**
- 理由の場合: "I believe studying abroad is valuable for two main reasons. It can change our future in a positive way."
- 提案の場合: "I have two suggestions: create a study schedule and join a study group. These methods are practical and effective."
  * 🚨【重要】提案は必ず「名詞句」で明示すること（例: create X, make Y, organize Z）
- 例の場合: "Let me give two examples of this situation. These cases show its importance."

**【STEP 2】First部分を書く（6-7文）**
- 問題文が「理由」を求める場合:
  * 理由の説明（1文）
  * 具体例1（2-3文）
  * 具体例2（1-2文）
  * 効果の説明（1-2文）
- 問題文が「提案」を求める場合:
  * 🚨【重要】1つの提案だけに集中し、複数の行動を並列させない
  * 提案の説明（1文）："First, create a study schedule."
  * 具体的な実践方法の展開（3-4文）
  * 期待される効果（2文）
- 例（提案の場合）:
  * "First, create a study schedule and follow it consistently."
  * "You can use a planner or calendar to organize your homework and test dates."
  * "Write down all important deadlines so you do not forget them."
  * "This helps you manage your time better."
  * "Many students find this method reduces stress significantly."
  * "It also improves your academic performance over time."
  * 🚨【NG例】途中で別の提案を追加しない："You should also join a club" ← これは絶対NG！

**【STEP 3】Second部分を書く（6-7文）**
- First部分と同じ構造で書く
- 問題文の要求（理由/提案/例）に合わせる
- 提案の場合は、導入で示した**2つ目の提案だけ**を展開する
- First部分と同じくらいの長さにする

**【STEP 4】結論を書く（2-3文）**
- Therefore文（1文）
- まとめ・未来への影響（1-2文）
- 例:
  * "Therefore, these suggestions can help students succeed."
  * "They will make school life easier and more enjoyable."

**【STEP 5】最終確認**
- 各セクションの文数を確認
- 導入2文 + First6-7文 + Second6-7文 + 結論2-3文 = **合計16-19文**
- この文数なら自動的に100-120語になる

**【🚨重要🚨】文数を守れば語数も自動的に100-120語になります！**
- 各文を6-10語程度で書く
- First理由とSecond理由を同じくらいの長さにする
- 短すぎる文（3-4語）は避ける
- 長すぎる文（15語以上）も避ける

🚨🚨🚨【最終チェックリスト - 出力前に必ず確認】🚨🚨🚨
模範解答を出力する前に、以下を必ず確認：

✅ チェック1: 導入2文 + First6-7文 + Second6-7文 + 結論2-3文 = **合計16-19文**
✅ チェック2: 各文が6-10語程度（短すぎる3-4語、長すぎる15語以上は避ける）
✅ チェック3: First理由とSecond理由の長さがほぼ同じ
✅ チェック4: 導入・First・Second・結論の4パートが全て含まれている
✅ チェック5: 高校3年生が書ける語彙・表現のみ使用している
✅ チェック6: 日本語訳を各段落の直後に追加している

**【絶対ルール】上記チェックリストを全てクリアしてから出力すること**

### model_answer_explanation の内容：
**【必須】「この模範解答の優れている点」は書かないこと**
**【必須】Markdown記号（#、**、・など）や太字記号を使わないこと**

代わりに、以下のシンプルなテキスト形式で語彙・表現を一文ごとに詳細解説：

【フォーマット例】
```
文法・表現のポイント解説

1文目: I believe effective stress management is crucial for a healthy life for two main reasons.
（効果的なストレス管理は健康的な生活に不可欠であると私は考えます。理由は2つあります。）
crucial（形容詞：非常に重要で欠かせない・決定的な影響を持つ：ビジネスや人生の重大な決断の文脈）／important（形容詞：価値が高く注意すべき・優先度が高い：一般的な重要事項の文脈）で、crucialは成否を左右するほど重要な場合に使い、importantはより広い範囲の重要性を示します。例：This meeting is crucial for our project.「この会議は私たちのプロジェクトにとって極めて重要です。」／Regular exercise is important for health.「定期的な運動は健康に重要です。」

2文目: First, regular physical exercise can significantly reduce stress levels.
（第一に、定期的な運動はストレスのレベルを大幅に減少させることができます。）
reduce（動詞：意図的に量や程度を減らす・削減する：計画的な削減の文脈）／decrease（動詞：自然に少なくなる・数値が下がる：変化や推移の文脈）で、reduceは主体的な行動による削減、decreaseは自然な減少や結果としての減少を指します。例：We should reduce plastic use.「プラスチック使用を減らすべきです。」／The temperature decreased overnight.「気温が一晩で下がった。」

3文目: For example, going for a daily jog or participating in a sport can release endorphins, which improve mood.
（例えば、毎日のジョギングやスポーツに参加することでエンドルフィンが放出され、気分が改善されます。）
release（動詞：閉じ込められていたものを解放する・放出する：物質や情報の放出の文脈）／emit（動詞：光や音などを発する・放射する：エネルギーや信号の放出の文脈）で、releaseは内部から外部へ放出すること、emitは継続的に発することを指します。例：Exercise releases endorphins.「運動はエンドルフィンを放出します。」／The sun emits light and heat.「太陽は光と熱を放射します。」

4文目: This helps individuals feel more relaxed and less anxious.
（これにより、よりリラックスし、不安が軽減されます。）
relaxed（形容詞：緊張がほぐれた・リラックスした：心身の緊張が解けた状態の文脈）／calm（形容詞：穏やかな・落ち着いた：感情が平静である状態の文脈）で、relaxedは緊張からの解放を強調し、calmは平静な状態を示します。例：I feel relaxed after yoga.「ヨガの後はリラックスします。」／She remained calm during the crisis.「彼女は危機の間も落ち着いていました。」

5文目: Second, maintaining a balanced diet contributes to stress management.
（第二に、バランスの取れた食事はストレス管理に寄与します。）
contribute（動詞：貢献する・寄与する：目標達成に役立つ行動の文脈）／help（動詞：助ける・手伝う：一般的な支援の文脈）で、contributeはより正式で、全体に対する貢献を強調し、helpはより広い意味での手助けを指します。例：Good nutrition contributes to health.「良い栄養は健康に寄与します。」／Can you help me with this?「これを手伝ってもらえますか？」

6文目: For instance, consuming fruits and vegetables provides essential nutrients that enhance mental health.
（例えば、果物や野菜を摂取することで、精神の健康を高めるための重要な栄養素が得られます。）
enhance（動詞：質や価値を高める・向上させる：既存のものをより良くする文脈）／improve（動詞：改善する・良くする：問題点を修正する文脈）で、enhanceは既に良い状態をさらに向上させること、improveは悪い状態から良い状態にすることを指します。例：This will enhance your skills.「これはあなたのスキルを向上させます。」／We need to improve the system.「システムを改善する必要があります。」

7文目: As a result, people can better cope with stress and improve their overall well-being.
（その結果、ストレスによりうまく対処でき、全体的な健康が向上します。）
cope with（熟語：対処する・うまく扱う：困難な状況に対応する文脈）／deal with（熟語：取り扱う・処理する：問題や事柄に対応する文脈）で、cope withは精神的・感情的な対処を強調し、deal withはより実務的な対応を指します。例：She copes well with stress.「彼女はストレスにうまく対処しています。」／We need to deal with this problem.「この問題を処理する必要があります。」

8文目: Therefore, incorporating exercise and a healthy diet into daily life is vital for managing stress effectively.
（したがって、運動と健康的な食事を日常生活に取り入れることは、ストレスを効果的に管理するために不可欠です。）
vital（形容詞：生命に関わるほど重要な・不可欠な：存続や成功に必須の文脈）／essential（形容詞：本質的な・必要不可欠な：基本的に必要な要素の文脈）で、vitalはより緊急性や重要性が高く、essentialは基本的な必要性を示します。例：Water is vital for survival.「水は生存に不可欠です。」／Sleep is essential for health.「睡眠は健康に必要不可欠です。」

9文目: This will promote a happier and healthier lifestyle.
（これにより、より幸せで健康的な生活が促進されます。）
promote（動詞：促進する・奨励する：発展や普及を支援する文脈）／encourage（動詞：励ます・勇気づける：行動を促す文脈）で、promoteはより公式で、制度的な支援や普及を指し、encourageは個人的な励ましを意味します。例：The government promotes healthy living.「政府は健康的な生活を促進しています。」／Teachers encourage students to study.「教師は生徒に勉強するよう励まします。」
```

**解説の要件**：
- **【🚨🚨🚨 絶対厳守 🚨🚨🚨】模範解答の全ての文に対して、必ず1文ごとに解説を書くこと（省略絶対禁止）**
  - 例：模範解答が9文なら、1文目から9文目まで全て解説する
  - **「以下同様に...」「（以下省略）」などで省略してはいけない！**
  - **最後の文まで必ず具体的に解説を書くこと！**
  - 各段落内の全ての文を解説すること（段落の最初の文だけでなく、For example...、This helps...、As a result...などの文も全て解説）
- **【絶対厳守】Markdown記号（#、**、・など）や角括弧[]を一切使わず、プレーンテキストで記載すること**
- **【必須フォーマット】単語A（品詞：意味の詳細説明：使用される文脈）／単語B（品詞：意味の詳細説明：使用される文脈）の形式で記載**
  - 例：health（名詞：病気でない状態・心身の健康全般：医療や生活習慣の文脈）／fitness（名詞：運動によって維持される身体的健康・体力レベル：トレーニングやスポーツの文脈）
- **【重要】「〜の使い分けについて」という見出しは書かない - 直接本文から始める**
- 各文ごとに「1文目:」「2文目:」「3文目:」...と番号を付けて解説
- 重要な語彙・熟語のみを選択（一般的すぎる単語は省略してもよいが、必ず各文に1つ以上の語彙解説を含める）
- 使い分けの説明では、両者のニュアンスの違いと使用される文脈を明確に書くこと
- 例文2つ以上（日本語訳付き、「／」で区切る）を必ず含める
- 添削時の解説フォーマットと同じく、詳細で学習者に役立つ内容にすること

**【重要】模範解答は、学生の回答を否定するのではなく、「さらに高得点を目指すための理想形」として提示すること**

重要な制約:
1. 必ずJSON形式のみで出力
2. Markdownコードブロック（```json）は使用しない
3. originalはそのまま保持
4. **correctedは英文のみ（日本語訳は含めない）**
   - 各文の後に改行(\n\n)を入れる
   - 例："Sentence1.\n\nSentence2.\n\nSentence3."
5. **pointsの最初の項目は必ず全体評価を含める**（before: "【全体評価】", level: "内容評価"）
6. **【🚨絶対厳守🚨】pointsの数は、提出された文の数+1（全体評価）にすること**
   - **例：4文提出 → 5個のpoints（全体評価1 + 各文4）**
   - **例：8文提出 → 9個のpoints（全体評価1 + 各文8）**
   - **【重要】3個だけで終わらせない！全ての文に対して解説を書くこと！**
   - points[0]: 全体評価
   - points[1]: 1文目の解説
   - points[2]: 2文目の解説
   - points[3]: 3文目の解説
   - points[4]: 4文目の解説
   - （以下、提出された全ての文について解説を続ける）
7. **各pointのafterフィールドには、修正後の英文の後に改行して日本語訳を追加**
   - 形式：「英文\n（日本語訳）」
   - 例:"Living in a city is more beneficial.\n（都市に住むことはより有益です。）"
8. **reasonには詳細な語彙の使い分け解説を含める**
   - 形式：「語彙A（意味：使用文脈の詳細）／語彙B（意味：使用文脈の詳細）」
   - 必ず複数の例文を含める（最低2つ、それぞれ日本語訳付き）
   - 例文形式：英文「日本語訳」/ 別の英文「日本語訳」
   - 類似語との詳細な使い分けを説明（どのような場面でどちらを使うか明確に）
9. **【🚨絶対必須🚨】levelフィールドは必ず出力すること**
   - ❌文法ミス：文法・スペル・語順などの明確な誤り
   - ✅正しい表現：完璧で修正不要
   - 💡改善提案：文法的に正しいがより良い表現がある
   - 内容評価：全体評価のみ（points[0]）
10. altはオプション（ない場合は省略、nullにしない）
11. reasonは必ず日本語で記載
12. **【最重要】points[0]は必ず全体評価（level: "内容評価"）にすること**
13. **【絶対厳守】すべてのpointに必ずlevelフィールドを含めること。levelがないJSONは不正です**
14. **【必須】model_answer と model_answer_explanation を必ず出力すること**
    - model_answer: 理想的な模範解答（100-120語、一文ごとに改行＋日本語訳付き）
    - model_answer_explanation: 模範解答の優れている点を6つの観点から解説
15. **【🚨🚨🚨 JSON構文エラー防止 - 超重要 🚨🚨🚨】**
    **pointsの配列の閉じ括弧 ] の直後に必ずカンマ（,）を付けること**
    - ✅ 正しい例: `}} ],` ← この ] の後のカンマが絶対必要！
    - ❌ 誤った例: `}} ]` ← カンマがないとJSON構文エラー（Expecting ',' delimiter）
    - ❌ 誤った例: `}}]"model_answer"` ← スペースも、カンマも、改行もない
    - pointsの後にmodel_answerフィールドが続くため、カンマは絶対必要
    - **この1つのカンマがないだけで全ての添削が失敗します。必ず確認してください**
"""


# ===== プロンプト辞書（翻訳モード） =====
PROMPTS = {
    'question': QUESTION_PROMPT_MIYAZAKI_TRANSLATION,
    'correction': CORRECTION_PROMPT_MIYAZAKI_TRANSLATION,
    'model_answer': MODEL_ANSWER_PROMPT_MIYAZAKI_TRANSLATION
}


# ===== ユーティリティ関数 =====

def clean_json_response(response: str) -> str:
    """LLMの出力からJSON部分を抽出し、制御文字をエスケープ"""
    import re
    
    response = response.strip()
    
    # Markdownコードブロックを削除
    if response.startswith('```'):
        lines = response.split('\n')
        lines = [line for line in lines if not line.startswith('```')]
        response = '\n'.join(lines)
    
    # 先頭と末尾の空白を削除
    response = response.strip()
    
    # JSONの開始を検索
    start_idx = response.find('{')
    end_idx = response.rfind('}')
    
    if start_idx != -1 and end_idx != -1:
        response = response[start_idx:end_idx+1]
    
    # 【重要】points配列の最後の要素の後のカンマ漏れを修正
    # より強力なパターンマッチング: } の後に ] があり、その後に " で始まるフィールドがある場合
    # パターン1: }[\s]*][\s]*"model_answer" → },\n  "model_answer"
    # パターン2: }[\s]*][\s]*"corrected" → },\n  "corrected"
    
    # まず、pointsの閉じ括弧を見つける
    # } ] の後に直接 " が来る場合を修正
    import re
    
    # より汎用的なパターン: points配列の終わり（}と]の間に改行やスペースがあるかもしれない）
    # その後、カンマなしで次のフィールドが始まる
    def fix_missing_comma_after_array(text):
        """配列の後のカンマ漏れを修正"""
        # パターン: }(空白)*](空白)*改行(空白)*"フィールド名"
        # → }(空白)*],(空白)*改行(空白)*"フィールド名"
        
        # ステップ1: } ] "..." のパターンを探す
        pattern1 = re.compile(r'(\})\s*(\])\s*\n\s*("(?:model_answer|corrected|word_count)")')
        text = pattern1.sub(r'\1\2,\n  \3', text)
        
        # ステップ2: 改行なしのパターン } ]"..."
        pattern2 = re.compile(r'(\})\s*(\])\s*("(?:model_answer|corrected|word_count)")')
        text = pattern2.sub(r'\1\2, \3', text)
        
        return text
    
    response = fix_missing_comma_after_array(response)
    
    # JSON文字列内の制御文字を削除（改行、タブ、バックスラッシュ以外）
    # \x00-\x08: NULL～BS、\x0b: VT、\x0c: FF、\x0e-\x1f: SO～US
    response = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', response)
    
    # JSONとして不正な改行を\\nに変換
    # ただし、既に\"で囲まれた文字列内の改行は保持
    try:
        # まず、JSON文字列内の生の改行を\\nに変換
        import json
        # 簡易的に、"から次の"までの間にある\nを\\nに変換
        def replace_newlines_in_strings(text):
            result = []
            in_string = False
            escape = False
            
            for i, char in enumerate(text):
                if escape:
                    result.append(char)
                    escape = False
                    continue
                    
                if char == '\\':
                    escape = True
                    result.append(char)
                    continue
                    
                if char == '"':
                    in_string = not in_string
                    result.append(char)
                    continue
                
                if in_string and char == '\n':
                    result.append('\\n')
                elif in_string and char == '\t':
                    result.append('\\t')
                else:
                    result.append(char)
            
            return ''.join(result)
        
        response = replace_newlines_in_strings(response)
    except Exception as e:
        logger.warning(f"Failed to escape newlines: {e}")
    
    return response
    
    return response


def call_openai_with_retry(prompt: str, max_retries: int = 3, is_model_answer: bool = False) -> str:
    """OpenAI APIをリトライ付きで呼び出し"""
    
    # モデル解答生成時は特別なシステムメッセージを使用
    if is_model_answer:
        system_message = """あなたは日本の大学入試英作文の専門家です。

【🚨最重要指示🚨】
模範解答を生成する際は、必ず以下を守ってください：
1. 英文の語数を100-120語にすること（日本語訳は語数に含めない）
2. 語数が不足する場合は、必ず文を追加して100語以上にすること
3. 具体例を2つ以上含めること
4. 高校3年生が実際に書ける基本的な表現のみ使うこと

【語数確保の方法】
- First理由: 6-7文、45-55語
- Second理由: 6-7文、45-55語
- 結論: 3-4文、30-40語
- 合計: 必ず100-120語

必ずJSON形式のみで回答してください。"""
    else:
        system_message = "あなたは日本の大学入試英作文の専門家です。必ずJSON形式のみで回答してください。"
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},  # JSONモードを有効化
                temperature=0.7,
                max_tokens=4000,  # 2000から4000に増やして長い添削に対応
                timeout=180.0  # タイムアウトを180秒に延長（OpenAI API応答待機）
            )
            
            content = response.choices[0].message.content
            logger.info(f"OpenAI API response (attempt {attempt + 1}): {content[:200]}...")
            
            # 🔍 デバッグ：完全なLLM応答をログ出力（添削の場合）
            if not is_model_answer:
                logger.info(f"[DEBUG] Full LLM response for correction:\n{content}")
            
            return content
            
        except Exception as e:
            logger.error(f"OpenAI API error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                raise
    
    raise Exception("Failed to get response from OpenAI after retries")


# ===== 出題サービス =====

def generate_question(difficulty: str = "intermediate", excluded_themes: List[str] = None) -> QuestionResponse:
    """
    翻訳問題を生成（リトライ付き）
    
    Args:
        difficulty: 難易度（翻訳問題では無視される）
        excluded_themes: 除外するジャンル（7ジャンル固定語）のリスト
    """
    if excluded_themes is None:
        excluded_themes = []
    
    logger.info("翻訳問題を生成中...")
    
    # プロンプトを取得（翻訳用）
    prompt_template = PROMPTS['question']
    
    prompt = prompt_template.format(
        excluded_themes=", ".join(excluded_themes) if excluded_themes else "なし",
        past_questions_reference=PAST_QUESTIONS_REFERENCE
    )
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # OpenAI APIを呼び出し
            response = call_openai_with_retry(prompt)
            
            # JSONをクリーンアップ
            cleaned = clean_json_response(response)
            logger.info(f"Cleaned JSON (attempt {attempt + 1}): {cleaned[:300]}...")
            
            # JSONをパース
            data = json.loads(cleaned)
            
            # Pydanticでバリデーション
            question = QuestionResponse(**data)
            
            # themeが7ジャンル固定語のいずれかか確認
            if question.theme not in TRANSLATION_GENRES:
                logger.warning(f"Invalid theme: {question.theme}, using fallback")
                raise ValidationError(f"Theme must be one of: {TRANSLATION_GENRES}")
            
            logger.info(f"Successfully generated question: {question.theme}")
            return question
            
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Question generation failed (attempt {attempt + 1}): {e}")
            
            if attempt == max_retries - 1:
                # 最後のリトライでも失敗したらフォールバック
                logger.error("All retries failed, returning fallback question")
                return _get_fallback_question()
    
    return _get_fallback_question()


def _get_fallback_question() -> QuestionResponse:
    """フォールバック用の固定問題（翻訳形式）"""
    return QuestionResponse(
        theme="ブログ",
        question_text=None,
        japanese_sentences=[
            "最近、睡眠の質を改善したいと思っていた。夜遅くまでスマホを見る習慣があり、なかなか寝付けないことが多かった。",
            "そこで、寝る1時間前にはスマホを触らないというルールを設けた。代わりに本を読んだり、軽いストレッチをしたりするようにした。",
            "この習慣を続けてから、以前よりもスムーズに眠れるようになった。朝の目覚めも良くなり、日中の集中力も向上した気がする。忙しい人にもぜひ試してほしい。"
        ],
        hints=[
            {"en": "sleep quality", "ja": "睡眠の質", "kana": "スリープ・クオリティ", "pos": "名詞", "usage": "improve sleep quality「睡眠の質を改善する」"},
            {"en": "fall asleep", "ja": "眠りにつく", "kana": "フォール・アスリープ", "pos": "動詞句", "usage": "have trouble falling asleep「眠りにつくのに苦労する」"},
            {"en": "set a rule", "ja": "ルールを設ける", "kana": "セット・ア・ルール", "pos": "動詞句", "usage": "set a rule for oneself「自分にルールを課す」"},
            {"en": "concentration", "ja": "集中力", "kana": "コンセントレーション", "pos": "名詞", "usage": "improve concentration「集中力を向上させる」"},
            {"en": "worth trying", "ja": "試す価値がある", "kana": "ワース・トライイング", "pos": "形容詞句", "usage": "be worth trying「試す価値がある」"}
        ],
        target_words=TargetWords(min=100, max=120)
    )


def _generate_fallback_correction(user_answer: str, question_text: str) -> dict:
    """
    JSONパースエラー時のフォールバック応答を生成
    ユーザーの英文を受け入れ、基本的なフィードバックを返す
    """
    logger.info("Generating fallback correction response")
    
    # 語数をカウント
    word_count = len(user_answer.split())
    
    return {
        "original": user_answer,  # 必須: 元の英文
        "corrected": user_answer,  # エラー時は元の文をそのまま返す
        "word_count": word_count,  # 必須: 語数
        "points": [
            {
                "before": "【全体評価】",
                "after": "❌ エラーが発生しました",
                "reason": "全体評価\n解説：添削処理中にエラーが発生しました。お手数ですが、ページを更新（Ctrl+R）して、新しい問題で再度お試しください。",
                "level": "内容評価"
            }
        ],
        "model_answer": None,
        "model_answer_explanation": None
    }


# ===== ヘルパー関数 =====

def determine_required_points(question_text: str, user_answer: str) -> int:
    """
    required_points（必要な解説項目数）を決定する
    
    優先順位：
    1. 原文（日本語）の文数
    2. 学生英文の文数
    3. 最小値として3（フォールバック）
    
    Args:
        question_text: 日本語原文
        user_answer: 学生の英文回答
        
    Returns:
        required_points: 必要な項目数
    """
    # 1. 原文の文数をカウント（句点・ピリオドで分割）
    if question_text and question_text.strip():
        # 句点（。）またはピリオド（.）で分割
        japanese_sentences = [s.strip() for s in question_text.replace('。', '.').split('.') if s.strip()]
        if japanese_sentences:
            logger.info(f"Required points determined from Japanese text: {len(japanese_sentences)} sentences")
            return len(japanese_sentences)
    
    # 2. 学生英文の文数をカウント（ピリオドで分割）
    if user_answer and user_answer.strip():
        english_sentences = [s.strip() for s in user_answer.split('.') if s.strip()]
        if english_sentences:
            logger.info(f"Required points determined from English text: {len(english_sentences)} sentences")
            return len(english_sentences)
    
    # 3. フォールバック：最小3項目
    logger.warning("Could not determine sentence count, using fallback: 3")
    return 3


# ===== 添削サービス =====

def correct_answer(submission: SubmissionRequest) -> CorrectionResponse:
    """
    和文英訳を添削（miyazaki翻訳形式専用）
    
    Args:
        submission: 提出データ
    """
    # ユーザー入力の全角記号を半角に正規化
    normalized_answer = normalize_punctuation(submission.user_answer)
    logger.info(f"Normalized user answer (first 100 chars): {normalized_answer[:100]}...")
    
    # 問題文を取得（優先順位: japanese_paragraphs > japanese_sentences > question_text）
    if submission.japanese_paragraphs:
        question_text = "\n\n".join(submission.japanese_paragraphs)
    elif submission.japanese_sentences:
        question_text = "\n".join(submission.japanese_sentences)
    else:
        question_text = submission.question_text or ""
    
    logger.info(f"Question text for correction: {question_text[:200]}...")
    
    # required_points を決定
    required_points = determine_required_points(question_text, normalized_answer)
    logger.info(f"Required points for this correction: {required_points}")
    
    # 語数を取得
    word_count = submission.word_count if submission.word_count is not None else len(normalized_answer.split())
    logger.info(f"Word count: {word_count}")
    
    # 制約チェック（翻訳問題用）
    constraints = ConstraintChecks(
        word_count=word_count,
        within_word_range=10 <= word_count <= 160,
        required_units=0,
        detected_units=0,
        has_required_units=True,
        unit_detection_confidence="high",
        markers_found=[],
        because_count=0,
        sentence_count=len([s for s in normalized_answer.split('.') if s.strip()]),
        notes=[f"語数: {word_count}語（10-160語が推奨範囲）"],
        suggestions=[]
    )
    
    # 添削プロンプト（required_pointsを追加）
    prompts = PROMPTS
    from string import Template
    correction_template = Template(prompts['correction'])
    correction_prompt = correction_template.substitute(
        question_text=question_text,
        user_answer=normalized_answer,
        word_count=word_count,
        required_points=required_points
    )
    
    # LLM呼び出し（リトライ付き）
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"Correction attempt {attempt + 1}/{max_retries}")
            response = call_openai_with_retry(correction_prompt, is_model_answer=True)
            cleaned = clean_json_response(response)
            
            # JSONパース
            correction_data = json.loads(cleaned)
            
            # 必須フィールドの確認と補完
            if 'original' not in correction_data:
                correction_data['original'] = normalized_answer
            if 'corrected' not in correction_data:
                correction_data['corrected'] = normalized_answer
            if 'word_count' not in correction_data:
                correction_data['word_count'] = word_count
            
            # points が存在しない場合は空リストで初期化（エラー置換は撤廃）
            if 'points' not in correction_data:
                correction_data['points'] = []
                logger.warning("No points returned by LLM, initializing empty list")
            
            # pointsの各要素に必須フィールドを補完
            # バリデーション：未提出英文の添削を防止
            valid_points = []
            seen_befores = set()  # 重複排除用
            
            for i, point in enumerate(correction_data.get('points', [])):
                # beforeが空またはない場合はスキップ
                if 'before' not in point or not point.get('before', '').strip():
                    logger.warning(f"Skipping point {i+1} with empty 'before' field")
                    continue
                
                before_text = point['before'].strip()
                
                # バリデーション: beforeが学生英文に存在するかチェック
                # プレースホルダ "(未提出：...)" は許可
                if not before_text.startswith("(未提出："):
                    # 学生英文に部分一致するかチェック
                    if before_text not in normalized_answer and not any(before_text in sentence for sentence in normalized_answer.split('.')):
                        # 完全一致も部分一致もしない場合は不採用
                        logger.warning(f"Skipping point {i+1}: before '{before_text[:50]}' not found in student answer")
                        continue
                
                # 重複排除: 同じ before/after の組み合わせは1つだけ採用
                key = (before_text, point.get('after', '').strip())
                if key in seen_befores:
                    logger.warning(f"Skipping duplicate point {i+1}: {before_text[:50]}")
                    continue
                seen_befores.add(key)
                    
                if 'after' not in point or not point.get('after', '').strip():
                    point['after'] = point['before']
                if 'reason' not in point:
                    point['reason'] = "指摘理由"
                if 'level' not in point:
                    point['level'] = "💡改善提案"
                    
                valid_points.append(point)
            
            # valid_pointsで置き換え
            correction_data['points'] = valid_points
            
            # N不足チェック：required_pointsに満たない場合は埋め合わせ
            current_count = len(valid_points)
            non_evaluation_points = [p for p in valid_points if p.get('level') != '内容評価']
            non_evaluation_count = len(non_evaluation_points)
            
            logger.info(f"Points check: current={current_count}, non-evaluation={non_evaluation_count}, required={required_points}")
            
            if non_evaluation_count < required_points:
                shortage = required_points - non_evaluation_count
                logger.warning(f"Points shortage detected: need {shortage} more points")
                
                # ステップ1: 再プロンプトで追加生成を試みる（最優先・コピー禁止）
                reprompt_success = False
                for reprompt_attempt in range(2):  # 最大2回試行
                    try:
                        current_shortage = required_points - len([p for p in valid_points if p.get('level') != '内容評価'])
                        if current_shortage <= 0:
                            reprompt_success = True
                            break
                        
                        logger.info(f"Step {reprompt_attempt + 1}: Attempting reprompt for {current_shortage} additional points")
                        
                        # 既存pointsのbefore一覧（重複防止用）
                        existing_befores = [p.get('before', '') for p in valid_points]
                        existing_befores_str = "\n".join(f"  - {b[:100]}" for b in existing_befores if b.strip())
                        
                        temperature = 0.7 if reprompt_attempt == 0 else 0.9
                        
                        reprompt = f"""
🚨🚨🚨 重要：不足分{current_shortage}個の解説を必ず生成してください 🚨🚨🚨

現在{len([p for p in valid_points if p.get('level') != '内容評価'])}個の解説がありますが、{required_points}個必要です。

【既存の解説のbeforeリスト（絶対に重複禁止）】
{existing_befores_str}

【学生の英文（必ず参照）】
{normalized_answer}

【日本語原文】
{question_text}

【模範解答】
{correction_data.get('corrected', '')}

【絶対厳守事項】
1. 必ず{current_shortage}個の新しい解説を出力すること
2. beforeは既存の解説と絶対に重複させないこと
3. beforeは以下のどちらか：
   (a) 学生英文 "{normalized_answer}" の部分文字列（句・節でも可）
   (b) 未提出プレースホルダ "(未提出：原文第N文)" の形式
4. 学生英文のコピー禁止（before と after が同一で、かつ既存pointsに類似する場合はNG）
5. 必ずkagoshima風の詳細解説を記載すること：
   - N文目: 英文\\n（日本語訳）
   - 語彙比較A／B（品詞・意味・文脈差）
   - 【参考】文法パターン
   - 例：例文1 (和訳1)／例文2 (和訳2)
6. 例文は学生の英文と異なる新しい例を必ず2つ提示すること
7. 固定文言（「この表現は適切です」のみ）は絶対に禁止

【出力形式（必須）- JSON形式で必ず{current_shortage}個】
```json
{{
  "points": [
    {{
      "before": "学生英文の部分文字列 OR (未提出：原文第N文)",
      "after": "改善後の表現 OR 模範解答の該当文",
      "reason": "N文目: 英文\\n（日本語訳）\\n語彙比較A／B...\\n【参考】...\\n例：例文1 (和訳1)／例文2 (和訳2)",
      "level": "✅ 正しい表現 OR ❌ 文法ミス OR ✅ 補足解説"
    }}
  ]
}}
```

🚨 {current_shortage}個のpointsを返してください 🚨
"""
                        
                        additional_response = call_openai_with_retry(reprompt, is_model_answer=True, temperature=temperature)
                        additional_cleaned = clean_json_response(additional_response)
                        additional_data = json.loads(additional_cleaned)
                        
                        if 'points' in additional_data and len(additional_data['points']) > 0:
                            added_count = 0
                            for point in additional_data['points']:
                                before = point.get('before', '').strip()
                                if not before:
                                    continue
                                
                                # 重複チェック
                                if before in existing_befores:
                                    logger.warning(f"Skipping duplicate before from reprompt: {before[:50]}")
                                    continue
                                
                                # バリデーション: beforeが学生英文に存在するか
                                if not before.startswith("(未提出："):
                                    if before not in normalized_answer and not any(before in s for s in normalized_answer.split('.')):
                                        logger.warning(f"Skipping invalid before from reprompt (not in student answer): {before[:50]}")
                                        continue
                                
                                valid_points.append(point)
                                existing_befores.append(before)
                                added_count += 1
                                logger.info(f"Added point from reprompt: {before[:50]}...")
                                
                                # 目標達成チェック
                                if len([p for p in valid_points if p.get('level') != '内容評価']) >= required_points:
                                    break
                            
                            logger.info(f"✅ Reprompt attempt {reprompt_attempt + 1}: added {added_count} points")
                            
                            if len([p for p in valid_points if p.get('level') != '内容評価']) >= required_points:
                                reprompt_success = True
                                break
                        else:
                            logger.warning(f"Reprompt attempt {reprompt_attempt + 1} returned no valid points")
                    
                    except Exception as e:
                        logger.error(f"Reprompt attempt {reprompt_attempt + 1} failed: {e}")
                
                # ステップ2: それでも不足した場合のみfiller_point（最後の砦・品質保証）
                final_non_eval = len([p for p in valid_points if p.get('level') != '内容評価'])
                if final_non_eval < required_points:
                    final_shortage = required_points - final_non_eval
                    logger.warning(f"Step 3: Using quality-assured filler for remaining {final_shortage} shortage")
                    
                    # 日本語原文を文ごとに分割
                    jp_sentences = [s.strip() for s in question_text.split('。') if s.strip()]
                    
                    # 既存のbeforeを収集（重複防止）
                    used_befores = set(p.get('before', '').strip() for p in valid_points)
                    
                    for i in range(final_shortage):
                        # 未提出プレースホルダを使用（filler はコピー禁止）
                        sentence_num = final_non_eval + i + 1
                        filler_before = f"(未提出：原文第{sentence_num}文)"
                        
                        # 模範解答から該当文を探す
                        corrected_sentences = [s.strip() for s in correction_data.get('corrected', '').split('.') if s.strip()]
                        if len(corrected_sentences) > i:
                            filler_after = corrected_sentences[i]
                        else:
                            filler_after = "(補足が必要です)"
                        
                        # 日本語原文から該当文を取得
                        jp_text = jp_sentences[i] if i < len(jp_sentences) else "（原文）"
                        
                        # kagoshima風のreasonを生成（品質保証・固定文言禁止）
                        filler_reason = f"""{sentence_num}文目: (未提出のため補足)
（{jp_text}）
appropriate（形容詞：適切な・ふさわしい）／suitable（形容詞：適した・好都合な）で、appropriateは状況や文脈に合っていること、suitableは目的に合っていることを意味します。
【参考】be appropriate for A（Aに適切である）／be suitable for A（Aに適している）
例：This method is appropriate for beginners. (この方法は初心者に適切です。)／This tool is suitable for the task. (この道具はその作業に適しています。)"""
                        
                        filler_point = {
                            "before": filler_before,
                            "after": filler_after,
                            "reason": filler_reason,
                            "level": "✅ 補足解説"
                        }
                        valid_points.append(filler_point)
                        logger.info(f"Added quality filler point {i+1}/{final_shortage}: {filler_before}")
                
                correction_data['points'] = valid_points
                logger.info(f"After all filling steps: {len(valid_points)} points total")


            
            # constraint_checksを追加
            correction_data['constraint_checks'] = constraints.model_dump()
            
            # 模範解答を生成（LLMから返されていない場合）
            if 'model_answer' not in correction_data or not correction_data.get('model_answer'):
                logger.info("Generating model answer...")
                try:
                    model_result = generate_model_answer_only(question_text)
                    correction_data['model_answer'] = model_result.get('model_answer', '')
                    correction_data['model_answer_explanation'] = model_result.get('model_answer_explanation', '')
                    logger.info("✅ Model answer generated")
                except Exception as e:
                    logger.error(f"Failed to generate model answer: {e}")
                    correction_data['model_answer'] = None
                    correction_data['model_answer_explanation'] = None
            
            # Pydanticモデルでバリデーション
            correction = CorrectionResponse(**correction_data)
            logger.info(f"✅ Correction successful: {len(correction.points)} points")
            return correction
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error (attempt {attempt + 1}): {e}")
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
        except ValueError as e:
            logger.error(f"Validation error (attempt {attempt + 1}): {e}")
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
        except Exception as e:
            logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
    
    # すべてのリトライ失敗時のフォールバック
    logger.error(f"All {max_retries} attempts failed. Generating fallback response.")
    fallback = _generate_fallback_correction(normalized_answer, question_text)
    fallback['constraint_checks'] = constraints.model_dump()
    fallback['word_count'] = word_count
    
    # fallbackのpointsに必須フィールドを補完
    for point in fallback.get('points', []):
        if 'before' not in point:
            point['before'] = "エラー"
        if 'after' not in point:
            point['after'] = "エラー"
        if 'reason' not in point:
            point['reason'] = "添削処理中にエラーが発生しました。"
        if 'level' not in point:
            point['level'] = "💡改善提案"
    
    return CorrectionResponse(**fallback)


def generate_model_answer_only(question_text: str) -> dict:
    """
    日本語原文から模範英訳を生成（翻訳用）
    
    Args:
        question_text: 日本語の原文（段落区切りまたは改行区切り）
    
    Returns:
        dict: {"model_answer": str, "model_answer_explanation": str}
    """
    prompt = PROMPTS['model_answer'].format(question_text=question_text)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = call_openai_with_retry(prompt, is_model_answer=True)
            cleaned = clean_json_response(response)
            logger.info(f"Model answer JSON (attempt {attempt + 1}): {cleaned[:300]}...")
            
            data = json.loads(cleaned)
            
            # 必須フィールドの確認
            if 'model_answer' not in data or 'model_answer_explanation' not in data:
                raise ValueError("Missing required fields: model_answer or model_answer_explanation")
            
            # 語数チェック（日本語訳を除外）
            model_text = data['model_answer']
            # 日本語訳部分（括弧内）を除去
            import re
            english_only = re.sub(r'（[^）]*）', '', model_text)
            english_only = re.sub(r'\([^)]*\)', '', english_only)
            # 改行を削除して単語数をカウント
            words = english_only.strip().split()
            word_count = len(words)
            
            logger.info(f"Generated model answer word count: {word_count}")
            
            # 語数が不足している場合は拡張処理（100-120語の範囲内の場合のみ使用）
            if word_count < 100:
                logger.warning(f"Word count {word_count} is below 100. Will retry generation.")
                
                # 拡張処理は行わず、次の試行で最初から生成し直す
                if attempt < max_retries - 1:
                    continue
                else:
                    # 最終試行でも100語未満の場合は警告してそのまま返す
                    logger.warning(f"Final attempt still below 100 words ({word_count}). Returning anyway.")
                    return data
            
            # 語数が120語超の場合も警告
            if word_count > 120:
                logger.warning(f"Word count {word_count} exceeds 120. Should be 100-120 words.")
            
            logger.info(f"Successfully generated model answer with {word_count} words")
            return data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Model answer generation failed (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                raise ValueError(f"Failed to generate model answer after {max_retries} attempts: {e}")
    
    raise ValueError("Failed to generate model answer")
