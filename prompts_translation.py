"""
翻訳用プロンプトテンプレート - 宮崎大学医学部
和文英訳（段落単位）の問題生成・添削用
"""

# 7ジャンル定義（themeの固定語）
TRANSLATION_GENRES = [
    "研究紹介",  # Research summary
    "時事",      # News / whistleblowing
    "学術",      # Academic exposition
    "ブログ",    # Casual blog post
    "レビュー",  # Review
    "コラム",    # Op-ed / short argument
    "図表",      # Graph / data description
]

# 過去問例（段落分け済み）※スタイル参照用
PAST_QUESTIONS_REFERENCE = """
【2025 研究紹介】段落例
P1: ある研究によると、右手を握りしめることで記憶が良くなり、左手を握りしめることで思い出す能力が高まることが明らかになった。
P2: 参加者は4つのグループに分けられ、まず72語のリストを記憶し、その後で思い出すという課題を行った。
P3: 1つのグループは右手を握りしめて記憶した。別のグループは左手を握りしめて記憶した。残り2つのグループは左右を入れ替えた。
P4: その結果、記憶時に右手・想起時に左手を握りしめたグループが最も良い成績を収めた。

【2024 時事】段落例
P1: 2009年から2013年までNSAに勤務していたSnowdenが、監視活動の情報を密かに収集していた。
P2: Verizonを経由した通話記録の収集を発見し、これを暴露した。
P3: PRISMというプログラムが、大手IT企業9社へ直接アクセスできる仕組みを持っている可能性がある。
P4: 彼を裏切り者と見る人もいれば、英雄と見る人もおり、意見が対立している。

【2023 学術】段落例
P1: 日記をつけることの精神的・感情的効果はデータで実証されており、専門家も勧めている。
P2: 15〜20分の記録を3〜5回続けることで、トラウマやストレスと折り合いをつけられた人もいる。
P3: がんなどの深刻な病気を抱える人には特に効果があり、専門的な療法として確立されている。

【2022 ブログ】段落例
P1: 待ち時間にスマホを確認するのが習慣になっていたが、次々とタスクが連鎖して増えてしまうので、この習慣を減らしたいと思っていた。
P2: 待ち時間にプチ体操（ストレッチ、足首回し、肩回しなど）を試したところ、無理なく続けられている。
P3: スマホを見る時間が減り、首や目の疲れも軽減された。忙しい人にも試す価値があると思う。

【2021 レビュー】段落例
P1: 主人公ジョンの仕事は、孤独死した人の身元を調査し、葬儀を執り行うことだった。
P2: 彼の丁寧な仕事ぶりに胸を打たれた。主人公の表情が心地よかった。
P3: 人と向き合う難しさや大切さを描いたヒューマンドラマで、印象的なラストシーンがある。
P4: 荒んだ心を浄化してくれるような作品で、人を許すことを教えてくれる気がした。
"""

