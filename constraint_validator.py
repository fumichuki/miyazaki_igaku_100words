"""
制約検証モジュール - サーバーサイド決定的チェック
宮崎大学医学部英作文特訓システム

このモジュールはLLMに依存せず、確実に以下をチェックします：
1. 語数カウント（100-120語または80-120語）
2. 2つの理由/提案/例の検出（ヒューリスティック）
"""
import re
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


def normalize_punctuation(text: str) -> str:
    """
    全角記号を半角に正規化
    
    ユーザーが全角で入力する可能性のある記号を半角に変換します：
    - 全角ピリオド（．）→ 半角ピリオド（.）
    - 全角カンマ（，）→ 半角カンマ（,）
    - 全角疑問符（？）→ 半角疑問符（?）
    - 全角感嘆符（！）→ 半角感嘆符（!）
    - 全角コロン（：）→ 半角コロン（:）
    - 全角セミコロン（；）→ 半角セミコロン（;）
    - 全角引用符（""''）→ 半角引用符（""''）
    - 全角ハイフン（ー）→ 半角ハイフン（-）
    
    Args:
        text: 正規化対象のテキスト
        
    Returns:
        正規化されたテキスト
    """
    if not text:
        return text
    
    # 全角→半角の変換マップ
    replacements = {
        '。': '.',  # 日本語の句点
        '．': '.',  # 全角ピリオド
        '，': ',',
        '？': '?',
        '！': '!',
        '：': ':',
        '；': ';',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        '（': '(',  # 全角左括弧
        '）': ')',  # 全角右括弧
        '　': ' ',  # 全角スペース → 半角スペース
        'ー': '-',
        '－': '-',
        '—': '-',
        '–': '-',
    }
    
    result = text
    for full_width, half_width in replacements.items():
        result = result.replace(full_width, half_width)
    
    return result


def deterministic_word_count(text: str) -> int:
    """
    決定的な語数カウント（LLM非依存）
    
    ルール:
    - 英単語のみをカウント（日本語は除外）
    - 句読点を除外
    - アポストロフィを含む単語（don't, it's）は1語としてカウント
    - ハイフンでつながった単語（well-being）は1語としてカウント
    - 全角記号は自動的に半角に変換されます
    
    Args:
        text: カウント対象のテキスト
        
    Returns:
        語数（整数）
    """
    if not text or not text.strip():
        return 0
    
    # 全角記号を半角に正規化
    text = normalize_punctuation(text)
    
    # 英単語パターン（アポストロフィとハイフンを含む）
    # \b[\w']+\b はアポストロフィを含む単語にマッチ
    # ハイフンでつながった単語は1語としてカウント
    tokens = re.findall(r"\b[\w'-]+\b", text, re.UNICODE)
    
    # 英語の単語のみをフィルタ（少なくとも1文字の英字を含む）
    english_words = [token for token in tokens if re.search(r'[a-zA-Z]', token)]
    
    count = len(english_words)
    logger.debug(f"Word count: {count} (text length: {len(text)} chars)")
    
    return count


def detect_discourse_markers(text: str) -> List[Tuple[str, int]]:
    """
    ディスコースマーカー（論理展開の指標）を検出
    
    検出対象:
    - First/Firstly/First of all
    - Second/Secondly
    - Another/Also/Moreover/Furthermore/In addition
    - One reason is/Another reason is
    - For example/For instance (複数の例がある場合)
    
    Args:
        text: 検証対象のテキスト
        
    Returns:
        [(マーカー文字列, 位置), ...] のリスト
    """
    # 全角記号を半角に正規化
    text = normalize_punctuation(text)
    
    markers_patterns = [
        r'\bfirst(?:ly)?\b',
        r'\bfirst of all\b',
        r'\bsecond(?:ly)?\b',
        r'\bthird(?:ly)?\b',
        r'\banother\b',
        r'\balso\b',
        r'\bmoreover\b',
        r'\bfurthermore\b',
        r'\bin addition\b',
        r'\bone reason is\b',
        r'\banother reason is\b',
        r'\bfor example\b',
        r'\bfor instance\b',
        r'\badditionally\b',
        r'\bbesides\b',
    ]
    
    found_markers = []
    
    for pattern in markers_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            found_markers.append((match.group(), match.start()))
    
    # 位置順にソート
    found_markers.sort(key=lambda x: x[1])
    
    return found_markers


