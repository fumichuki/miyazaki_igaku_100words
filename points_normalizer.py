"""
添削ポイントの正規化処理
- 断片を全文に拡張
- level を ❌ または ✅ に強制
- ✅ の場合は after=before に矯正
- sentence_no を付与
"""
import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


# 省略形リスト（ピリオドを含むが文末ではないもの）
_ABBREVIATIONS = [
    "a.m.", "p.m.", "e.g.", "i.e.", "etc.",
    "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.",
    "U.S.", "U.K.", "vs.", "vol.", "fig.",
    "Jan.", "Feb.", "Mar.", "Apr.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec.",
    "Mon.", "Tue.", "Wed.", "Thu.", "Fri.", "Sat.", "Sun."
]
_DOT_PLACEHOLDER = "<DOT>"


def _protect_abbreviations(text: str) -> str:
    """
    省略形のピリオドを一時的にプレースホルダーに置換して保護する
    
    文末の省略形（例: "U.S. It"）の場合、省略形内部のピリオドのみ保護し、
    文末のピリオドは保護しない
    
    Args:
        text: 元のテキスト
    
    Returns:
        保護されたテキスト
    """
    protected = text
    
    # 省略形を保護（ただし、文末判定のため特別な処理が必要）
    for abbr in _ABBREVIATIONS:
        # 大文字小文字を区別せずにマッチング
        # ただし、省略形の後にスペース+大文字が続く場合は文の区切りと見なす
        # 例: "U.S. It" の場合、"U.S." 全体ではなく "U.S" のみ保護
        pattern = re.compile(re.escape(abbr), re.IGNORECASE)
        
        # 省略形の後にスペース+大文字が続く場合は、最後のピリオド以外を保護
        # 例: "U.S." → "U<DOT>S."
        if abbr.endswith('.'):
            abbr_without_last_dot = abbr[:-1]  # "U.S." → "U.S"
            # "U.S." の後にスペース+大文字が続く場合のみ、最後のピリオドを残す
            protected = re.sub(
                re.escape(abbr) + r'(?=\s+[A-Z])',
                abbr_without_last_dot.replace(".", _DOT_PLACEHOLDER) + ".",
                protected,
                flags=re.IGNORECASE
            )
            # それ以外の場合は全体を保護
            protected = pattern.sub(
                lambda m: m.group(0).replace(".", _DOT_PLACEHOLDER),
                protected
            )
    
    # イニシャル形式（A.B.C.など）を保護
    protected = re.sub(r'\b([A-Z])\.(?=\s*[A-Z]\.)', r'\1' + _DOT_PLACEHOLDER, protected)
    
    # 小数（3.14など）を保護
    protected = re.sub(r'(\d)\.(\d)', r'\1' + _DOT_PLACEHOLDER + r'\2', protected)
    
    return protected


def _restore_abbreviations(text: str) -> str:
    """
    プレースホルダーをピリオドに戻す
    
    Args:
        text: 保護されたテキスト
    
    Returns:
        復元されたテキスト
    """
    return text.replace(_DOT_PLACEHOLDER, ".")