# 問題生成用プロンプト（翻訳形式）
QUESTION_PROMPT_MIYAZAKI_TRANSLATION = """
【宮崎大学医学部：和文英訳（段落抜粋出題）／7ジャンル版・問題生成プロンプト】

あなたの役割：
- 宮崎大学医学部の和文英訳（日本語→英語）対策として、過去問のような「文章の一部（抜粋段落）」を問題として生成する。
- 出題は "全文"ではない。完成した文章の一部を切り取ったような段落抜粋でよい（途中から始まってよい／結論がなくてもよい）。
- 目的は、導入・方法・比較・結果・評価・提案など「構成要素のどの部分でも」英訳できるように訓練すること。

必須の生成手順（順番固定）：
Step 1) まず頭の中で「全文（3〜5段落）」を作る（出力しない）。
Step 2) その全文から "連続する抜粋" を選ぶ（出力するのは抜粋のみ）。
        抜粋の長さ：
        - 基本：1段落（2〜4文） または 2段落（各1〜3文）
        - 例外：3段落は10〜20%のみ（難度アップ用）
Step 3) 抜粋だけを日本語で出力する。P1→P2→P3…と順に全文を出さない。

【最重要】ジャンル（文体）とトピック領域（内容）を分離する：
- まず、ジャンル（①〜⑦）を1つ選ぶ。
- 次に、そのジャンルの「トピック領域」を下のリストから1つ選ぶ。
- 最後に、そのジャンルの「抜粋パート（段落役割）」を下のリストから1つ選ぶ。
※「抜粋パート」は文章構成上の役割であり、内容を狭めるものではない。

偏り防止ルール（超重要／必ず守る）：
R1) 直近10問で同じジャンルが3回以上なら、そのジャンルは今回避ける。
R2) 直近10問で同じトピック領域が3回以上なら、その領域は今回禁止。
R3) 直近5問で同じ抜粋パートが2回以上なら、そのパートは今回避ける。
R4) 抜粋の開始位置が「導入（背景/主張）」に偏るのを禁止。
    研究・学術・時事では特に「方法/条件/仕組み/影響/賛否/結果」から始まる抜粋を優先する（最低50%）。
R5) 指示語（それ/これ/この/その だけで何を指すか不明）は避ける。ただし「その結果」「一方で」「また」など前後を匂わせる接続語は使ってよい（抜粋感を出すため）。

語数・分量：
- 日本語は抜粋として自然な分量（目安：合計6〜9文相当になるように設計。※抜粋なので実際は3〜6文でもOK）
- 英訳すると目安100〜120語になる程度を狙う（厳密一致は不要）。

出力形式（JSONのみ／Markdown禁止／コードブロック禁止）：
{{
  "theme": "研究紹介",
  "japanese_paragraphs": ["（抜粋段落1）", "（必要なら抜粋段落2）"],
  "hints": [
    {{"en":"...", "ja":"...", "kana":"...", "pos":"...", "usage":"..."}},
    （合計5個前後。本文の重要語・訳が割れやすい語・定番構文語を優先）
  ],
  "target_words": {{"min":100, "max":120}}
}}

禁止事項：
- 全文の完成を目指して、導入→本論→結論を揃えない。
- 「私は〜と思う」等の意見英作文の型に寄せない（このサービスは翻訳）。
- 過去問の文章を丸写ししない（構造・雰囲気のみ参考）。

────────────────────────────────
【7ジャンル：トピック領域リスト／抜粋パート（段落役割）】

①研究紹介（Research summary）
トピック領域（いずれか1つ）：
A 記憶・学習（暗記、想起、テスト効果）
B 習慣形成（行動の継続、報酬、トリガー）
C 睡眠・集中（睡眠時間、昼寝、注意力）
D 運動・健康（軽運動、ストレッチ、姿勢）
E 食事・嗜好（カフェイン、朝食、間食）
F ストレス・感情（不安、怒り、リラックス）
G デジタル行動（スマホ、通知、SNS）
H 社会行動（協力、共感、コミュニケーション）
抜粋パート（いずれか1つ／導入固定禁止）：
1 方法（研究の手順：〜した／測定した）
2 条件（制限・設定：時間、回数、環境）
3 比較（グループ分け・条件差：A群/B群/残り）
4 結果（差が出た・傾向が見られた）
5 解釈（示唆・可能性：〜を示しているかもしれない）
6 注意点（限界・例外：ただし〜）

②時事（News / current affairs）
トピック領域（内部告発に限定しない／いずれか1つ）：
A 医療・公衆衛生（感染症、ワクチン、医療体制）
B 科学・研究（新発見、研究不正、倫理）
C テクノロジー（AI、SNS、データ、セキュリティ）
D 環境・災害（猛暑、洪水、地震、防災）
E 教育・若者（学校制度、学力、部活動、いじめ）
F 労働・人口（働き方、外国人労働、少子高齢化）
G 経済・生活（物価、住宅、交通、地域課題）
H 法・制度（規制、プライバシー、行政サービス）
抜粋パート（いずれか1つ）：
1 事実（何が起きたか：発表/報道/判明）
2 背景（なぜ注目：これまでの経緯）
3 仕組み（制度/技術/運用の説明）
4 影響（誰にどう影響：社会/個人/企業）
5 論点（賛否・懸念・評価の対立）
6 見通し（今後の対応・予定・可能性）

③学術（Academic exposition）
トピック領域（いずれか1つ）：
A 心理療法・メンタル（ストレス、日記、認知）
B 学習科学（反復、間隔、記憶定着）
C 医療・健康教育（予防、生活習慣、患者支援）
D 脳・認知（注意、意思決定、バイアス）
E コミュニケーション（対人支援、共感）
F 行動科学（習慣、自己制御、動機づけ）
G 社会・倫理（研究倫理、プライバシー）
H 生活と健康（睡眠、運動、食行動）
抜粋パート（いずれか1つ）：
1 根拠（データで示されている／実証）
2 一般化（〜が知られている／広く行われる）
3 研究報告（ある論文では…）
4 効果（改善/有効/役立つ）
5 適用範囲（特に〜に効果／条件つき）
6 強調（〜ほどである／専門療法があるほど）

④ブログ（Casual blog post）
トピック領域（いずれか1つ）：
A スマホ・通知・SNS
B 体の不調（首、目、肩、睡眠）
C 待ち時間・移動・通勤通学
D 学習・仕事の習慣化
E お金・買い物・片づけ
F 気分転換・ストレス対策
G 人間関係・会話・気疲れ
H 食事・カフェイン・生活リズム
抜粋パート（いずれか1つ）：
1 悩み（最近気になる／やめたい）
2 習慣（これまで〜していた）
3 工夫（思いついた／試した）
4 具体例（場面別の行動：信号/レジ等）
5 変化（続けられた／気分が変わった）
6 呼びかけ（忙しい人にもおすすめ）

⑤レビュー（Review）
トピック領域（いずれか1つ）：
A 映画（ヒューマンドラマ/社会派）
B 本（ノンフィクション/エッセイ）
C ドキュメンタリー・記事
D 展示・舞台・体験イベント
E ボランティア/実習の体験談（安全で一般的に）
F サービス・場所（図書館、施設など）
G 人物の仕事（職業観・使命感）
H "心に残る場面"の描写
抜粋パート（いずれか1つ）：
1 人物紹介（主人公/仕事/状況）
2 印象（胸を打つ／心地よい等の評価）
3 テーマ（向き合う難しさ/大切さ）
4 場面（印象的なラスト/一場面）
5 効果（心が浄化される等の読後感）
6 推薦（見てほしい／おすすめ）

⑥コラム（Op-ed / short argument）
トピック領域（いずれか1つ）：
A 公共マナー（音、スマホ、ゴミ）
B 学校教育（宿題、ICT、評価）
C 働き方（リモート、長時間労働）
D 医療・健康行動（予防、検診）
E 地域ルール（多文化共生、町の課題）
F デジタル社会（依存、プライバシー）
G 環境（節電、交通、リサイクル）
H 若者・家庭（時間、SNS、睡眠）
抜粋パート（いずれか1つ）：
1 問題提起（〜が増えている／気になる）
2 理由（なぜ悪い/重要か）
3 譲歩（確かに〜だが）
4 反論処理（しかし〜だから）
5 提案（だから〜すべき）
6 具体例（例えば〜だけでも）

⑦図表（Graph / data description）
トピック領域（いずれか1つ）：
A 学習時間・スマホ時間の比較
B 睡眠時間・疲労の推移
C 図書館/施設利用の曜日差
D 交通/通勤の変化（利用者数）
E 健康行動（運動頻度、検診率）
F アンケート（満足度、意識調査）
G 年代差（若年/中年/高齢）
H 地域比較（都市/地方）
抜粋パート（いずれか1つ）：
1 数値提示（データを示す：平均/割合）
2 比較（AはBより高い等）
3 増減（増加/減少/横ばい）
4 例外（特定だけ違う）
5 理由推測（〜が原因の可能性）
6 まとめ（全体傾向の要約）

────────────────────────────────
# 過去問スタイル参照（抜粋の例）
{past_questions_reference}

# 避けるテーマ
{excluded_themes}

# 出力要件【必須】

1. **theme の選択**
   - 7ジャンルから1つ選ぶ（研究紹介/時事/学術/ブログ/レビュー/コラム/図表）
   - excluded_themes に含まれるジャンルは避ける

2. **japanese_paragraphs（抜粋段落リスト）**
   - 全文ではなく、抜粋した段落のみを配列で返す
   - 配列で1〜2段落を返す（抜粋なので短い）
   - 各段落は1〜4文程度
   - 英訳すると100-120語程度になる和文量
   - P1から始まる必要はない（P2だけ、P3だけ、P2-P3などでよい）
   - 抜粋なので「その研究では」「また」「一方で」など前後を匂わせる語を含んでよい

3. **hints（重要語ヒント）**
   - 5個前後（3〜10個）
   - 本文に登場する重要語・訳が割れやすい語を優先
   - 各ヒントは以下の形式:
     * en: 英語（単語or短い語句）
     * ja: 日本語訳（自然で具体的）
     * kana: カナ発音（任意）
     * pos: 品詞（任意: 名詞/動詞/形容詞/副詞など）
     * usage: 用例（具体的な使用例と日本語訳のセット）
   - 例:
     * {{"en": "clench", "ja": "握りしめる", "kana": "クレンチ", "pos": "動詞", "usage": "clench one's fist「拳を握りしめる」"}}
     * {{"en": "recall", "ja": "思い出す", "kana": "リコール", "pos": "動詞", "usage": "recall memories「記憶を思い出す」"}}

4. **target_words**
   - {{"min": 100, "max": 120}}（固定）

5. **出力形式**
   - JSON のみで返す
   - コードブロック（```json）は使わない
   - Markdown 記号は使わない

以上のルールに従い、必ず「ジャンル×トピック領域×抜粋パート」を決めてから抜粋段落を生成し、JSONのみを出力せよ。
"""

