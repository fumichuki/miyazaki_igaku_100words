"""
Pydanticモデル定義 - 宮崎大学医学部英作文特訓システム
JSONスキーマの厳格な管理とバリデーション
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator, model_validator


# ===== ヒント =====
class Hint(BaseModel):
    """ヒント単語"""
    en: str = Field(..., min_length=1, description="英単語")
    ja: str = Field(..., min_length=1, description="日本語訳")
    pos: Optional[str] = Field(None, description="品詞")
    usage: Optional[str] = Field(None, description="用法（動詞のみ）")
    kana: Optional[str] = Field(None, description="ふりがな（互換性のため残す）")


# ===== 出題API =====
class TargetWords(BaseModel):
    """目標語数範囲（語数制約なしのため実質的に無効）"""
    min: int = Field(..., ge=0, le=9999, description="最小語数")
    max: int = Field(..., ge=0, le=9999, description="最大語数")
    
    @model_validator(mode='after')
    def check_min_max(self):
        if self.min > self.max:
            raise ValueError("min must be less than or equal to max")
        return self


class QuestionResponse(BaseModel):
    """出題APIのレスポンス"""
    theme: str = Field(..., min_length=1, description="テーマ")
    question_text: Optional[str] = Field(None, description="英語の問題文（大問５形式）")
    japanese_sentences: Optional[List[str]] = Field(default_factory=list, description="日本語文のリスト（旧形式）")
    hints: List[Hint] = Field(..., min_length=3, max_length=10, description="ヒント単語リスト")
    target_words: TargetWords = Field(..., description="目標語数")
    model_answer: Optional[str] = Field(None, description="模範解答")
    alternative_answer: Optional[str] = Field(None, description="別解")
    common_mistakes: Optional[List[str]] = Field(default_factory=list, description="よくあるミス")
    # Phase 2: Archetypeメタデータ（オプション）
    archetype_id: Optional[str] = Field(None, description="アーキタイプID（Phase 2）")
    topic_id: Optional[str] = Field(None, description="トピックID（Phase 2）")
    required_units: Optional[int] = Field(None, description="必要な単位数（Phase 2）")
    unit_type: Optional[str] = Field(None, description="単位のタイプ（Phase 2）")
    question_text_english: Optional[str] = Field(None, description="英語の問題文（Phase 2）")
    
    @field_validator('japanese_sentences')
    @classmethod
    def validate_sentences(cls, v):
        if v and not all(isinstance(s, str) and len(s) > 0 for s in v):
            raise ValueError("All japanese_sentences must be non-empty strings")
        return v


# ===== 添削API =====
class CorrectionPoint(BaseModel):
    """添削ポイント"""
    before: str = Field(..., min_length=1, description="修正前の表現")
    after: str = Field(..., min_length=1, description="修正後の表現")
    reason: str = Field(..., min_length=1, description="修正理由")
    level: Optional[str] = Field(None, description="レベル（内容評価、❌文法ミス、✅正しい表現、💡改善提案）")
    alt: Optional[str] = Field(None, description="別の表現（オプション）")


class Score(BaseModel):
    """採点詳細"""
    content: int = Field(..., ge=0, le=5, description="内容点（0-5点）")
    structure: int = Field(..., ge=0, le=5, description="構成点（0-5点）")
    vocabulary: int = Field(..., ge=0, le=5, description="語彙点（0-5点）")
    grammar: int = Field(..., ge=0, le=5, description="文法点（0-5点）")
    word_count_penalty: int = Field(..., ge=0, le=5, description="語数点（0-5点）")


class Comments(BaseModel):
    """採点コメント"""
    content: str = Field(..., min_length=1, description="内容点のコメント")
    structure: str = Field(..., min_length=1, description="構成点のコメント")
    vocabulary: str = Field(..., min_length=1, description="語彙点のコメント")
    grammar: str = Field(..., min_length=1, description="文法点のコメント")
    word_count_penalty: str = Field(..., min_length=1, description="語数点のコメント")


class CorrectionResponse(BaseModel):
    """添削APIのレスポンス"""
    original: str = Field(..., min_length=1, description="元の英文")
    corrected: str = Field(..., min_length=1, description="修正版英文")
    word_count: int = Field(..., ge=0, description="語数")
    score: Optional[Score] = Field(None, description="採点詳細（オプション）")
    total: Optional[int] = Field(None, ge=0, le=25, description="合計点（オプション）")
    comments: Optional[Comments] = Field(None, description="採点コメント（オプション）")
    points: List[CorrectionPoint] = Field(..., min_length=1, description="添削ポイント")
    constraint_checks: Optional['ConstraintChecks'] = Field(None, description="制約チェック結果（Phase 1追加）")
    model_answer: Optional[str] = Field(None, description="理想的な模範解答")
    model_answer_explanation: Optional[str] = Field(None, description="模範解答の解説")
    
    @field_validator('points')
    @classmethod
    def validate_points_count(cls, v, info):
        """語数に応じて必要な添削ポイント数を検証"""
        # word_countは別のフィールドなので、ここでは最小限のチェック
        if len(v) < 1:
            raise ValueError("At least 1 correction point is required")
        return v


# ===== 提出リクエスト =====
class SubmissionRequest(BaseModel):
    """添削依頼リクエスト"""
    question_id: str = Field(..., min_length=1, description="問題ID")
    japanese_sentences: Optional[List[str]] = Field(default_factory=list, description="日本語文（旧形式）")
    question_text: Optional[str] = Field(None, description="英語の問題文（大問５形式）")
    user_answer: str = Field(..., min_length=10, description="ユーザーの英作文")
    target_words: TargetWords = Field(..., description="目標語数")
    word_count: Optional[int] = Field(None, ge=0, description="フロントエンドで計算した語数")


# ===== 問題生成リクエスト =====
class QuestionRequest(BaseModel):
    """問題生成リクエスト"""
    difficulty: Optional[str] = Field("intermediate", description="難易度")
    excluded_themes: Optional[List[str]] = Field(default_factory=list, description="除外テーマ")


# ===== 制約検証レスポンス（Phase 1追加） =====
class ConstraintChecks(BaseModel):
    """制約チェック結果"""
    word_count: int = Field(..., ge=0, description="実際の語数")
    within_word_range: bool = Field(..., description="語数範囲内か")
    required_units: int = Field(..., ge=1, description="必要な理由/提案/例の数")
    detected_units: int = Field(..., ge=0, description="検出された単位数")
    has_required_units: bool = Field(..., description="必要な単位数を満たしているか")
    unit_detection_confidence: str = Field(..., description="単位検出の信頼度（high/medium/low）")
    markers_found: List[str] = Field(default_factory=list, description="検出されたディスコースマーカー")
    because_count: int = Field(..., ge=0, description="理由接続詞の数")
    sentence_count: int = Field(..., ge=0, description="文の数")
    notes: List[str] = Field(..., min_length=1, description="詳細メッセージ")
    suggestions: List[str] = Field(default_factory=list, description="改善提案")


class ValidationRequest(BaseModel):
    """制約検証リクエスト"""
    text: str = Field(..., min_length=1, description="検証対象のテキスト")
    min_words: int = Field(..., ge=10, le=200, description="最小語数")
    max_words: int = Field(..., ge=10, le=200, description="最大語数")
    required_units: int = Field(2, ge=1, le=5, description="必要な理由/提案/例の数")
    
    @model_validator(mode='after')
    def check_min_max(self):
        if self.min_words > self.max_words:
            raise ValueError("min_words must be less than or equal to max_words")
        return self


class ValidationResponse(BaseModel):
    """制約検証レスポンス"""
    constraints: ConstraintChecks = Field(..., description="制約チェック結果")
    all_constraints_met: bool = Field(..., description="すべての制約を満たしているか")
    ready_to_submit: bool = Field(..., description="提出可能か")


# ===== アウトライン支援（Phase 3追加） =====
class OutlineSection(BaseModel):
    """アウトライン1セクション"""
    label: str = Field(..., min_length=1, description="セクションラベル（Introduction, First reason, etc.）")
    marker: Optional[str] = Field(None, description="ディスコースマーカー（First, Second, etc.）")
    purpose: str = Field(..., min_length=1, description="このセクションの目的")
    suggested_sentences: int = Field(..., ge=1, le=10, description="推奨文数")
    key_points: List[str] = Field(..., min_length=1, description="含めるべきポイント")
    example_phrases: List[str] = Field(default_factory=list, description="使える表現例")


class OutlineRequest(BaseModel):
    """アウトライン生成リクエスト"""
    theme: str = Field(..., min_length=1, description="問題のテーマ")
    required_units: int = Field(2, ge=1, le=5, description="必要な単位数（理由・提案など）")
    unit_type: str = Field("reasons", description="単位のタイプ（reasons/things/suggestions）")
    target_words: TargetWords = Field(..., description="目標語数")


class OutlineResponse(BaseModel):
    """アウトライン生成レスポンス"""
    theme: str = Field(..., description="テーマ")
    structure_type: str = Field(..., description="構造タイプ（two-reasons/two-things/etc.）")
    total_sections: int = Field(..., ge=3, description="総セクション数")
    estimated_words: int = Field(..., ge=10, description="推定語数")
    sections: List[OutlineSection] = Field(..., min_length=3, description="アウトラインセクション")
    tips: List[str] = Field(default_factory=list, description="執筆のヒント")
