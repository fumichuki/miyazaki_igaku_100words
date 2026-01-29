# 段落抜粋出題の実装TODO

## 概要
「段落抜粋出題（1段目だけ／2〜3段目／3段目だけ）」を実現するための実装計画。
現状それが安定して出ない理由と、具体的な修正箇所を記載。

---

## 1) 現状の問題点（なぜ「狙った抜粋」にならないのか）

### A. 仕様（狙い）と出力（現実）のズレ

**設計意図:**
- 過去問は「複数段落の文章」だが、ユーザー疲労を避けるため抜粋したい

**現実の問題:**
- 「抜粋の型」が明確に固定されていないため、LLM側が以下の傾向を示す：
  - ❌ **導入（P1）から始めがち**
  - ❌ **2〜3段落抜粋に偏る/全文っぽくなる**
  - ❌ **「3段目だけ」のような意図的に中腹だけ切り出す出題が安定しない**

### B. "抜粋モード"のメタ情報が存在しない

**問題点:**
- 「今回はP1だけ」「今回はP2-3」「今回はP3だけ」などの**抜粋タイプを、JSONに明示するフィールドがない**

**影響:**
- ❌ 生成物が狙い通りか検証できない
- ❌ フロントで「今どの抜粋か」を表示できない
- ❌ DBに履歴として残せない（偏り検出も不可能）
- → 結果、運用で品質が上がらない

### C. バリデーション不足

**問題点:**
`models.py` の `QuestionResponse` は `japanese_paragraphs` を受け取れるが、以下のチェックが弱い/無い：

- ❌ 段落数が 1〜3 に収まっているか
- ❌ 「P3だけ」の時に自己完結する書き方になっているか（指示語だらけで破綻してないか）
- ❌ 段落あたりの文数が過剰でないか

**影響:**
- LLMが規則を破っても通ってしまい、UIにそのまま出る

### D. そもそも "問題生成プロンプト" が正しく使われていない（🔴重大バグ）

**問題点:**
- `llm_service.py` の `generate_question()` が `PROMPTS['question']` を参照している（llm_service.py:1083 付近）
- しかし `prompts_translation_simple.py` の `PROMPTS` には `'question'` が存在しない（`'correction'` しかない）
- → **実運用だと KeyError で問題生成が壊れる可能性が高い**

**さらに:**
- 本命の抜粋用プロンプト `QUESTION_PROMPT_MIYAZAKI_TRANSLATION`（`prompts_translation.py`）が、**生成に使われていない**

### E. フロントが「抜粋であること」を前提にしていない

**問題点:**
`static/main.js` は `japanese_paragraphs` を箇条書き表示するだけで、以下を一切表示しない：

- それが「抜粋」なのか
- どの抜粋タイプなのか

**影響:**
- ユーザー体験として「全文の一部なんだ」と理解しづらい

---

## 2) エージェントに投げる実装TODO（ファイル別・修正点つき）

### ✅ ToDo 1：問題生成が壊れている参照を直す（🔴最優先）

**対象:** `llm_service.py`  
**修正箇所:** `generate_question()` の `prompt_template = PROMPTS['question']`（1083行付近）

**やること:**
1. `PROMPTS['question']` を使うのをやめて、`QUESTION_PROMPT_MIYAZAKI_TRANSLATION` を使うように変更
2. `prompt = QUESTION_PROMPT_MIYAZAKI_TRANSLATION.format(...)` で以下を差し込む：
   - `past_questions_reference`
   - `excluded_themes`
   - （すでにプロンプト側にプレースホルダあり）

**狙い:**
- 抜粋出題専用プロンプトを確実に適用し、まず出題機能を安定させる

---

### ✅ ToDo 2：「抜粋タイプ」をJSONに明示して制御する

**対象:** `prompts_translation.py`  
**修正箇所:** 出力形式・要件（`japanese_paragraphs`の説明がある 240行前後）

**やること:**

#### 1. JSON出力に `excerpt_type` を追加する

```json
{
  "theme": "研究紹介",
  "excerpt_type": "P2_P3",
  "japanese_paragraphs": ["段落2の内容", "段落3の内容"],
  "hints": [...]
}
```

#### 2. 抜粋タイプの定義

- **`P1_ONLY`**: 1段目だけ（導入部分）
- **`P2_P3`**: 2〜3段目（中盤）
- **`P3_ONLY`**: 3段目だけ（結果/評価部分）
- **`P4_P5`**: 4〜5段目（結論部分）※稀
- **`MIDDLE`**: 中盤の連続する1〜2段落