def normalize_user_input(text: str) -> str:
    """
    ユーザー入力を正規化する
    
    以下の修正を行う：
    - 全角スペースを半角スペースに変換
    - 改行を単一スペースに変換（句読点がない改行は文の途中として扱う）
    - ピリオド直後にスペースなく文字が続く場合、スペースを挿入（例: "word.In" → "word. In"）
    - 複数の連続スペースを1つに統一
    - 文末句読点の前の余分なスペースを削除
    - 文末にピリオドがない場合は追加
    - 各文の文頭を大文字化（自動整形）
    - 前後の余分な空白を削除
    
    注意: スペルミス・文法ミス・語彙ミスは修正しない（添削対象として残す）
    
    Args:
        text: ユーザーが入力した英文
    
    Returns:
        正規化された英文
    """
    if not text or not text.strip():
        return ""
    
    # 前後の空白を削除
    normalized = text.strip()
    
    # ステップ0a: 全角スペースを半角スペースに変換（最優先）
    normalized = normalized.replace('　', ' ')
    
    # ステップ0b: 改行を単一スペースに変換
    # 改行は文の区切りではなく、入力の途中と見なす（過剰分割を防ぐ）
    # 例: "...full by people\nso a lot..." → "...full by people so a lot..."
    normalized = re.sub(r'\n+', ' ', normalized)
    
    # ステップ1: ピリオド直後にスペースなく文字が続く場合、スペースを挿入
    # 省略形を保護する前に実行（p.m.In → p.m. In）
    # 注: 大文字・小文字両方に対応（survey.Japan → survey. Japan）
    normalized = re.sub(r'\.([A-Za-z])', r'. \1', normalized)
    
    # ステップ2: 疑問符・感嘆符の直後も同様
    normalized = re.sub(r'([?!])([A-Za-z])', r'\1 \2', normalized)
    
    # ステップ3: 複数の連続スペースを1つに統一
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # ステップ3.5: 文末句読点の前の余分なスペースを削除（例: "word ." → "word."）
    normalized = re.sub(r'\s+([.?!])$', r'\1', normalized)
    # 文中の句読点の前の余分なスペースも削除（例: "word . Next" → "word. Next"）
    normalized = re.sub(r'\s+([.?!])\s+', r'\1 ', normalized)
    
    # ステップ4: 文末にピリオド・疑問符・感嘆符がない場合は、ピリオドを追加
    if not normalized.endswith(('.', '?', '!')):
        normalized = normalized + '.'
    
    # ステップ5: 各文の文頭を大文字化（自動整形）
    # 最初の文字を大文字化
    if normalized:
        normalized = normalized[0].upper() + normalized[1:]
    
    # 句読点（. ! ?）の後に続く文字を大文字化
    # 例: "hello. the dog" → "hello. The dog"
    # 注: 省略形（e.g., i.e., p.m.）の直後は大文字化しない
    def capitalize_after_punctuation(match):
        punctuation = match.group(1)  # . or ! or ?
        space = match.group(2)        # スペース
        letter = match.group(3)       # 文字
        return punctuation + space + letter.upper()
    
    # パターン: [.!?] + スペース + 小文字
    # 例: ". the" → ". The"
    normalized = re.sub(r'([.!?])(\s+)([a-z])', capitalize_after_punctuation, normalized)
    
    return normalized.strip()


def split_into_sentences(text: str) -> List[str]:
    """
    英文をセンテンスに分割する（省略形に対応・厳格モード）
    
    p.m., a.m., e.g., U.S. などの省略形のピリオドで分割されないようにする
    
    分割条件（厳格化）:
    - ピリオド・疑問符・感嘆符 + スペース + 大文字/引用符/括弧のみ
    - 小文字始まりは前の文の継続と見なす（過剰分割を防ぐ）
    
    Args:
        text: 英文テキスト
    
    Returns:
        センテンスのリスト
    """
    if not text or not text.strip():
        return []
    
    # 改行は normalize_user_input() で既にスペースに変換済み
    # ここでは改行チェックをスキップ
    
    # ステップ1: 省略形のピリオドを保護
    protected = _protect_abbreviations(text.strip())
    
    # ステップ2: 文末候補のピリオドを検出（厳格化）
    # 条件: [.!?] + スペース1つ以上 + (大文字 or 引用符 or 括弧)
    # 小文字始まり（so, this, that など）は新しい文として扱わない
    parts = re.split(r'([.!?])\s+(?=[A-Z"\'\(])', protected)
    
    # ステップ3: 分割結果を文に再構成
    sentences = []
    i = 0
    while i < len(parts):
        if i + 1 < len(parts) and parts[i + 1] in '.!?':
            # テキスト + 句読点を結合
            sentence = parts[i] + parts[i + 1]
            # プレースホルダーを復元
            restored = _restore_abbreviations(sentence)
            # 重複ピリオドを削除（U.S.. → U.S.）
            restored = re.sub(r'\.\.+', '.', restored)
            sentences.append(restored)
            i += 2
        else:
            # 最後の部分（句読点なし）
            if parts[i].strip():
                restored = _restore_abbreviations(parts[i])
                sentences.append(restored)
            i += 1
    
    # 空の要素を削除し、両端の空白を削除
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def find_sentence_containing_fragment(fragment: str, sentences: List[str]) -> tuple:
    """
    断片を含むセンテンスを探す
    
    Args:
        fragment: 断片テキスト
        sentences: センテンスのリスト
    
    Returns:
        (sentence_index, sentence_text) または (None, None)
    """
    fragment_lower = fragment.lower().strip()
    
    for i, sentence in enumerate(sentences):
        if fragment_lower in sentence.lower():
            return (i, sentence)
    
    return (None, None)


