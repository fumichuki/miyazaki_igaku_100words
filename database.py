"""
データベース管理 - SQLite
鹿児島大学英作文特訓システム
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
DB_PATH = DATA_DIR / 'kagoshima_eisakubun.db'


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
                japanese_sentences TEXT NOT NULL,
                hints TEXT NOT NULL,
                target_words TEXT NOT NULL,
                model_answer TEXT,
                alternative_answer TEXT,
                common_mistakes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
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
        
        cursor.execute("""
            INSERT INTO questions (
                id, mode, theme, question_text, japanese_sentences, hints, target_words,
                model_answer, alternative_answer, common_mistakes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            question_id,
            "general",  # 理系・文系版のみ
            question.theme,
            question.question_text,  # 英語の問題文を保存
            json.dumps(question.japanese_sentences, ensure_ascii=False),
            json.dumps([h.model_dump() for h in question.hints], ensure_ascii=False),
            json.dumps(question.target_words.model_dump(), ensure_ascii=False),
            question.model_answer,
            question.alternative_answer,
            json.dumps(question.common_mistakes or [], ensure_ascii=False)
        ))
        
        conn.commit()
        logger.info(f"Question saved: {question_id} - {question.theme}")
    
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
            return dict(row)
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


# 初期化
init_database()
