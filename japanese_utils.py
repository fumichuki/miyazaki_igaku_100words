"""
日本語文の分割処理
"""
import re
from typing import List


def split_japanese_sentences(text: str) -> List[str]:
    """
    日本語原文を文に分割する
    
    句点（。）、疑問符（？）、感嘆符（！）で文を分割
    
    Args:
        text: 日本語原文
        
    Returns:
        文のリスト
    """
    if not text or not text.strip():
        return []
    
    # 句点・疑問符・感嘆符で分割（記号も保持）
    parts = re.split(r'([。！？])', text)
    
    # テキスト + 記号を結合
    sentences = []
    i = 0
    while i < len(parts):
        if i + 1 < len(parts) and parts[i + 1] in '。！？':
            # テキスト + 記号
            sentence = parts[i] + parts[i + 1]
            if sentence.strip():
                sentences.append(sentence.strip())
            i += 2
        else:
            # 最後の部分（記号なし）
            if parts[i].strip():
                # 末尾に句点がない場合は追加
                sentence = parts[i].strip()
                if not sentence.endswith(('。', '！', '？')):
                    sentence += '。'
                sentences.append(sentence)
            i += 1
    
    return sentences


def extract_hints_from_japanese(text: str) -> List[str]:
    """
    日本語原文からヒント単語を抽出（将来の拡張用）
    
    Args:
        text: 日本語原文
        
    Returns:
        ヒント単語のリスト（現在は空リスト）
    """
    # TODO: 将来的にヒント単語を自動抽出する機能を実装
    return []
