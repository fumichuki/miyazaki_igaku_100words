"""
英作文特訓システム - 宮崎大学医学部版（100字指定）
Flask API Server - GPT-4o搭載 + Pydantic Validation
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from pydantic import ValidationError
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# 内部モジュール
from models import (
    QuestionRequest, SubmissionRequest, QuestionResponse, CorrectionResponse,
    ValidationRequest, ValidationResponse, ConstraintChecks,
    OutlineRequest, OutlineResponse
)
from llm_service import generate_question, correct_answer
from database import (
    save_question, get_question, save_submission, 
    get_submission_history, get_statistics, get_excluded_themes,
    get_theme_statistics
)
from constraint_validator import validate_constraints
from outline_generator import generate_outline
import config

# ロギング設定
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)

# Flask初期化
app = Flask(__name__)
CORS(app, origins=config.CORS_ORIGINS)

# データディレクトリ（後方互換性のため残す）
DATA_DIR = config.DATA_DIR
DATA_DIR.mkdir(exist_ok=True)

logger.info(f"🚀 {config.APP_NAME} v{config.APP_VERSION} 起動: http://localhost:{config.PORT}")
logger.info(f"📊 データベース: {config.DB_PATH}")
logger.info(f"🎯 有効機能: {sum(config.FEATURES.values())}/{len(config.FEATURES)}")

# ===== APIエンドポイント =====

@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')


@app.route('/system-info')
def system_info():
    """システム説明ページ"""
    return render_template('system_info.html')


@app.route('/test')
def test():
    """テストページ"""
    return render_template('test_button.html')


@app.route('/api/question', methods=['POST'])
def api_generate_question():
    """
    問題を生成
    POST /api/question
    Body: {"difficulty": "intermediate", "excluded_themes": [...]}
    """
    try:
        # リクエストをバリデーション
        data = request.get_json() or {}
        question_request = QuestionRequest(**data)
        
        # 最近使用されたテーマを除外
        recent_themes = get_excluded_themes(max_recent=10)
        all_excluded = list(set(question_request.excluded_themes + recent_themes))
        
        # 問題を生成
        question = generate_question(
            difficulty=question_request.difficulty,
            excluded_themes=all_excluded
        )
        
        # データベースに保存
        question_id = save_question(question)
        
        # レスポンスを返す
        response_data = question.model_dump()
        response_data['question_id'] = question_id
        
        return jsonify(response_data), 200
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({'error': 'Invalid request', 'details': e.errors()}), 400
    
    except Exception as e:
        logger.error(f"Question generation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/correct', methods=['POST'])
def api_correct_answer():
    """
    英作文を添削
    POST /api/correct
    Body: {
        "question_id": "q_xxx",
        "japanese_sentences": [...],
        "user_answer": "...",
        "target_words": {"min": 60, "max": 160}
    }
    """
    try:
        # リクエストをバリデーション
        data = request.get_json()
        submission = SubmissionRequest(**data)
        
        # 添削を実行
        correction = correct_answer(submission)
        
        # デバッグ用：添削結果を完全にログ出力
        import json
        response_dict = correction.model_dump()
        logger.info(f"=== Full correction response ===")
        logger.info(f"Points count: {len(response_dict.get('points', []))}")
        for i, point in enumerate(response_dict.get('points', [])):
            logger.info(f"Point {i}: before='{point.get('before', '')[:30]}', level='{point.get('level', 'MISSING')}'")
        logger.info(f"Full JSON:\n{json.dumps(response_dict, ensure_ascii=False, indent=2)}")
        
        # データベースに保存
        submission_id = save_submission(
            question_id=submission.question_id,
            user_answer=submission.user_answer,
            correction=correction
        )
        
        # レスポンスを返す
        response_data = correction.model_dump()
        response_data['submission_id'] = submission_id
        
        return jsonify(response_data), 200
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({'error': 'Invalid request', 'details': e.errors()}), 400
    
    except Exception as e:
        logger.error(f"Correction error: {e}", exc_info=True)
        
        # エラーが発生した場合でも、ユーザーには基本的なフィードバックを返す
        try:
            # フォールバック応答を生成
            from llm_service import _generate_fallback_correction
            user_answer = data.get('user_answer', '')
            fallback_data = _generate_fallback_correction(
                user_answer,
                data.get('question_text', '')
            )
            
            # constraint_checks を追加
            word_count = len(user_answer.split())
            fallback_data['constraint_checks'] = {
                "word_count": word_count,
                "within_word_range": 100 <= word_count <= 120,
                "detected_units": 0,
                "required_units": 2,
                "has_required_units": False,
                "unit_detection_confidence": "low",
                "markers_found": [],
                "because_count": 0,
                "sentence_count": user_answer.count('.'),
                "notes": ["システムエラーにより制約チェックをスキップしました"],
                "suggestions": []
            }
            
            logger.info("Returning fallback correction response to user")
            return jsonify(fallback_data), 200
            
        except Exception as fallback_error:
            logger.error(f"Fallback generation also failed: {fallback_error}")
            return jsonify({
                'error': '申し訳ございません。一時的なエラーが発生しました。もう一度お試しください。',
                'technical_details': str(e)
            }), 500


@app.route('/api/model_answer', methods=['POST'])
def api_model_answer():
    """
    模範解答のみを生成（翻訳用）
    POST /api/model_answer
    Body: {"question_id": "q_xxx", "question_text": "..."（任意）}
    ※question_textが空の場合はDBから取得してjapanese_sentencesを使用
    """
    try:
        data = request.get_json()
        question_id = data.get('question_id')
        question_text = data.get('question_text', '')
        
        if not question_id:
            return jsonify({'error': 'question_id is required'}), 400
        
        # question_textが空の場合はDBから取得
        if not question_text:
            logger.info(f"question_text is empty, fetching from DB: {question_id}")
            question_data = get_question(question_id)
            if question_data:
                # 新形式（japanese_paragraphs）を優先、なければ旧形式（japanese_sentences）
                if question_data.get('japanese_paragraphs'):
                    question_text = "\n".join(question_data['japanese_paragraphs'])
                    logger.info(f"Retrieved japanese_paragraphs from DB: {question_text[:100]}...")
                elif question_data.get('japanese_sentences'):
                    question_text = "\n".join(question_data['japanese_sentences'])
                    logger.info(f"Retrieved japanese_sentences from DB: {question_text[:100]}...")
                else:
                    return jsonify({'error': 'question not found in DB'}), 404
            else:
                return jsonify({'error': 'question not found in DB'}), 404
        
        # 模範解答を生成（日本語原文から英訳）
        from llm_service import generate_model_answer_only
        result = generate_model_answer_only(question_text)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Model answer generation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def api_get_history():
    """
    提出履歴を取得
    GET /api/history?limit=50
    """
    try:
        limit = int(request.args.get('limit', 50))
        history = get_submission_history(limit=limit)
        return jsonify({'history': history}), 200
        
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/statistics', methods=['GET'])
def api_get_statistics():
    """
    統計情報を取得
    GET /api/statistics
    """
    try:
        stats = get_statistics()
        theme_stats = get_theme_statistics()
        
        return jsonify({
            'statistics': stats,
            'theme_statistics': theme_stats
        }), 200
        
    except Exception as e:
        logger.error(f"Statistics retrieval error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/validate-constraints', methods=['POST'])
def api_validate_constraints():
    """
    制約を検証（Phase 1: サーバーサイド決定的チェック）
    POST /api/validate-constraints
    Body: {
        "text": "検証対象のテキスト",
        "min_words": 60,
        "max_words": 160,
        "required_units": 2
    }
    """
    try:
        # リクエストをバリデーション
        data = request.get_json()
        validation_request = ValidationRequest(**data)
        
        # 制約を検証
        constraints_result = validate_constraints(
            text=validation_request.text,
            min_words=validation_request.min_words,
            max_words=validation_request.max_words,
            required_units=validation_request.required_units
        )
        
        # Pydanticモデルに変換
        constraints = ConstraintChecks(**constraints_result)
        
        # すべての制約を満たしているか判定
        all_met = constraints.within_word_range and constraints.has_required_units
        ready = all_met  # 追加条件があれば調整可能
        
        response = ValidationResponse(
            constraints=constraints,
            all_constraints_met=all_met,
            ready_to_submit=ready
        )
        
        return jsonify(response.model_dump()), 200
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({'error': 'Invalid request', 'details': e.errors()}), 400
    
    except Exception as e:
        logger.error(f"Constraint validation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/outline', methods=['POST'])
def api_generate_outline():
    """
    アウトラインを生成（Phase 3）
    POST /api/outline
    Body: {
        "theme": "テーマ",
        "required_units": 2,
        "unit_type": "reasons",
        "target_words": {"min": 60, "max": 160}
    }
    """
    try:
        # リクエストをバリデーション
        data = request.get_json() or {}
        outline_request = OutlineRequest(**data)
        
        # アウトラインを生成
        outline = generate_outline(
            theme=outline_request.theme,
            required_units=outline_request.required_units,
            unit_type=outline_request.unit_type,
            target_words=outline_request.target_words
        )
        
        logger.info(f"Outline generated: {outline.theme} ({outline.structure_type})")
        
        return jsonify(outline.model_dump()), 200
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({'error': 'Invalid request', 'details': e.errors()}), 400
    
    except Exception as e:
        logger.error(f"Outline generation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    return jsonify({
        'status': 'ok',
        'version': config.APP_VERSION,
        'features': config.FEATURES,
        'timestamp': datetime.now().isoformat()
    }), 200


if __name__ == '__main__':
    # 設定の検証
    config_errors = config.validate_config()
    if config_errors:
        logger.error("⚠️ 設定エラー:")
        for error in config_errors:
            logger.error(f"  - {error}")
    
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG_MODE)