#### 3. 抜粋タイプの選択ルール（プロンプトに明記）

```
【抜粋タイプの選択ルール】
以下のいずれかを選択してください：

1. P1_ONLY（導入のみ）: 20%の確率
   - 背景/問題提起/概要を1段落で
   - 自己完結するように書く

2. P2_P3（中盤）: 50%の確率（最も推奨）
   - 方法/条件/比較/影響など
   - 接続語（「その研究では」「また」「一方で」）を含める
   - 指示語は最小限にし、前提を軽く含める

3. P3_ONLY（結果/評価のみ）: 20%の確率
   - 結果/効果/評価を1段落で
   - 「その結果」「このように」などで始めてよい
   - ただし指示語で破綻しないよう、冒頭に最小限の前提を置く

4. P4_P5（結論）: 10%の確率（稀）
   - まとめ/提案/見通しなど

【P3_ONLY / P1_ONLYの注意】
- 「その研究」「このプログラム」などの指示語で破綻しないこと
- 冒頭に最小限の前提を置く（ただし"全文の導入"には戻らない）
- 例: 「ある研究の結果、〜」「このような技術の進歩には〜」
```

#### 4. プロンプトへの追記箇所

```python
出力形式（JSONのみ／Markdown禁止／コードブロック禁止）：
{{
  "theme": "研究紹介",
  "excerpt_type": "P2_P3",  # ← 追加
  "japanese_paragraphs": ["（抜粋段落1）", "（必要なら抜粋段落2）"],
  "hints": [
    {{"en":"...", "ja":"...", "kana":"...", "pos":"...", "usage":"..."}},
  ],
  "target_words": {{"min":100, "max":120}}
}}
```

---

### ✅ ToDo 3：モデルで"抜粋として妥当か"を機械的に弾く

**対象:** `models.py`  
**修正箇所:** `QuestionResponse`

**やること:**

#### 1. フィールド追加

```python
class QuestionResponse(BaseModel):
    theme: str
    excerpt_type: Optional[str] = None  # ← 追加
    japanese_paragraphs: Optional[List[str]] = None
    japanese_sentences: Optional[List[str]] = None
    hints: List[Hint]
    target_words: Optional[Dict[str, int]] = None
```

#### 2. バリデーション追加

```python
@validator('japanese_paragraphs')
def validate_paragraphs(cls, v, values):
    """段落の妥当性をチェック"""
    if v is None:
        return v
    
    # 段落数チェック（1〜3段落）
    if not (1 <= len(v) <= 3):
        raise ValueError(f"japanese_paragraphs は 1〜3個である必要があります（現在: {len(v)}個）")
    
    # excerpt_type との整合性チェック
    excerpt_type = values.get('excerpt_type')
    if excerpt_type:
        expected_count = {
            'P1_ONLY': 1,
            'P2_P3': 2,
            'P3_ONLY': 1,
            'P4_P5': 2,
            'MIDDLE': (1, 2)
        }
        
        if excerpt_type in expected_count:
            expected = expected_count[excerpt_type]
            if isinstance(expected, int):
                if len(v) != expected:
                    raise ValueError(
                        f"excerpt_type={excerpt_type} の場合、段落数は {expected} である必要があります（現在: {len(v)}）"
                    )
            elif isinstance(expected, tuple):
                if not (expected[0] <= len(v) <= expected[1]):
                    raise ValueError(
                        f"excerpt_type={excerpt_type} の場合、段落数は {expected[0]}〜{expected[1]} である必要があります（現在: {len(v)}）"
                    )
    
    # 段落あたりの文数チェック（極端に長い段落を弾く）
    for i, paragraph in enumerate(v):
        sentence_count = paragraph.count('。')
        if sentence_count > 5:
            raise ValueError(
                f"段落{i+1}の文数が多すぎます（{sentence_count}文）。1段落は5文以内にしてください。"
            )
    
    return v
```

---

### ✅ ToDo 4：生成失敗時に"抜粋条件違反"を再生成する

**対象:** `llm_service.py`  
**修正箇所:** `generate_question()` のリトライループ

**やること:**

#### 1. リトライ時に違反理由を追記