def detect_because_clauses(text: str) -> int:
    """
    理由を示す接続詞（because, since, as）の数をカウント
    
    Args:
        text: 検証対象のテキスト
        
    Returns:
        理由接続詞の数
    """
    # 全角記号を半角に正規化
    text = normalize_punctuation(text)
    
    patterns = [
        r'\bbecause\b',
        r'\bsince\b',
        r'\bas\b(?!\s+(?:well|usual))',  # "as well", "as usual"を除外
    ]
    
    count = 0
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        count += len(matches)
    
    return count


def detect_sentence_boundaries(text: str) -> int:
    """
    文の数をカウント（ピリオド、感嘆符、疑問符で区切る）
    
    全角記号（．！？）は自動的に半角（.!?）に変換されます。
    
    Args:
        text: 検証対象のテキスト
        
    Returns:
        文の数
    """
    # 全角記号を半角に正規化
    text = normalize_punctuation(text)
    
    # Mr., Dr., U.S. などの略語に注意
    # 簡易的な文末検出
    sentences = re.split(r'[.!?]+\s+', text.strip())
    # 最後の文（ピリオドの後にスペースがない場合）を含める
    sentences = [s for s in sentences if s.strip()]
    
    return len(sentences)


def detect_two_units(text: str) -> Dict[str, Any]:
    """
    2つの理由/提案/例の存在を検出（ヒューリスティック）
    
    検出方法:
    1. ディスコースマーカー（First, Second, Another等）
    2. 理由を示す接続詞（because, since）の複数回使用
    3. 文の数（4文以上あれば2理由の可能性が高い）
    
    Args:
        text: 検証対象のテキスト
        
    Returns:
        {
            "detected_units": 検出された単位数（0-2）,
            "has_two_units": 2単位以上か,
            "markers_found": 検出されたマーカーのリスト,
            "because_count": 理由接続詞の数,
            "sentence_count": 文の数,
            "confidence": 信頼度（"high", "medium", "low"）,
            "suggestions": 改善提案のリスト
        }
    """
    markers = detect_discourse_markers(text)
    because_count = detect_because_clauses(text)
    sentence_count = detect_sentence_boundaries(text)
    
    detected_units = 0
    confidence = "low"
    suggestions = []
    
    # マーカーベースの検出
    # First/Second のペアがあれば確実に2単位
    markers_text = [m[0].lower() for m in markers]
    has_first = any('first' in m for m in markers_text)
    has_second = any('second' in m for m in markers_text)
    
    if has_first and has_second:
        detected_units = 2
        confidence = "high"
    elif has_first or has_second:
        detected_units = 1
        confidence = "medium"
        suggestions.append("片方のマーカー（First/Second）しか検出されませんでした。もう一方も明示すると明確になります。")
    
    # Another, Also等の追加マーカーをカウント
    additional_markers = [m for m in markers_text if m in ['another', 'also', 'moreover', 'furthermore', 'in addition', 'additionally']]
    
    if detected_units == 0 and len(additional_markers) >= 1:
        detected_units = 1
        confidence = "medium"
        if len(additional_markers) >= 2:
            detected_units = 2
            confidence = "medium"
    
    # 理由接続詞（because等）が2回以上あれば2理由の可能性
    if detected_units == 0 and because_count >= 2:
        detected_units = 2
        confidence = "medium"
        suggestions.append("理由を示す接続詞（because等）が複数検出されました。First, Second などのマーカーを使うとより明確になります。")
    
    # 文の数で推定（4文以上あれば2理由の可能性が高い）
    if detected_units == 0 and sentence_count >= 4:
        detected_units = 2
        confidence = "low"
        suggestions.append("4文以上ありますが、論理構造が明確ではありません。First, Second などのマーカーを使って理由を明示してください。")
    
    # 検出できない場合の提案
    if detected_units == 0:
        suggestions.append("2つの理由/提案/例が明確に区別できません。'First, ...' と 'Second, ...' のような構造を使ってください。")
    elif detected_units == 1:
        suggestions.append("1つの理由/提案のみが検出されました。もう1つ追加して、2つの理由を明確に示してください。")
    
    return {
        "detected_units": min(detected_units, 2),  # 最大2
        "has_two_units": detected_units >= 2,
        "markers_found": [m[0] for m in markers],
        "because_count": because_count,
        "sentence_count": sentence_count,
        "confidence": confidence,
        "suggestions": suggestions
    }


