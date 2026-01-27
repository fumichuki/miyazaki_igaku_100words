"""
Configuration settings for Miyazaki University School of Medicine English Writing System
宮崎大学医学部英作文特訓システム - 設定管理（100字指定）
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 環境変数をロード
load_dotenv()

# ===== Application Settings =====

APP_NAME = "みや塾　英作文特訓講座　宮崎大学医学部（100字指定）"
APP_VERSION = "3.0.0"  # 理系・文系専用版
DEBUG_MODE = os.getenv("DEBUG", "true").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8001"))

# ===== Database Settings =====

DATA_DIR = Path('data')
DB_PATH = DATA_DIR / 'miyazaki_igaku_eisakubun.db'
PAST_QUESTIONS_JSON = DATA_DIR / 'past_questions.json'

# ===== OpenAI Settings =====

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))

# ===== Word Count Settings =====

# 理系・文系版の語数設定
WORD_COUNT = {
    "min": 80,
    "max": 120,
    "target": 100
}

# 制約チェック設定
WORD_COUNT_TOLERANCE = 0  # 語数の許容誤差
MIN_WORD_COUNT_ABSOLUTE = 60  # 絶対的な最小語数
MAX_WORD_COUNT_ABSOLUTE = 200  # 絶対的な最大語数

# ===== Question Generation Settings =====

# 除外テーマの最大数
MAX_EXCLUDED_THEMES = 10

# ===== Correction Settings =====

# スコアリング設定
SCORING_WEIGHTS = {
    "content": 5,        # 内容
    "structure": 5,      # 構成
    "vocabulary": 5,     # 語彙
    "grammar": 5,        # 文法
    "word_count": 5      # 語数
}

# ===== Validation Settings =====

# Two-units検証の信頼度レベル
CONFIDENCE_LEVELS = {
    "high": 0.9,     # 高信頼度（First/Second等の明示的マーカー）
    "medium": 0.7,   # 中信頼度（複数のbecause/therefore等）
    "low": 0.5       # 低信頼度（ヒューリスティック）
}

# 談話標識（Discourse Markers）
DISCOURSE_MARKERS = {
    "first": ["first", "firstly", "first of all", "to begin with"],
    "second": ["second", "secondly", "in addition", "furthermore", "moreover"],
    "third": ["third", "thirdly", "finally", "lastly"],
    "conclusion": ["in conclusion", "to conclude", "in summary", "to sum up"]
}

# ===== Outline Generation Settings =====

# セクション別の推奨文数
SECTION_SENTENCES = {
    "introduction": 2,
    "body": 3,
    "conclusion": 2
}

# 語数推定の係数（1文あたりの平均語数）
WORDS_PER_SENTENCE = 15

# ===== Logging Settings =====

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ===== Feature Flags =====

FEATURES = {
    "constraint_validation": True,   # Phase 1: 制約チェック
    "outline_support": True,         # Phase 3: アウトライン支援
    "database_storage": True,        # データベース保存
    "theme_tracking": True           # テーマ重複回避
}

# ===== API Settings =====

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
API_VERSION = "v1"
API_PREFIX = "/api"

# レート制限（将来の拡張用）
RATE_LIMIT = {
    "enabled": False,
    "requests_per_minute": 60
}

# ===== Development Settings =====

# テスト用のフォールバック問題
FALLBACK_QUESTION = {
    "theme": "英語学習の重要性",
    "japanese_sentences": [
        "英語を学ぶことは大切だと思う。",
        "世界中の人とコミュニケーションができるからだ。",
        "また、たくさんの情報にアクセスできる。"
    ],
    "hints": [
        {"en": "communicate", "ja": "コミュニケーションする", "kana": "こみゅにけーしょんする"},
        {"en": "access", "ja": "アクセスする", "kana": "あくせすする"},
        {"en": "information", "ja": "情報", "kana": "じょうほう"}
    ]
}

# ===== Validation =====

def validate_config():
    """設定の検証"""
    errors = []
    
    # OpenAI API Key
    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is not set")
    
    # データディレクトリ
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # ポート番号
    if not (1024 <= PORT <= 65535):
        errors.append(f"Invalid PORT: {PORT} (must be 1024-65535)")
    
    return errors


if __name__ == "__main__":
    # 設定の検証
    errors = validate_config()
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuration validated successfully")
        print(f"\nApp: {APP_NAME} v{APP_VERSION}")
        print(f"Port: {PORT}")
        print(f"Database: {DB_PATH}")
        print(f"Model: {OPENAI_MODEL}")
        print(f"Features: {sum(FEATURES.values())}/{len(FEATURES)} enabled")