```python
def generate_question(theme: Optional[str] = None, max_retries: int = 3) -> QuestionResponse:
    """問題を生成"""
    
    for attempt in range(max_retries):
        try:
            # プロンプト生成
            prompt = QUESTION_PROMPT_MIYAZAKI_TRANSLATION.format(
                past_questions_reference=past_questions_ref,
                excluded_themes=excluded_themes_text
            )
            
            # リトライ時は条件を追記
            if attempt > 0:
                retry_instructions = "\n\n【前回の生成で以下の問題がありました。修正してください】\n"
                if 'paragraph_count_mismatch' in retry_reason:
                    retry_instructions += "- 段落数が excerpt_type と一致していません\n"
                if 'too_many_sentences' in retry_reason:
                    retry_instructions += "- 1段落の文数が多すぎます（5文以内にしてください）\n"
                if 'missing_excerpt_type' in retry_reason:
                    retry_instructions += "- excerpt_type フィールドが必須です\n"
                
                prompt += retry_instructions
            
            # LLM呼び出し
            response = call_openai_with_retry(prompt, temperature=0.7)
            
            # パース
            data = parse_json_response(response)
            
            # バリデーション（ここで ValueError が発生する可能性）
            question = QuestionResponse(**data)
            
            return question
            
        except ValueError as e:
            logger.warning(f"生成失敗 (attempt {attempt + 1}/{max_retries}): {e}")
            
            # 次回リトライのための理由を記録
            retry_reason = []
            error_msg = str(e)
            
            if '段落数' in error_msg:
                retry_reason.append('paragraph_count_mismatch')
            if '文数が多すぎ' in error_msg:
                retry_reason.append('too_many_sentences')
            if 'excerpt_type' in error_msg:
                retry_reason.append('missing_excerpt_type')
            
            if attempt == max_retries - 1:
                raise
            
            # 少し待ってからリトライ
            time.sleep(1)
    
    raise Exception("問題生成に失敗しました")
```

---

### ✅ ToDo 5：UIに「抜粋タイプ」を表示する

**対象:** `static/main.js`  
**修正箇所:** `displayQuestion()` の `japanese_paragraphs` 表示部分（248行付近）

**やること:**

#### 1. excerpt_type の表示を追加

```javascript
} else if (data.japanese_paragraphs && data.japanese_paragraphs.length > 0) {
  // 翻訳形式（段落→一文一文箇条書き）の場合
  const theme = data.theme || "学術";
  
  // テーマヘッダー
  const themeHeader = document.createElement("div");
  themeHeader.className = "theme-header-question";
  themeHeader.textContent = `📌 テーマ: ${theme}　　下記を英訳せよ`;
  container.appendChild(themeHeader);
  
  // 抜粋タイプの表示を追加
  if (data.excerpt_type) {
    const excerptInfo = document.createElement("div");
    excerptInfo.className = "excerpt-type-info";
    
    const excerptLabels = {
      'P1_ONLY': '（抜粋：段落①のみ）',
      'P2_P3': '（抜粋：段落②〜③）',
      'P3_ONLY': '（抜粋：段落③のみ）',
      'P4_P5': '（抜粋：段落④〜⑤）',
      'MIDDLE': '（抜粋：中盤部分）'
    };
    
    excerptInfo.textContent = excerptLabels[data.excerpt_type] || '（抜粋）';
    container.appendChild(excerptInfo);
  }
  
  // 問題文の表示（箇条書き）
  const ul = document.createElement("ul");
  ul.className = "question-sentences-list";
  // ... 以下既存コード
}
```

#### 2. CSSスタイル追加（`static/style.css`）

```css
.excerpt-type-info {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
  font-style: italic;
}
```

---

### ✅ ToDo 6（任意だが強い）：DBに excerpt_type を保存して偏り検知できるようにする

**対象:** `database.py`  
**修正箇所:** `save_question()` のカラム追加ロジック

**やること:**

#### 1. テーブルにカラム追加

```python
def init_database():
    """データベースを初期化"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 問題テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                mode TEXT DEFAULT 'general',
                theme TEXT NOT NULL,
                excerpt_type TEXT,  -- ← 追加
                japanese_sentences TEXT NOT NULL,
                japanese_paragraphs TEXT,  -- 既存
                hints TEXT NOT NULL,
                ...
            )
        """)
        
        # 既存テーブルにカラムが無ければ追加
        cursor.execute("PRAGMA table_info(questions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'excerpt_type' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN excerpt_type TEXT")
            logger.info("Added excerpt_type column to questions table")
        
        conn.commit()
```

#### 2. 保存・取得時に扱う

