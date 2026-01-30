"""
データベース管理 - SQLite
宮崎大学医学部英作文特訓システム
"""
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from models import QuestionResponse, CorrectionResponse
import uuid

logger = logging.getLogger(__name__)

# データベースファイルパス
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / 'miyazaki_igaku_eisakubun.db'


@contextmanager
def get_db_connection():
    """データベース接続を取得"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # 辞書形式で結果を取得
    try:
        yield conn
    finally:
        conn.close()


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
                excerpt_type TEXT,
                japanese_sentences TEXT NOT NULL,
                hints TEXT NOT NULL,
                target_words TEXT NOT NULL,
                model_answer TEXT,
                alternative_answer TEXT,
                common_mistakes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 既存テーブルにexcerpt_typeカラムが無ければ追加
        cursor.execute("PRAGMA table_info(questions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'excerpt_type' not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN excerpt_type TEXT")
            logger.info("Added excerpt_type column to questions table")
            conn.commit()
        
        # 提出テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id TEXT PRIMARY KEY,
                question_id TEXT NOT NULL,
                mode TEXT DEFAULT 'general',
                user_answer TEXT NOT NULL,
                corrected TEXT NOT NULL,
                word_count INTEGER,
                score_content INTEGER,
                score_structure INTEGER,
                score_vocabulary INTEGER,
                score_grammar INTEGER,
                score_word_count INTEGER,
                total_score INTEGER,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
        """)
        
        # 既出テーマテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS used_themes (
                theme TEXT PRIMARY KEY,
                mode TEXT DEFAULT 'general',
                count INTEGER DEFAULT 1,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # インデックス
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_submissions_question 
            ON submissions(question_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_used_themes_last_used 
            ON used_themes(last_used DESC)
        """)
        
        conn.commit()
        logger.info("Database initialized successfully")


# ===== 問題管理 =====

def save_question(question: QuestionResponse) -> str:
    """問題を保存"""
    # UUIDを使用してユニークなIDを生成
    question_id = f"q_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # まずテーブルにquestion_textカラムがあるか確認して、なければ追加
        cursor.execute("PRAGMA table_info(questions)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'question_text' not in columns:
            logger.info("Adding question_text column to questions table")
            cursor.execute("ALTER TABLE questions ADD COLUMN question_text TEXT")
            conn.commit()
        
        # japanese_paragraphsカラムがなければ追加
        if 'japanese_paragraphs' not in columns:
            logger.info("Adding japanese_paragraphs column to questions table")
            cursor.execute("ALTER TABLE questions ADD COLUMN japanese_paragraphs TEXT")
            conn.commit()
        
        # excerpt_typeカラムがなければ追加
        if 'excerpt_type' not in columns:
            logger.info("Adding excerpt_type column to questions table")
            cursor.execute("ALTER TABLE questions ADD COLUMN excerpt_type TEXT")
            conn.commit()
        
        # topic_labelカラムがなければ追加
        if 'topic_label' not in columns:
            logger.info("Adding topic_label column to questions table")
            cursor.execute("ALTER TABLE questions ADD COLUMN topic_label TEXT")
            conn.commit()
        
        cursor.execute("""
            INSERT INTO questions (
                id, mode, theme, topic_label, excerpt_type, question_text, japanese_sentences, japanese_paragraphs, 
                hints, target_words, model_answer, alternative_answer, common_mistakes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            question_id,
            "general",  # 理系・文系版のみ
            question.theme,
            question.topic_label,  # トピックラベル（A-H）
            question.excerpt_type,  # ← 追加
            question.question_text,  # 英語の問題文を保存
            json.dumps(question.japanese_sentences, ensure_ascii=False),
            json.dumps(question.japanese_paragraphs if question.japanese_paragraphs else [], ensure_ascii=False),
            json.dumps([h.model_dump() for h in question.hints], ensure_ascii=False),
            json.dumps(question.target_words.model_dump(), ensure_ascii=False),
            question.model_answer,
            question.alternative_answer,
            json.dumps(question.common_mistakes or [], ensure_ascii=False)
        ))
        
        conn.commit()
        logger.info(f"Question saved: {question_id} - {question.theme} ({question.excerpt_type})")
    
    # 既出テーマを記録
    record_used_theme(question.theme, "general")
    
    return question_id