def replace_fragment_in_sentence(sentence: str, before_fragment: str, after_fragment: str) -> str:
    """
    センテンス内の断片を置換する（1回のみ）
    
    Args:
        sentence: 元のセンテンス
        before_fragment: 置換前の断片
        after_fragment: 置換後の断片
    
    Returns:
        置換後のセンテンス
    """
    # 大文字小文字を区別せずに1回だけ置換
    pattern = re.compile(re.escape(before_fragment), re.IGNORECASE)
    result = pattern.sub(after_fragment, sentence, count=1)
    return result


def normalize_level(level: str, before: str, after: str) -> tuple:
    """
    level を ❌ または ✅ に正規化し、after を調整する
    
    ルール:
    - 💡 が含まれる → ✅ に変換し、after=before
    - level が無い → ✅ に変換し、after=before
    - ❌ のときは before≠after を許可
    - ✅ のときは after=before に矯正
    
    Args:
        level: 元の level
        before: 修正前の英文（全文）
        after: 修正後の英文（全文）
    
    Returns:
        (normalized_level, normalized_after)
    """
    # level が無い、または 💡 を含む場合
    if not level or '💡' in level:
        logger.info(f"Normalizing level: '{level}' → '✅ 正しい表現' (after=before)")
        return ('✅ 正しい表現', before)
    
    # ❌ の場合はそのまま
    if '❌' in level:
        logger.info(f"Level is ❌, keeping after: '{after[:50]}...'")
        return (level, after)
    
    # ✅ の場合は after=before に矯正
    if '✅' in level:
        if before != after:
            logger.info(f"Level is ✅ but after≠before. Setting after=before")
        return (level, before)
    
    # その他の場合はデフォルトで ✅
    logger.info(f"Unknown level '{level}', defaulting to '✅ 正しい表現' (after=before)")
    return ('✅ 正しい表現', before)