```python
def save_question(question: QuestionResponse) -> str:
    """問題を保存"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        question_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO questions (
                id, theme, excerpt_type, japanese_paragraphs, 
                japanese_sentences, hints, target_words, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            question_id,
            question.theme,
            question.excerpt_type,  # ← 追加
            json.dumps(question.japanese_paragraphs, ensure_ascii=False) if question.japanese_paragraphs else None,
            json.dumps(question.japanese_sentences, ensure_ascii=False) if question.japanese_sentences else None,
            json.dumps([h.dict() for h in question.hints], ensure_ascii=False),
            json.dumps(question.target_words, ensure_ascii=False) if question.target_words else None,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        return question_id
```

#### 3. 偏り検知ロジック

```python
def get_recent_excerpt_types(limit: int = 10) -> List[str]:
    """直近N問の抜粋タイプを取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT excerpt_type 
            FROM questions 
            WHERE excerpt_type IS NOT NULL
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        return [row[0] for row in cursor.fetchall()]

def should_avoid_excerpt_type(excerpt_type: str) -> bool:
    """特定の抜粋タイプを避けるべきか判定"""
    recent = get_recent_excerpt_types(10)
    count = recent.count(excerpt_type)
    
    # 直近10問で3回以上同じタイプなら避ける
    return count >= 3
```

---

## 3) 受け入れ条件（ここまでできたら"仕様どおり"）

### ✅ チェックリスト

- [ ] `/api/question` を連続で叩いた時に、`P1_ONLY` / `P2_P3` / `P3_ONLY` が混ざって出る
- [ ] どれも `japanese_paragraphs` が **1〜2段落中心（最大3）** で、ユーザーが疲れない分量
- [ ] UIに「抜粋：段落②〜③」などが出て、ユーザーが混乱しない
- [ ] 生成が失敗しても、リトライで条件を満たしたJSONに収束する
- [ ] DBに `excerpt_type` が保存され、偏り検知ができる

### ✅ テスト手順

#### 1. 問題生成テスト

```bash
# 10回連続で問題生成
for i in {1..10}; do
  curl http://localhost:8001/api/question
  echo "\n---\n"
done
```

**確認事項:**
- `excerpt_type` が出力されているか
- P1_ONLY, P2_P3, P3_ONLY が適度に混ざっているか
- 段落数が excerpt_type と一致しているか

#### 2. バリデーションテスト

```python
# models.py のバリデーションが機能するか
from models import QuestionResponse

# ❌ 段落数が多すぎる（4段落）
try:
    QuestionResponse(
        theme="研究",
        excerpt_type="P2_P3",
        japanese_paragraphs=["段落1", "段落2", "段落3", "段落4"],
        hints=[]
    )
except ValueError as e:
    print(f"✅ 正常に弾かれた: {e}")

# ❌ excerpt_type と段落数が不一致
try:
    QuestionResponse(
        theme="研究",
        excerpt_type="P1_ONLY",
        japanese_paragraphs=["段落1", "段落2"],
        hints=[]
    )
except ValueError as e:
    print(f"✅ 正常に弾かれた: {e}")
```

#### 3. UI表示テスト

1. ブラウザで http://localhost:8001 にアクセス
2. 「問題を取得」ボタンを押す
3. 以下が表示されることを確認：
   - テーマヘッダー
   - **抜粋タイプ（例: 「（抜粋：段落②〜③）」）**
   - 問題文の箇条書き

---

## 4) 実装の優先順位

| 優先度 | ToDo | 理由 |
|--------|------|------|
| 🔴 最優先 | ToDo 1 | 問題生成が壊れている（KeyError） |
| 🟡 高 | ToDo 2 | 抜粋タイプの明示化（仕様の根幹） |
| 🟡 高 | ToDo 3 | バリデーション（品質担保） |
| 🟢 中 | ToDo 4 | リトライロジック（安定性向上） |
| 🟢 中 | ToDo 5 | UI表示（UX改善） |
| 🔵 低 | ToDo 6 | DB保存と偏り検知（運用改善） |

---

## 5) 実装後の期待される動作

### 例1: P1_ONLY（導入のみ）

**生成されるJSON:**
```json
{
  "theme": "研究紹介",
  "excerpt_type": "P1_ONLY",
  "japanese_paragraphs": [
    "ある研究によると、右手を握りしめることで出来事や行動のより強い記憶を形成し、左手を握りしめることでその記憶を後に思い出すのに役立つ可能性があります。"
  ],
  "hints": [...]
}
```