def get_question(question_id: str) -> Optional[Dict[str, Any]]:
    """問題を取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
        row = cursor.fetchone()
        
        if row:
            data = dict(row)
            # JSONフィールドをパース
            if 'japanese_sentences' in data and data['japanese_sentences']:
                try:
                    data['japanese_sentences'] = json.loads(data['japanese_sentences'])
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse japanese_sentences for {question_id}")
            
            if 'japanese_paragraphs' in data and data['japanese_paragraphs']:
                try:
                    data['japanese_paragraphs'] = json.loads(data['japanese_paragraphs'])
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse japanese_paragraphs for {question_id}")
            
            if 'hints' in data and data['hints']:
                try:
                    data['hints'] = json.loads(data['hints'])
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse hints for {question_id}")
            
            if 'target_words' in data and data['target_words']:
                try:
                    data['target_words'] = json.loads(data['target_words'])
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse target_words for {question_id}")
            
            if 'common_mistakes' in data and data['common_mistakes']:
                try:
                    data['common_mistakes'] = json.loads(data['common_mistakes'])
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse common_mistakes for {question_id}")
            
            return data
        return None


# ===== 提出管理 =====

def save_submission(
    question_id: str,
    user_answer: str,
    correction: CorrectionResponse
) -> str:
    """提出を保存（採点機能なし）"""
    # UUIDを使用してユニークなIDを生成
    submission_id = f"s_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 採点機能を削除したため、スコア関連のカラムにはNULLを保存
        cursor.execute("""
            INSERT INTO submissions (
                id, question_id, mode, user_answer, corrected, word_count,
                score_content, score_structure, score_vocabulary,
                score_grammar, score_word_count, total_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            submission_id,
            question_id,
            "general",  # 理系・文系版のみ
            user_answer,
            correction.corrected,
            correction.word_count,
            None,  # score_content (採点なし)
            None,  # score_structure (採点なし)
            None,  # score_vocabulary (採点なし)
            None,  # score_grammar (採点なし)
            None,  # score_word_count (採点なし)
            None   # total_score (採点なし)
        ))
        
        conn.commit()
        logger.info(f"Submission saved: {submission_id} (mode: general, no scoring)")
    
    return submission_id


def get_submission_history(limit: int = 50) -> List[Dict[str, Any]]:
    """提出履歴を取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                s.*,
                q.theme,
                q.japanese_sentences
            FROM submissions s
            JOIN questions q ON s.question_id = q.id
            ORDER BY s.submitted_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_statistics() -> Dict[str, Any]:
    """統計情報を取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 総提出数
        cursor.execute("SELECT COUNT(*) as count FROM submissions")
        total_submissions = cursor.fetchone()['count']
        
        # 平均スコア
        cursor.execute("SELECT AVG(total_score) as avg_score FROM submissions")
        avg_score = cursor.fetchone()['avg_score'] or 0
        
        # 最高スコア
        cursor.execute("SELECT MAX(total_score) as max_score FROM submissions")
        max_score = cursor.fetchone()['max_score'] or 0
        
        # 項目別平均スコア
        cursor.execute("""
            SELECT 
                AVG(score_content) as avg_content,
                AVG(score_structure) as avg_structure,
                AVG(score_vocabulary) as avg_vocabulary,
                AVG(score_grammar) as avg_grammar,
                AVG(score_word_count) as avg_word_count
            FROM submissions
        """)
        avg_scores = cursor.fetchone()
        
        return {
            'total_submissions': total_submissions,
            'average_score': round(avg_score, 2),
            'max_score': max_score,
            'average_scores': {
                'content': round(avg_scores['avg_content'] or 0, 2),
                'structure': round(avg_scores['avg_structure'] or 0, 2),
                'vocabulary': round(avg_scores['avg_vocabulary'] or 0, 2),
                'grammar': round(avg_scores['avg_grammar'] or 0, 2),
                'word_count': round(avg_scores['avg_word_count'] or 0, 2)
            }
        }


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
        
        return [row[0] for row in cursor.fetchall() if row[0]]


