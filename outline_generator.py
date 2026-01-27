"""
アウトライン生成モジュール - Phase 3
宮崎大学医学部英作文特訓システム

構造化された回答の骨組みを提供
"""
from typing import List, Dict
from models import OutlineSection, OutlineResponse, TargetWords


# ===== 構造タイプ定義 =====

def get_structure_type(unit_type: str, required_units: int) -> str:
    """ユニットタイプと数から構造タイプを決定"""
    return f"{required_units}-{unit_type}"


# ===== セクション生成 =====

def generate_introduction_section(theme: str, unit_type: str, required_units: int) -> OutlineSection:
    """導入部のセクション生成"""
    unit_labels = {
        "reasons": "reasons",
        "things": "things/points",
        "examples": "examples",
        "suggestions": "suggestions",
        "benefits": "benefits",
        "ways": "ways"
    }
    
    unit_label = unit_labels.get(unit_type, "points")
    
    return OutlineSection(
        label="Introduction",
        marker=None,
        purpose=f"State your opinion/position on '{theme}' and mention that you will provide {required_units} {unit_label}",
        suggested_sentences=2,
        key_points=[
            f"Clear statement of your position regarding '{theme}'",
            f"Brief mention that you will discuss {required_units} {unit_label}"
        ],
        example_phrases=[
            "I believe that...",
            "In my opinion...",
            "I think that...",
            f"There are {required_units} main {unit_label} for this.",
            f"I will discuss {required_units} important {unit_label}."
        ]
    )


def generate_body_section(
    unit_number: int,
    unit_type: str,
    theme: str
) -> OutlineSection:
    """本論セクション生成（First reason, Second suggestion等）"""
    markers = ["First", "Second", "Third", "Fourth", "Fifth"]
    marker = markers[unit_number - 1] if unit_number <= len(markers) else f"Point {unit_number}"
    
    unit_singular = {
        "reasons": "reason",
        "things": "thing",
        "examples": "example",
        "suggestions": "suggestion",
        "benefits": "benefit",
        "ways": "way"
    }.get(unit_type, "point")
    
    return OutlineSection(
        label=f"{marker} {unit_singular}",
        marker=marker,
        purpose=f"Explain your {marker.lower()} {unit_singular} with supporting details",
        suggested_sentences=3,
        key_points=[
            f"State the {unit_singular} clearly",
            "Provide explanation or evidence",
            "Connect to the theme if needed"
        ],
        example_phrases=[
            f"{marker}, ...",
            f"The {marker.lower()} {unit_singular} is...",
            "This is important because...",
            "For example, ...",
            "This shows that..."
        ]
    )


def generate_conclusion_section(theme: str, required_units: int, unit_type: str) -> OutlineSection:
    """結論部のセクション生成"""
    return OutlineSection(
        label="Conclusion",
        marker=None,
        purpose=f"Summarize your {required_units} {unit_type} and restate your position",
        suggested_sentences=2,
        key_points=[
            f"Briefly recap the {required_units} {unit_type} mentioned",
            "Reaffirm your position or provide final thought"
        ],
        example_phrases=[
            "In conclusion, ...",
            "For these reasons, ...",
            "Therefore, ...",
            "To sum up, ...",
            "These are why I believe..."
        ]
    )


def estimate_word_count(sections: List[OutlineSection]) -> int:
    """セクション構成から推定語数を計算"""
    # 各文を平均15語と仮定
    avg_words_per_sentence = 15
    total_sentences = sum(section.suggested_sentences for section in sections)
    return total_sentences * avg_words_per_sentence


def generate_writing_tips(unit_type: str, required_units: int) -> List[str]:
    """執筆のヒントを生成"""
    base_tips = [
        f"Use discourse markers (First, Second) to clearly separate your {required_units} {unit_type}",
        "Start each paragraph with a topic sentence",
        "Provide specific examples or evidence to support each point",
        "Keep your sentences clear and concise"
    ]
    
    if unit_type == "reasons":
        base_tips.append("Explain WHY each reason is important or valid")
    elif unit_type == "suggestions":
        base_tips.append("Make your suggestions specific and actionable")
    elif unit_type == "examples":
        base_tips.append("Ensure your examples are relevant and illustrative")
    
    return base_tips


# ===== メイン生成関数 =====

def generate_outline(
    theme: str,
    required_units: int = 2,
    unit_type: str = "reasons",
    target_words: TargetWords = None
) -> OutlineResponse:
    """
    アウトラインを生成
    
    Args:
        theme: テーマ
        required_units: 必要な単位数（デフォルト2）
        unit_type: 単位タイプ（reasons/things/suggestions等）
        target_words: 目標語数
    
    Returns:
        OutlineResponse: 生成されたアウトライン
    """
    if target_words is None:
        target_words = TargetWords(min=80, max=120)
    
    # セクション生成
    sections = []
    
    # 1. Introduction
    sections.append(generate_introduction_section(theme, unit_type, required_units))
    
    # 2. Body sections (First reason, Second reason, etc.)
    for i in range(1, required_units + 1):
        sections.append(generate_body_section(i, unit_type, theme))
    
    # 3. Conclusion
    sections.append(generate_conclusion_section(theme, required_units, unit_type))
    
    # 推定語数
    estimated_words = estimate_word_count(sections)
    
    # 構造タイプ
    structure_type = get_structure_type(unit_type, required_units)
    
    # 執筆のヒント
    tips = generate_writing_tips(unit_type, required_units)
    
    return OutlineResponse(
        theme=theme,
        structure_type=structure_type,
        total_sections=len(sections),
        estimated_words=estimated_words,
        sections=sections,
        tips=tips
    )