**UI表示:**
```
📌 テーマ: 研究紹介　　下記を英訳せよ
（抜粋：段落①のみ）
• ある研究によると、右手を握りしめることで出来事や行動のより強い記憶を形成し、左手を握りしめることでその記憶を後に思い出すのに役立つ可能性があります。
```

### 例2: P2_P3（中盤）

**生成されるJSON:**
```json
{
  "theme": "研究紹介",
  "excerpt_type": "P2_P3",
  "japanese_paragraphs": [
    "その研究の参加者は４つのグループに分けられ、まず72語のリストから単語を記憶し、後でそれらを思い出すように求められました。",
    "１つのグループは、リストを記憶する直前に約90秒間右手を握りしめ、その後単語を思い出す直前にも同じことを行いました。別のグループは、記憶する前と思い出す前の両方で左手を握りしめました。"
  ],
  "hints": [...]
}
```

**UI表示:**
```
📌 テーマ: 研究紹介　　下記を英訳せよ
（抜粋：段落②〜③）
• その研究の参加者は４つのグループに分けられ、まず72語のリストから単語を記憶し、後でそれらを思い出すように求められました。
• １つのグループは、リストを記憶する直前に約90秒間右手を握りしめ、その後単語を思い出す直前にも同じことを行いました。
• 別のグループは、記憶する前と思い出す前の両方で左手を握りしめました。
```

### 例3: P3_ONLY（結果のみ）

**生成されるJSON:**
```json
{
  "theme": "研究紹介",
  "excerpt_type": "P3_ONLY",
  "japanese_paragraphs": [
    "その結果、リストを記憶する際に右手を握りしめ、単語を思い出す際に左手を握りしめたグループは、他のグループより良い成績を記録しました。"
  ],
  "hints": [...]
}
```

**UI表示:**
```
📌 テーマ: 研究紹介　　下記を英訳せよ
（抜粋：段落③のみ）
• その結果、リストを記憶する際に右手を握りしめ、単語を思い出す際に左手を握りしめたグループは、他のグループより良い成績を記録しました。
```

---

## 6) 関連ファイル一覧

| ファイル | 役割 | 修正内容 |
|---------|------|---------|
| `prompts_translation.py` | 問題生成プロンプト | excerpt_type の追加、選択ルールの明記 |
| `llm_service.py` | LLM呼び出し | QUESTION_PROMPT_MIYAZAKI_TRANSLATION の使用、リトライロジック |
| `models.py` | データモデル | excerpt_type フィールド追加、バリデーション |
| `static/main.js` | フロントエンド | excerpt_type の表示 |
| `static/style.css` | スタイル | excerpt-type-info のスタイル追加 |
| `database.py` | DB操作 | excerpt_type カラム追加、偏り検知 |

---

## 7) 注意事項

### ⚠️ 既存データへの影響

- `excerpt_type` は新規追加フィールドのため、既存の問題データには `NULL` が入る
- 既存データは引き続き動作するが、抜粋タイプの表示はされない
- マイグレーションは自動で行われる（`ALTER TABLE` で追加）

### ⚠️ 後方互換性

- `excerpt_type` は `Optional` なので、古い形式のJSONも受け付ける
- ただし、新規生成では必須にすることを推奨

### ⚠️ テスト環境での確認

- 本番環境に適用する前に、必ずテスト環境で以下を確認：
  1. 問題生成が正常に動作するか
  2. バリデーションが機能するか
  3. UI表示が正しいか
  4. DBへの保存・取得が正常か

---

## 8) 実装完了後の確認事項

- [ ] `llm_service.py` で `QUESTION_PROMPT_MIYAZAKI_TRANSLATION` が使用されている
- [ ] `prompts_translation.py` に `excerpt_type` の選択ルールが明記されている
- [ ] `models.py` に `excerpt_type` フィールドとバリデーションが追加されている
- [ ] `static/main.js` で抜粋タイプが表示されている
- [ ] `database.py` で `excerpt_type` が保存・取得できる
- [ ] 連続生成で P1_ONLY, P2_P3, P3_ONLY が適度に混ざる
- [ ] 段落数が 1〜3 に収まっている
- [ ] UI表示が適切（抜粋タイプのラベル付き）
- [ ] エラーハンドリングが機能している（リトライで収束）

---

以上が段落抜粋出題を実現するための実装TODOです。
優先順位に従って実装を進めてください。