def should_avoid_excerpt_type(excerpt_type: str) -> bool:
    """特定の抜粋タイプを避けるべきか判定"""
    recent = get_recent_excerpt_types(10)
    count = recent.count(excerpt_type)
    
    # 直近10問で3回以上同じタイプなら避ける
    return count >= 3


# ===== 既出テーマ管理（重複回避） =====

def record_used_theme(theme: str, mode: str = "general"):
    """テーマの使用を記録"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 既存のテーマを確認（modeも考慮）
        cursor.execute("SELECT count FROM used_themes WHERE theme = ? AND mode = ?", (theme, mode))
        row = cursor.fetchone()
        
        if row:
            # 既存のテーマなら使用回数を増やす
            cursor.execute("""
                UPDATE used_themes 
                SET count = count + 1, last_used = CURRENT_TIMESTAMP
                WHERE theme = ? AND mode = ?
            """, (theme, mode))
        else:
            # 新規テーマなら挿入
            cursor.execute("""
                INSERT INTO used_themes (theme, mode, count, last_used)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            """, (theme, mode))
        
        conn.commit()
        logger.info(f"Theme recorded: {theme} (mode: {mode})")


def get_excluded_themes(max_recent: int = 10) -> List[str]:
    """最近使用されたテーマを取得（重複回避用）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT theme 
            FROM used_themes 
            ORDER BY last_used DESC 
            LIMIT ?
        """, (max_recent,))
        
        rows = cursor.fetchall()
        themes = [row['theme'] for row in rows]
        
        logger.info(f"Excluded themes: {themes}")
        return themes


def get_theme_statistics() -> List[Dict[str, Any]]:
    """テーマの使用統計を取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT theme, count, last_used
            FROM used_themes
            ORDER BY count DESC, last_used DESC
            LIMIT 20
        """)
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_recent_themes(limit: int = 20) -> List[str]:
    """
    直近N問のtheme（ジャンル）を取得（新しい順）
    
    Args:
        limit: 取得する問題数
    
    Returns:
        themeのリスト（新しい順）
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT theme
            FROM questions
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        themes = [row['theme'] for row in rows]
        
        return themes