def normalize_points(
    points: List[Dict[str, Any]],
    normalized_answer: str,
    japanese_sentences: List[str],
    original_user_answer: str = None
) -> List[Dict[str, Any]]:
    """
    points を正規化する
    
    1. before/after を全文に拡張
    2. level を ❌ または ✅ に強制
    3. ✅ の場合は after=before に矯正
    4. sentence_no を付与
    5. sentence_no 昇順でソート
    6. original_before を追加（フロントエンド表示用）
    
    Args:
        points: LLMから返された points
        normalized_answer: 正規化された学生英文
        japanese_sentences: 日本語原文のセンテンスリスト
        original_user_answer: 正規化前のユーザー入力（オプション）
    
    Returns:
        正規化された points
    """
    logger.info(f"Starting points normalization: {len(points)} points")
    
    # 学生英文をセンテンスに分割（正規化後）
    student_sentences = split_into_sentences(normalized_answer)
    logger.info(f"Student answer split into {len(student_sentences)} sentences")
    
    # 元のユーザー入力もセンテンスに分割（正規化前）
    original_sentences = []
    if original_user_answer:
        # 正規化前の入力を同じロジックで分割（ピリオドなしでも対応）
        original_sentences = split_into_sentences(original_user_answer)
        logger.info(f"Original user input split into {len(original_sentences)} sentences")
    
    normalized_points = []
    
    for i, point in enumerate(points):
        try:
            original_before = point.get('before', '').strip()
            original_after = point.get('after', '').strip()
            original_level = point.get('level', '')
            
            logger.info(f"Processing point {i+1}: before='{original_before[:50]}...', level='{original_level}'")
            
            # before が空の場合はスキップ
            if not original_before:
                logger.warning(f"Point {i+1}: Empty before, skipping")
                continue
            
            # 🚨重要: LLMが返す before も正規化する（ピリオル補完など）
            normalized_before = normalize_user_input(original_before)
            logger.info(f"Point {i+1}: Normalized before='{normalized_before[:50]}...'")
            
            # 断片 → 全文に拡張（正規化後の before で検索）
            sentence_index, full_sentence = find_sentence_containing_fragment(normalized_before, student_sentences)
            
            if full_sentence is None:
                # 見つからない場合は警告してスキップ
                logger.warning(f"Point {i+1}: Fragment '{original_before[:50]}' not found in student answer, skipping")
                continue
            
            logger.info(f"Point {i+1}: Found in sentence {sentence_index + 1}: '{full_sentence[:50]}...'")
            
            # before を全文に置換（既に正規化済みの文字列を使用）
            full_before = full_sentence
            
            # after も正規化
            normalized_after = normalize_user_input(original_after)
            
            # after を全文に拡張（normalized_after が断片の場合、センテンス内で置換）
            if '❌' in original_level and normalized_before != normalized_after:
                # 修正が必要な場合：normalized_before を normalized_after に置換
                full_after = replace_fragment_in_sentence(full_sentence, normalized_before, normalized_after)
                # 修正後の文字列も正規化（念のため）
                full_after = normalize_user_input(full_after)
                logger.info(f"Point {i+1}: Replaced fragment in sentence: '{full_after[:50]}...'")
            else:
                # 修正不要な場合：after は before と同じ
                full_after = full_before
            
            # level を正規化し、必要なら after を調整
            normalized_level, final_after = normalize_level(original_level, full_before, full_after)
            
            # 元のユーザー入力（正規化前）を取得
            original_before_text = full_before  # デフォルトは正規化後
            if original_sentences and sentence_index < len(original_sentences):
                original_before_text = original_sentences[sentence_index]
                logger.info(f"Point {i+1}: Original user input: '{original_before_text[:50]}...'")
            
            # sentence_no を付与
            # japanese_sentence があればそれを元に特定、なければ sentence_index+1
            sentence_no = sentence_index + 1
            if point.get('japanese_sentence'):
                # 日本語原文から index を特定（完全一致）
                try:
                    jp_index = japanese_sentences.index(point['japanese_sentence'])
                    sentence_no = jp_index + 1
                    logger.info(f"Point {i+1}: Matched Japanese sentence, sentence_no={sentence_no}")
                except ValueError:
                    # 見つからない場合は sentence_index+1 を使用
                    logger.warning(f"Point {i+1}: Japanese sentence not found in original, using sentence_index+1")
            
            # 正規化結果を設定
            point['before'] = full_before
            point['after'] = final_after
            point['level'] = normalized_level
            point['sentence_no'] = sentence_no
            point['original_before'] = original_before_text  # 正規化前のユーザー入力
            
            normalized_points.append(point)
            logger.info(f"Point {i+1}: Normalized successfully (sentence_no={sentence_no})")
        
        except Exception as e:
            logger.error(f"Error normalizing point {i+1}: {e}")
            # エラーが発生した場合はスキップ
            continue
    
    # sentence_no 昇順でソート
    normalized_points.sort(key=lambda p: p.get('sentence_no', 9999))
    
    logger.info(f"Points normalization complete: {len(normalized_points)} points")
    return normalized_points