def validate_constraints(
    text: str,
    min_words: int,
    max_words: int,
    required_units: int = 2
) -> Dict[str, Any]:
    """
    すべての制約を検証（統合関数）
    
    Args:
        text: 検証対象のテキスト
        min_words: 最小語数
        max_words: 最大語数
        required_units: 必要な理由/提案/例の数（デフォルト: 2）
        
    Returns:
        {
            "word_count": 実際の語数,
            "within_word_range": 語数範囲内か,
            "required_units": 必要な単位数,
            "detected_units": 検出された単位数,
            "has_required_units": 必要な単位数を満たしているか,
            "unit_detection_confidence": 単位検出の信頼度,
            "notes": 詳細メッセージのリスト,
            "suggestions": 改善提案のリスト
        }
    """
    # 語数カウント
    word_count = deterministic_word_count(text)
    within_range = min_words <= word_count <= max_words
    
    # 2単位検出（翻訳問題ではrequired_units=0でスキップ）
    if required_units > 0:
        unit_detection = detect_two_units(text)
        detected_units = unit_detection["detected_units"]
        has_required = detected_units >= required_units
    else:
        # 翻訳問題: 単位検出をスキップ
        unit_detection = {
            "detected_units": 0,
            "confidence": "n/a",
            "markers_found": [],
            "because_count": 0,
            "sentence_count": 0,
            "suggestions": []
        }
        detected_units = 0
        has_required = True  # required_units=0なら常に満たす
    
    # メッセージ生成
    notes = []
    suggestions = []
    
    # 語数チェック
    if not within_range:
        if word_count < min_words:
            shortage = min_words - word_count
            notes.append(f"⚠️ 語数不足: {word_count}語（{shortage}語不足）")
            suggestions.append(f"あと{shortage}語以上追加してください（目標: {min_words}-{max_words}語）")
        else:
            excess = word_count - max_words
            notes.append(f"⚠️ 語数超過: {word_count}語（{excess}語超過）")
            suggestions.append(f"{excess}語以上削減してください（目標: {min_words}-{max_words}語）")
    else:
        notes.append(f"✅ 語数OK: {word_count}語（{min_words}-{max_words}語）")
    
    # 単位数チェック（required_units > 0の場合のみ）
    if required_units > 0:
        if not has_required:
            notes.append(f"⚠️ 理由/提案が不足: {detected_units}個検出（{required_units}個必要）")
            suggestions.extend(unit_detection["suggestions"])
        else:
            confidence_label = {
                "high": "明確",
                "medium": "やや明確",
                "low": "不明確"
            }.get(unit_detection["confidence"], "不明")
            notes.append(f"✅ 理由/提案OK: {detected_units}個検出（{confidence_label}）")
            
            # 信頼度が低い場合は改善提案を追加
            if unit_detection["confidence"] == "low":
                suggestions.append("論理構造をより明確にするため、'First, ...' と 'Second, ...' のようなマーカーの使用を推奨します。")
    
    return {
        "word_count": word_count,
        "within_word_range": within_range,
        "required_units": required_units,
        "detected_units": detected_units,
        "has_required_units": has_required,
        "unit_detection_confidence": unit_detection["confidence"],
        "markers_found": unit_detection["markers_found"],
        "because_count": unit_detection["because_count"],
        "sentence_count": unit_detection["sentence_count"],
        "notes": notes,
        "suggestions": suggestions
    }