def get_recent_subtopics(limit: int = 10) -> List[str]:
    """
    直近N問のサブトピック（A-H）をhintsから推測して取得（新しい順）
    
    各ジャンルには8つのトピック領域（A-H）が定義されている。
    hintsの内容をキーワードマッチで分類する。
    
    Args:
        limit: 取得する問題数
    
    Returns:
        "ジャンル:トピック"形式のリスト（例: "研究紹介:C", "時事:A"）
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT theme, hints, japanese_sentences
            FROM questions
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        
        import json
        subtopics = []
        
        # キーワードマッピング（全7ジャンル対応）
        topic_keywords = {
            "研究紹介": {
                "A": ["記憶", "暗記", "想起", "テスト効果", "学習"],
                "B": ["習慣", "継続", "報酬", "トリガー", "行動"],
                "C": ["睡眠", "昼寝", "集中", "注意力"],
                "D": ["運動", "ストレッチ", "姿勢", "健康", "軽運動"],
                "E": ["食事", "カフェイン", "朝食", "間食", "嗜好"],
                "F": ["ストレス", "不安", "怒り", "リラックス", "感情"],
                "G": ["スマホ", "デジタル", "通知", "SNS"],
                "H": ["協力", "共感", "コミュニケーション", "社会行動"]
            },
            "時事": {
                "A": ["医療", "ワクチン", "感染症", "病院", "公衆衛生"],
                "B": ["科学", "研究", "発見", "論文", "倫理"],
                "C": ["AI", "テクノロジー", "データ", "セキュリティ"],
                "D": ["環境", "災害", "猛暑", "洪水", "防災"],
                "E": ["教育", "学校", "学力", "いじめ", "若者"],
                "F": ["労働", "外国人", "少子", "高齢化", "人口"],
                "G": ["経済", "物価", "住宅", "交通", "生活"],
                "H": ["法", "規制", "プライバシー", "制度", "行政"]
            },
            "学術": {
                "A": ["心理", "療法", "メンタル", "認知"],
                "B": ["反復", "間隔", "記憶", "定着"],
                "C": ["予防", "患者", "生活習慣"],
                "D": ["脳", "注意", "意思決定", "バイアス"],
                "E": ["対人", "支援", "共感"],
                "F": ["自己制御", "動機", "習慣"],
                "G": ["研究倫理", "プライバシー"],
                "H": ["睡眠", "運動", "食行動"]
            },
            "ブログ": {
                "A": ["スマホ", "通知", "SNS"],
                "B": ["体", "不調", "首", "目", "肩", "睡眠"],
                "C": ["待ち時間", "移動", "通勤", "通学"],
                "D": ["学習", "仕事", "習慣"],
                "E": ["お金", "買い物", "片づけ"],
                "F": ["気分転換", "ストレス"],
                "G": ["人間関係", "会話", "気疲れ"],
                "H": ["食事", "カフェイン", "生活リズム"]
            },
            "レビュー": {
                "A": ["映画", "ヒューマン", "ドラマ"],
                "B": ["本", "ノンフィクション", "エッセイ"],
                "C": ["ドキュメンタリー", "記事"],
                "D": ["展示", "舞台", "イベント"],
                "E": ["ボランティア", "実習", "体験"],
                "F": ["サービス", "図書館", "施設"],
                "G": ["仕事", "職業", "使命"],
                "H": ["場面", "心に残る"]
            },
            "コラム": {
                "A": ["マナー", "音", "ゴミ"],
                "B": ["学校", "宿題", "ICT", "評価"],
                "C": ["働き方", "リモート", "労働"],
                "D": ["医療", "予防", "検診"],
                "E": ["地域", "多文化", "共生", "町"],
                "F": ["デジタル", "依存", "プライバシー"],
                "G": ["環境", "節電", "リサイクル"],
                "H": ["若者", "家庭", "時間"]
            },
            "図表": {
                "A": ["学習時間", "スマホ時間"],
                "B": ["睡眠時間", "疲労"],
                "C": ["図書館", "施設", "利用", "曜日"],
                "D": ["交通", "通勤", "利用者"],
                "E": ["運動", "検診", "健康行動"],
                "F": ["アンケート", "満足度", "意識"],
                "G": ["年代", "若年", "中年", "高齢"],
                "H": ["地域", "都市", "地方"]
            }
        }
        
        for row in rows:
            theme = row['theme']
            hints_str = row['hints'] or ""
            ja_sentences = row['japanese_sentences'] or ""
            
            # 全ジャンル対応
            if theme in topic_keywords:
                # hintsとja_sentencesを結合してテキスト検索
                full_text = hints_str + " " + ja_sentences
                
                # 最もマッチするトピックを探す
                max_matches = 0
                best_topic = "不明"
                
                for topic, keywords in topic_keywords[theme].items():
                    matches = sum(1 for kw in keywords if kw in full_text)
                    if matches > max_matches:
                        max_matches = matches
                        best_topic = topic
                
                subtopics.append(f"{theme}:{best_topic}")
            else:
                # マッピング未定義のジャンル
                subtopics.append(f"{theme}:未分類")
        
        return subtopics


# 初期化
init_database()