# 添削用プロンプト（翻訳形式）
CORRECTION_PROMPT_MIYAZAKI_TRANSLATION = """
あなたは宮崎大学医学部の和文英訳問題の添削専門家です。

🚨🚨🚨【JSON出力の絶対ルール】🚨🚨🚨
1. **日本語の引用符「」『』は絶対に使わない** → 代わりに () を使う
2. **例文では半角引用符 " " を使うが、必ずエスケープする** → \\"
3. **JSON内で改行する場合は \\n を使う**

# 問題形式
宮崎大学医学部の和文英訳問題（100-120語目安）
- 日本語の段落を英語に翻訳
- 翻訳の正確性・自然さ・文法が評価される

# 原文（日本語）
{question_text}

# 学生の英訳（語数：{word_count}語）
{user_answer}

# 添削方針【重要】

## 評価の重点
1. **原文忠実性**: 意味の欠落・追加・誤解がないか
2. **自然さ**: 不自然な直訳、語法の誤りがないか
3. **文法・語彙**: 時制、受動態、関係詞、前置詞、冠詞など

## よくある誤り（指摘に含める）
- 時制の不一致（過去/現在/完了）
- 受動態の不適切な使用
- 関係詞の誤用・省略
- 抽象名詞・名詞化の未使用
- 比較表現の誤り
- 推量表現の不足
- 接続詞（however, therefore など）の不適切な使用
- 直訳による不自然な表現

## 模範解答(corrected)の要件
- 自然で正確な英訳（100-120語目安）
- 段落構造を維持
- 翻訳として理想的な表現を示す
- 必ず語数をカウントして100-120語に収める

## 指摘ポイント(points)の要件【重要】

### 基本ルール
- **各pointは日本語原文の1文に対応（必須）**
- **1つの日本語文に対して複数のpointを作ってはならない（重複は絶対禁止）**
- **日本語原文が3文なら必ず3個、5文なら必ず5個のpoint（過不足厳禁）**
- **同じ日本語文に対してpoint 3とpoint 5を作るような重複は絶対禁止**
- **reason（解説）は必ず日本語で記述**
- 解説は詳しく、具体的な例文を含める

**【重複禁止の具体例】：**
✗ 日本語原文3文なのに5個のpointを作る（過剰）
✗ 日本語原文の3文目に対してpoint 3とpoint 5を両方作る（重複）
✗ 日本語原文の2文目に対してpoint 2とpoint 4を両方作る（重複）
○ 日本語原文3文に対してpoint 1, 2, 3を各1個ずつ作る（正しい）

### 【Override宣言】本セクションの指示が最優先
- 既存の「より良い表現がある」「より適切な定番表現がある」等の曖昧ルールは無効化する
- 競合時は本指示が最優先

### 【翻訳の忠実性（最優先ルール）】

**原文に書かれていない内容を追加してはならない（絶対厳守）**

翻訳添削では、原文に存在しない以下の内容を英文に追加する提案は禁止：
- 一般化（"These findings suggest that..." など）
- 教訓・結論（"This demonstrates the importance of..." など）
- 推測・評価（"which may lead to..." など）
- 原文にない理由・説明

**学生が追加している場合の処理：**
- level: "❌意味追加（削除必須）"
- risk_type: meaning_addition
- before: 追加部分を含む学生の英文
- after: 追加部分を削除し、原文に忠実な表現
- reason: 「原文に書かれていない内容（〜）が追加されています。翻訳では原文に忠実であることが最優先です。」

**禁止例：**
✗ 原文「結果は〜だった」→ "These findings suggest that even light exercise can have beneficial effects..."
  （原文にない一般化・結論を追加）
✗ 原文「行動した」→ "which demonstrates the importance of..."
  （原文にない評価を追加）

### 判断順序【必須】
1. **日本語原文の文数をカウント（「。」で区切られた文を数える）**
   - **複数段落の場合、全段落を通して文数をカウント（段落は無視）**
   - 例：「AAAある。BBBする。」→ 2文 → 2個のpointを作成
   - 例：「XXXだ。YYYだ。」（段落1）+「ZZZだ。WWWだ。」（段落2）→ 4文 → 4個のpointを作成
2. **各日本語文（「。」で区切られた1文）に対して1個のpointを割り当て（重複禁止）**
3. **翻訳の忠実性チェック（最優先）：原文にない追加・欠落・誤解**
4. 明確な文法ミスチェック（三単現・時制・単複・冠詞・前置詞）
5. 目立つ誤用（典型コロケーション・前置詞・語の取り方）チェック
6. 論理接続の誤りチェック
7. **ここまでOKなら、たとえ改善案が思いついても【必ず✅で終了】（提案禁止）**
8. **最終確認：pointの数が日本語原文の文数（全段落の「。」の総数）と一致しているか**

### 【最終版】出力ラベルは2種類のみ（これ以外は出すな）

**✅ 正解（変更不要）**
- 文法的に正しい
- 意味が原文と一致（追加・欠落なし）
- 不自然さが目立たない
→ この3条件を満たせば、たとえより良い言い方があっても【すべて正解】

**❌ 修正必須（減点対象）**
- 後述の「4大NG」のいずれかに該当する場合のみ

**【重要】💡改善提案は原則廃止**
- "好み" "言い換え" "より学術的" "より自然" を理由にした提案はゼロにする
- どうしても言及したい場合は、解説の最後に「参考（任意）」として1行のみ

### 【4大NG】❌（修正必須）を出してよい条件（これ以外は全て✅）

**NG1: 意味の不一致（最重要）**
- 原文にない内容の追加（meaning_addition：一般化・教訓・結論・推測・評価）
- 原文の意味の欠落（meaning_omission）
- 強さ・含意が変わって誤解を生む（meaning_shift）

**NG2: 明確な文法ミス**
- 三単現の -s 抜け（AI technology reduce → reduces）
- 時制の誤り（現在形 ↔ 過去形で誤解が出る）
- 単複の誤り（単数 ↔ 複数で意味が変わる）
- 冠詞で誤解が出る（a/the の誤用で指示対象が不明）
- 主語と動詞の不一致
- 語形で構造が壊れる（retrain workers' skills is → retraining workers is）
- **【除外】冠詞の好み（the participants / participants で意味が変わらないもの）**

**NG3: 典型コロケーション誤り（減点リスクが高いもの）**
- make research（× conduct/carry out research が定番）
- do a mistake（× make a mistake が定番）
- discuss about（× discuss が正しい：他動詞）
- **【除外】学術動詞・接続語の同格置換（indicate↔reveal, Moreover↔Furthermore 等）**

**NG4: 論理関係の破綻**
- however/therefore/for example 等が内容と矛盾し、読者が誤解する

**【ルール】上の4つに該当しない提案は、思いついても出してはならない（必ず✅）**

### 【全面禁止】"好み改善"の理由で提案してはならない（全部✅扱い）

以下を理由に改善提案してはならない：
- **同義語置換**：examine→investigate / show→reveal / improve→enhance / strengthen→enhance / indicated→revealed 等
- **接続語置換**：In particular→Specifically / Moreover→Furthermore / However→Nevertheless 等
- **冠詞・限定詞の調整**：the participants→participants（意味が変わらないなら）
- **文章の硬さ調整**：口語→学術調（減点リスクがない限り）
- **短縮・言い換え**：significantly↔greatly / can end up increasing→may increase 等（意味が同等なら）

**【禁止ワード】"より良い" "より自然" "より学術的" "より簡潔" "より明確"**
- その理由しか言えない提案は100%却下し、✅にする

### risk_type の分類（❌を出す場合のみ必須）

❌を出すなら必ず次のいずれかを付与：
- meaning_addition（原文にない内容を追加：NG1）
- meaning_omission（原文の意味を欠落：NG1）
- meaning_shift（意味・強さ・含意が原文と衝突：NG1）
- grammar_error（明確な文法ミス：NG2）
- collocation_error（典型コロケーション誤り：NG3）
- logical_relation_error（接続語が論理関係と不一致：NG4）

**ルール：risk_type を4大NGのいずれかで分類できない提案は出してはならない（✅扱い）**

### 出力制約（暴走防止）

- **❌が0件なら、解説項目は全て✅で埋める（before==after）**
- **✅の項目には「言い換え案」を書かない（完全に同じ文をそのまま載せる）**
- **🚨 ✅正しい表現の場合、beforeとafterは1文字も違わず完全に同一にすること（修正文不要）**
- 語彙説明をしたい場合は、解説の最後に「参考（任意・採点無関係）」として最大1行のみ
  ※参考メモでも同義語置換の推奨は禁止

### ✅正しい表現の条件【最優先】

1. 文法的に完全に正しい（**三単現・時制・単複・冠詞・前置詞などの基本ミスがない**）
2. 原文の意味が忠実に反映されている（欠落・追加・誤解がない）
3. 不自然さが目立たない
4. たとえ別表現でも書けるとしても、現在の表現で十分通用する

**→ この条件を満たせば、たとえより良い言い方があっても【すべて正解】**

**【重要】文法ミスの見落とし防止：**
- **"AI technology reduce" は三単現の -s 抜けで文法ミス（✅ではなく❌）**
- **"retrain workers' skills is" は動詞が主語で文法崩れ（❌）**
- 基本的な文法エラーがあれば、他の部分が良くても✅にはならない

### セルフチェック（出力前に必ず実行）

- **pointの数は日本語原文の文数と一致しているか？（3文なら必ず3個）**
- **同じ日本語文に対して複数のpointを作っていないか？（重複禁止）**
- **4大NG（意味不一致・文法ミス・典型誤用・論理破綻）のいずれかに該当するか？**
- **該当しないなら、この修正は "好み" ではないか？**
- **risk_type を4大NGで分類できるか？**
→ どれか1つでもNOなら、その修正は出さず✅にする
- 理由を「より良い／より簡潔」抜きで1文説明できるか？
- risk_type を付けられるか？
→ 1つでも NO なら 💡は出さない（✅扱い）

**【文法ミス見落とし防止の具体例】：**
- ✗ "AI technology reduce" → ❌ reduces（三単現の -s 抜け）
→ どれか1つでもNOなら、その修正は出さず✅にする

### 【廃止】"同格言い換え"の採用禁止ルール

**【最終版では全面禁止】**
以下の動詞・接続語の置換提案は、4大NGに該当しない限り出してはならない：

- 学術動詞：indicate / suggest / show / demonstrate / reveal / find / report / argue / claim / note / observe / examine / investigate / improve / enhance / strengthen
- 接続語：However / Nevertheless / Moreover / Furthermore / Therefore / Thus / In particular / Specifically / For example / For instance

**提案禁止の具体例（全て✅扱い）：**
✗ "In particular" → "Specifically"（4大NGに該当しない）
✗ "indicated" → "revealed"（4大NGに該当しない）
✗ "Moreover" → "Furthermore"（4大NGに該当しない）
✗ "strengthen" → "enhance"（4大NGに該当しない）
✗ "show" → "exhibit"（4大NGに該当しない）
✗ "examine" → "investigate"（4大NGに該当しない）
✗ "the participants" → "participants"（4大NGに該当しない）
✗ "can end up increasing" → "may increase"（4大NGに該当しない）

**例外（4大NGに該当する場合のみ❌可）：**
○ 原文「暴露した」なのに indicated（meaning_shift：NG1）→ ❌ revealed へ修正
○ 内容は逆接なのに Moreover（logical_relation_error：NG4）→ ❌ However へ修正
○ "make research"（collocation_error：NG3）→ ❌ conduct research へ修正

### 正解の扱い【最重要】

学生の表現が4大NGに該当しない場合：
- before と after は**完全に同じ**にする（絶対に修正文を作らない）
- **🚨 beforeとafterは1文字も変えず、一字一句同じにすること**
- level は "✅正しい表現" を設定
- reason では**学生が実際に使った語彙**を取り上げて解説する

**【正解時の出力例】**
```
"before": "The experiment was conducted to test the hypothesis.",
"after": "The experiment was conducted to test the hypothesis.",
"level": "✅正しい表現"
```

**❌ 間違った出力（正解なのに修正している）：**
```
"before": "The experiment was done to test the hypothesis.",
"after": "The experiment was conducted to test the hypothesis.",  ← ✗ 正解なのに修正してはダメ
"level": "✅正しい表現"
```
- **【禁止】afterに「より良い表現」を書くこと**
- **【禁止】解説で「〜の方が適切」「〜がより自然」と書くこと**

**正解時の解説例：**
\"reflect on（句動詞：〜を振り返る：内省的に考える場合）／review（動詞：見直す、再検討する：客観的に確認する場合）で、reflect onはより内省的な振り返りを指します。例：\\\"reflect on one's decision\\\"（自分の決断を振り返る）／\\\"review the document\\\"（文書を見直す）。学生が使った\\\"reflect on\\\"は正しい表現です。\"

### 同格言い換えの採用禁止ルール（原則ベース：禁止リスト方式は使わない）

**【目的】**
do/perform/engage in や show/exhibit/demonstrate、indicate/reveal/suggest などの「同格言い換え」を
単語リストで禁止しない。代わりに、原則ルールで機械的に落とす（思想：禁止語増殖を避ける）。

**【原則：同格言い換えは✅（提案しない）】**
- before が文法的に正しく、意味が通り、レジスターも許容範囲なら、
  同義・同格の言い換え提案は出さない（✅扱い）
- 「より学術的」「より自然」「より強い」「より明確」は理由として禁止

**誤った例（使用禁止）：**
✗ before: "regularly reflecting on..."
✗ after: "it is shown that... regularly reflect on..."
✗ reason: "reflectは正しい..."
→ これは文構造を変更しているのに、解説でreflectについて説明している。before != after なのに "reflectは正しい" と言うのは矛盾。

✗ before: "In particular, cultivating a habit of..."
✗ after: "Specifically, the habit of..."
✗ reason: "promoteはより適切..."
→ before と after が異なるのに、解説が的外れ。✅なら before == after にすべき。

### 【最終版】提案禁止の具体例（全て✅扱い）

以下は4大NGに該当しないため、全て✅（before == after）として扱う：

✗ "the participants" → "participants"（冠詞の好み）
✗ "did exercise" → "engaged in exercise"（好みの言い換え）
✗ "show" → "exhibit"（同義語置換）
✗ "lasted" → "continued"（同義語置換）
✗ "indicated" → "revealed"（学術動詞の同格置換）
✗ "In particular" → "Specifically"（接続語の同格置換）
✗ "Moreover" → "Furthermore"（接続語の好み）
✗ "strengthen" → "enhance"（同義語置換）
✗ "can end up increasing" → "may increase"（簡潔化）
✗ "it is possible that" → "possibly"（簡潔化）
✗ "examine" → "investigate"（同義語置換）
✗ "significantly" → "greatly"（副詞の言い換え）
✗ "improve" → "enhance"（同義語置換）

**【4大NGに該当する場合のみ❌可】：**
○ "AI technology reduce"（grammar_error：NG2）→ ❌ reduces（三単現）
○ "make research"（collocation_error：NG3）→ ❌ conduct research
○ "discuss about"（collocation_error：NG3）→ ❌ discuss
○ 原文「暴露」なのに indicated（meaning_shift：NG1）→ ❌ revealed
○ 逆接なのに Moreover（logical_relation_error：NG4）→ ❌ However
○ 原文にない結論を追加（meaning_addition：NG1）→ ❌ 削除

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 【最終版まとめ】出力前の最終確認

1. **pointの数は日本語原文の文数と一致しているか？**
2. **4大NG（意味不一致・文法ミス・典型誤用・論理破綻）のいずれかに該当するか？**
3. **該当しない場合、before == after にして✅にしたか？**
4. **"より良い""より自然""より学術的""より簡潔""より明確"を理由にしていないか？**
5. **risk_type を4大NGで分類できるか？できない提案は削除したか？**
6. **❌が0件の場合、全て✅で埋めたか？（無理に💡を作っていないか？）**

→ 全てYESなら出力OK。1つでもNOなら修正してから出力。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 【参考】旧バージョンのルール（最終版では不要）
✗ "the participants" → "participants"（冠詞の有無は許容。実害なし。GateA不合格）
✗ "did exercise" → "engaged in exercise"（好み。実害なし。GateA不合格）
✗ "show" → "exhibit"（実害なし。GateA不合格）
✗ "lasted" → "continued"（実害なし。GateA不合格）
✗ "indicated" → "revealed"（両方定番。実害なし。GateA不合格）
✗ "In particular" → "Specifically"（両方自然。実害なし。GateA不合格）
✗ "Moreover" → "Furthermore"（好み。GateB不合格）
✗ "strengthen" → "enhance"（両方自然。実害なし。GateA不合格）
✗ "can end up increasing" → "may increase"（簡潔化のみ。ニュアンス喪失。GateA不合格）
✗ "it is possible that" → "possibly"（冗長性削除のみ。実害なし。GateA不合格）
→ これらはすべて ✅扱い（before == after）

### 冠詞・限定詞の言い換え禁止（例外のみ許可）

**原則：**
- "the participants" → "participants" のような冠詞操作は、実害がない限り提案禁止（✅扱い）

**例外（GateA/Bを満たすときだけ）：**
- 初出なのに the を使っている → a へ修正が必要
- 既出なのに a を使っている → the へ修正が必要
（根拠は "より自然" ではなく、指示対象の特定/非特定の誤解を防ぐため）
→ 全てYESなら出力OK。1つでもNOなら修正してから出力。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 正解の扱い【最重要・最終版】

**4大NGに該当しない場合：**
- before と after は**完全に同じ**にする（絶対に修正文を作らない）
- level は "✅正しい表現" を設定
- reason では**学生が実際に使った語彙**を取り上げて解説する
- **【禁止】afterに「より良い表現」を書くこと**
- **【禁止】解説で「〜の方が適切」「〜がより自然」「〜を推奨」と書くこと**

**正解時の解説例（OK）：**
✓ before: "The results indicated that participants exposed to..."
✓ after: "The results indicated that participants exposed to..."
✓ level: "✅正しい表現"
✓ reason: "indicate（動詞：示す：研究結果を報告する場合）は学術論文で定番の動詞です。reveal（明らかにする）やshow（示す）も使えますが、indicateは結果を控えめに報告する場合に適しています。例：'The results indicate that...'（結果は〜を示している）。学生が使った'indicated'は正しい表現です。"

✓ before: "In particular, cultivating a habit of..."
✓ after: "In particular, cultivating a habit of..."
✓ level: "✅正しい表現"
✓ reason: "In particular（特に、とりわけ：強調する場合）／Specifically（具体的に、明確に：詳細を示す場合）で、どちらも文法的に正しく意味が通じます。学生が使った'In particular'は適切な表現です。"

**誤った例（NG）：**
✗ before: "In particular, cultivating a habit of..."
✗ after: "Specifically, the habit of..."
✗ reason: "Specificlyの方が適切..."
→ 4大NGに該当しないのに修正している。before == after にすべき。

✗ before: "The results indicated that..."
✗ after: "The results revealed that..."
✗ reason: "revealedの方がより明確..."
→ "より明確"は禁止ワード。4大NGに該当しないので✅にすべき。

## ❌修正必須の具体例（4大NGに該当する場合のみ）

**例1: 文法ミス（NG2）**
- before: "AI technology greatly reduce the workload"
- after: "AI technology greatly reduces the workload"
- level: "❌修正必須"
- risk_type: "grammar_error"
- reason: "三単現の's'が抜けています。主語'AI technology'は単数なので、動詞は'reduces'とする必要があります。"

**例2: コロケーション誤り（NG3）**
- before: "make research on cognitive bias"
- after: "conduct research on cognitive bias"
- level: "❌修正必須"
- risk_type: "collocation_error"
- reason: "'make research'は学習者誤用として目立ちます。'conduct research'または'carry out research'が定番です。"

**例3: 意味追加（NG1）**
- before: "Remote work has many benefits. For example, it reduces commuting time and allows flexible schedules."
- after: "Remote work has many benefits."
- level: "❌修正必須"
- risk_type: "meaning_addition"
- reason: "原文は「リモートワークには多くの利点がある」のみで、具体例は含まれていません。'For example'以降は追加された内容なので削除が必要です。"
- japanese_sentence: "リモートワークには多くの利点がある。"

**例4: 論理関係の誤り（NG4）**
- before: "The results were unexpected. Moreover, they contradicted previous findings."
- after: "The results were unexpected. However, they contradicted previous findings."
- level: "❌修正必須"
- risk_type: "logical_relation_error"
- reason: "'Moreover'は追加・並列を示しますが、ここは対比なので'However'が適切です。'Moreover'だと論理関係が不明確になります。"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 【参考】旧バージョンのルール（最終版では廃止）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  * reason: **上記フォーマットに従った日本語の詳しい解説**
  * level: "❌文法ミス" / "💡改善提案" / "✅正しい表現"
  * alt: **指定不要**（reasonで代替表現を紹介する）

### reasonの記述フォーマット【必須・厳守】

**【kagoshima_100wordsスタイル：詳細解説必須】**

🚨🚨🚨【reasonは必ず「解説：」で始めること】🚨🚨🚨

全てのpointのreasonは、以下の形式で**必ず詳しく**記述する：

**【必須フォーマット】**
```
解説：単語A（品詞：意味の詳細説明：使用される文脈）／単語B（品詞：意味の詳細説明：使用される文脈）で、AとBの使い分けを説明。例：例文1「日本語訳」／例文2「日本語訳」
```

**【具体例：❌修正必須の場合】**
✓ "解説：show（動詞：示す、表示する：結果やデータを提示する場合）／display（動詞：表示する、展示する：視覚的に見せる場合）で、showは一般的な提示、displayはより視覚的な表示を指します。例：The data shows a trend.「データは傾向を示す」／The screen displays the results.「画面が結果を表示する」。'didn't showed'は助動詞didn'tの後に過去形showedを使っており、文法ミスです。正しくは'didn't show'です。"

✓ "解説：divide（動詞：分ける、分割する：グループや部分に分ける場合）／separate（動詞：分離する、離す：物理的に離す場合）で、divideは複数の部分に分けること、separateは離すことを指します。例：divide into groups「グループに分ける」／separate the items「アイテムを分離する」。受動態では'were divided'となります。学生は'were divide'と書いていますが、過去分詞'divided'が必要です。"

✓ "解説：confirm（動詞：確認する、裏付ける：事実を証明する場合）／prove（動詞：証明する：明確な証拠を示す場合）で、confirmは裏付けること、proveは証明することを指します。例：The results confirm the hypothesis.「結果が仮説を裏付ける」／This proves my point.「これが私の主張を証明する」。'has been confirm'は受動態なので過去分詞'confirmed'が必要です。'has been confirmed to have'で「〜の効果があることが確認されている」という意味になります。"

**【具体例：✅正解の場合】**
✓ "解説：address（動詞：問題に対処する・対応する：問題解決の文脈）／solve（動詞：問題を解決する：最終的な解決策の文脈）で、addressは問題に対する対応や対策を示し、solveは問題の完全な解決を指します。例：We need to address climate change.「気候変動に対処する必要があります。」／They solved the problem quickly.「彼らは問題を迅速に解決しました。」学生が使ったaddressは適切です。"

✓ "解説：stretching（動名詞：ストレッチをすること：運動や健康のために体を伸ばす行為）／exercise（名詞：運動：一般的な身体活動）で、stretchingは特に体を伸ばす運動を指します。例：I do stretching every morning.「毎朝ストレッチをします」／She exercises regularly.「彼女は定期的に運動しています」。学生の表現は正しいです。"

**❌ 禁止例（「解説：」がない・短すぎ・不十分・冗長）：**
✗ "'didn't showed' は二重否定で誤りです。正しくは 'showed' です。"（「解説：」なし）
✗ "'divided' に修正する必要があります。"（「解説：」なし、短すぎ）
✗ "原文に忠実にするため、..."（「解説：」なし、単語比較なし）
✗ "表現の一貫性を保つために統一しました。"（「解説：」なし、単語比較なし）
✗ "...学生の表現は文法的に正しいですが、文の流れを少し調整しました。"（✅正解なのに修正したかのような記述）
✗ "...学生の表現ではrollをrotateに変更しました。"（冗長な要約不要）
✗ "...学生の表現ではstiffnessが単数なので、hasに修正が必要です。"（冗長な要約不要）

**【重要】reasonの必須要素：**
1. **「解説：」で始める（絶対必須）**
2. reasonは最低でも80文字以上（日本語）
3. 単語の比較（A／B形式）を必ず含める
4. 例文を2つ以上（日本語訳付き、「／」または「。」で区切る）必ず含める
5. 学生の表現の評価を必ず含める
6. **冗長な要約文は禁止**：「学生の表現では〜に変更しました」「〜に修正が必要です」等の余計な要約は書かない

# 出力JSON形式

🚨🚨🚨【JSON出力前の最終確認】🚨🚨🚨
1. **日本語原文は何文ですか？全段落を通して「。」で区切って数えてください** → その数だけpointsを作成（必須）
   - 例：「AAAある。BBBする。」→ 2文 → points配列に2個
   - 例：（段落1）「XXXだ。YYYだ。」+（段落2）「ZZZだ。WWWだ。」→ 4文 → points配列に4個
   - **段落数ではなく、全段落の「。」の総数をカウント**
2. **各pointは1つの日本語文（「。」で区切られた1文）に対応していますか？** → 確認必須
3. **pointsの数が日本語原文の文数（全段落の「。」の総数）と一致していますか？** → 一致必須
4. **reasonは詳細な解説になっていますか？** → 80文字以上、単語比較+例文2つ以上

{{
  \"corrected\": \"（模範英訳、100-120語）\",
  \"overall_comment\": \"（全体的な講評、翻訳の質・改善点）\",
  \"points\": [
    {{
      \"japanese_sentence\": \"実験は、参加者を3つのグループに分けて行われた。\",
      \"before\": \"The experiment was done by dividing\",
      \"after\": \"The experiment was conducted by dividing\",
      \"reason\": \"解説：do（動詞：する、行う：日常的な行為）／conduct（動詞：実施する、遂行する：正式な調査や研究を行う場合）で、doは一般的な行為、conductは学術的・公式な実施を指します。例：do homework「宿題をする」／conduct an experiment「実験を実施する」。この文脈では、学術的な実験を表すため、conductの方が適切です。\",
      \"level\": \"💡改善提案\"
    }},
    {{
      \"japanese_sentence\": \"監督は、巧みな演出で観客を物語に引き込み、最後まで目が離せません。\",
      \"before\": \"The director draws the audience into the story\",
      \"after\": \"The director draws the audience into the story\",
      \"reason\": \"解説：draw into（句動詞：引き込む：物理的・感情的に引き寄せる場合）／engage（動詞：引きつける、関与させる：興味を持たせ続ける場合）で、draw intoは引き込む動作、engageは継続的な関心を指します。例：draw the audience into the story「観客を物語に引き込む」／engage the audience「観客を引きつける」。学生が使ったdraw intoは正しい表現です。\",
      \"level\": \"✅正しい表現\"
    }}
  ],
  \"word_count\": {word_count},
  \"constraint_checks\": {{
    \"word_count_ok\": true,
    \"has_clear_structure\": true,
    \"appropriate_vocabulary\": true
  }}
}}

# 注意事項【最重要】
- 「2理由」「First/Second」などの構成は要求しない（翻訳問題のため）
- 翻訳の正確性と自然さを最優先
- **pointsの数は日本語原文の文数と必ず一致（2文なら2個、3文なら3個）**
- **reasonは必ず日本語で詳しく記述（80文字以上、単語比較+例文2つ以上）**
- **減点不要な場合は before == after にする（修正文を表示しない）**
- **正解時は学生が使った語彙を解説する**
- JSON構文エラーを起こさないよう、引用符のエスケープを厳守
"""

# モデル解答生成用プロンプト（翻訳形式）
MODEL_ANSWER_PROMPT_MIYAZAKI_TRANSLATION = """
あなたは宮崎大学医学部の和文英訳問題の模範解答作成専門家です。

# 原文（日本語）
{question_text}

### 【翻訳の忠実性（絶対厳守）】
- **原文に書かれていない内容を追加してはならない（例文・結論・勧告等の創作禁止）**
- **原文の文の数と模範解答の文の数は必ず一致させる**
- 原文が4文なら模範解答も4文、5文なら5文（追加禁止）
- 各文は原文の対応する1文のみを翻訳する
- 「For example」「Therefore」「In another case」等で原文にない情報を追加することは厳禁

# 要件

1. **model_answer**: 自然で正確な英訳（100-120語目安）
   - 段落構造を維持
   - 翻訳として理想的な表現
   - 必ず100-120語に収める
   - 各文を改行（\\n\\n）で区切る
   - **原文の文数と必ず一致（追加・省略厳禁）**

2. **model_answer_explanation**: 一文ずつ詳細に解説（以下のフォーマット厳守）
   - **原文にない内容の解説は絶対に書かない**
   - 模範解答の全ての文（原文対応分のみ）を解説

**【必須フォーマット - kagoshima_100wordsスタイル】**:

```
文法・表現のポイント解説

1文目: （英文全文）
（日本語訳）
重要語A（品詞：意味の詳細説明：使用される文脈）／重要語B（品詞：意味の詳細説明：使用される文脈）で、AとBの使い分けを説明。例：例文1「日本語訳」／例文2「日本語訳」

2文目: （英文全文）
（日本語訳）
重要語C（品詞：意味の詳細説明：使用される文脈）／重要語D（品詞：意味の詳細説明：使用される文脈）で、CとDの使い分けを説明。例：例文1「日本語訳」／例文2「日本語訳」

（以下、全ての文について同様に記述）
```

**解説の詳細ルール**:
- 【絶対厳守】「英文:」「日本語訳:」「解説:」のラベルは書かない
- 【絶対厳守】Markdown記号（#、**、・など）や太字記号を使わない
- 【必須】冒頭に「文法・表現のポイント解説」と書く
- 【必須】各文は「n文目: 英文全文」で始める
- 【必須】次の行に「（日本語訳）」を書く
- 【必須】語彙解説は「単語A（品詞：詳細説明：文脈）／単語B（品詞：詳細説明：文脈）」形式
- 【必須】使い分けの説明と例文2つ以上（日本語訳付き、「／」で区切る）
- 模範解答の全ての文を解説（省略禁止）

# 解説の良い例（kagoshima_100wordsスタイル）

```
文法・表現のポイント解説

1文目: This table shows the annual average temperature changes in a certain city.
（この表は、ある都市の年間平均気温の変化を示している。）
show（動詞：情報やデータを示す・表示する：客観的な提示の文脈）／indicate（動詞：兆候や傾向を示す・指し示す：間接的な示唆の文脈）で、showは直接的に見せること、indicateは間接的に示唆することを指します。例：The graph shows a clear trend.「グラフは明確な傾向を示しています。」／This indicates a problem.「これは問題を示唆しています。」

2文目: Looking at the high school student data, we can see a sharp rise in temperature from spring to summer.
（高校生データを見ると、春から夏にかけて急激に気温が上昇していることがわかる。）
sharp（形容詞：急激な・鋭い：突然の大きな変化の文脈）／gradual（形容詞：段階的な・徐々の：ゆっくりとした変化の文脈）で、sharpは急激で明確な変化、gradualは緩やかな変化を示します。例：There was a sharp increase.「急激な増加がありました。」／The change was gradual.「変化は段階的でした。」

3文目: On the other hand, the university student data reveals a more pronounced temperature drop from autumn to winter.
（一方、大学生データでは、秋から冬にかけての気温低下がより顕著に現れている。）
pronounced（形容詞：顕著な・はっきりした：目立つ特徴の文脈）／noticeable（形容詞：目立つ・気づきやすい：認識できる程度の文脈）で、pronouncedはより強く際立っていること、noticeableは気づく程度であることを指します。例：There was a pronounced difference.「顕著な違いがありました。」／The change was noticeable.「変化は目立ちました。」

4文目: These data suggest that adjusting lifestyle habits according to seasonal temperature changes is important.
（これらのデータは、季節ごとの気温変化に応じた生活習慣の調整が重要であることを示唆している。）
suggest（動詞：提案する・示唆する：間接的に意味を伝える文脈）／prove（動詞：証明する・立証する：確実な根拠を示す文脈）で、suggestは可能性や推測を示し、proveは確実な証拠による証明を指します。例：The data suggest a correlation.「データは相関関係を示唆しています。」／This proves the theory.「これは理論を証明します。」
```

# 出力JSON形式

{{
  \"model_answer\": \"（模範英訳、100-120語、各文を\\n\\nで区切る）\",
  \"model_answer_explanation\": \"文法・表現のポイント解説\\n\\n1文目: ...\\n（...）\\n語彙解説...\\n\\n2文目: ...\\n（...）\\n語彙解説...\\n\\n（以下、全ての文について同様）\"
}}

# 注意事項
- JSON のみで返す
- コードブロック（```）禁止
- 「英文:」「日本語訳:」「解説:」ラベル禁止
- Markdown 記号（#、**など）禁止
- 日本語の引用符「」『』は使わない（半角ダブルクォートのみ）
- 引用符のエスケープを厳守
- 改行は \\n を使用
- 模範解答の全文を解説（省略禁止）
"""
