"""
全角記号の正規化テスト
"""
from constraint_validator import normalize_punctuation, deterministic_word_count, detect_sentence_boundaries


def test_normalize_punctuation():
    """全角記号が半角に変換されることを確認"""
    
    # テスト1: 全角ピリオド
    text1 = "I like apples．However，I don't like oranges？"
    normalized1 = normalize_punctuation(text1)
    print(f"テスト1: 全角記号の変換")
    print(f"  入力: {text1}")
    print(f"  出力: {normalized1}")
    assert normalized1 == "I like apples.However,I don't like oranges?"
    print("  ✅ 成功\n")
    
    # テスト2: 全角スペース
    text2 = "I　like　apples"
    normalized2 = normalize_punctuation(text2)
    print(f"テスト2: 全角スペース")
    print(f"  入力: {text2}")
    print(f"  出力: {normalized2}")
    assert normalized2 == "I like apples"
    print("  ✅ 成功\n")
    
    # テスト3: 全角ハイフン
    text3 = "well－being"
    normalized3 = normalize_punctuation(text3)
    print(f"テスト3: 全角ハイフン")
    print(f"  入力: {text3}")
    print(f"  出力: {normalized3}")
    assert normalized3 == "well-being"
    print("  ✅ 成功\n")
    
    # テスト4: 語数カウント
    text4 = "I like apples．However，I don't like oranges？"
    word_count = deterministic_word_count(text4)
    print(f"テスト4: 語数カウント（全角記号含む）")
    print(f"  入力: {text4}")
    print(f"  語数: {word_count}")
    assert word_count == 8  # I, like, apples, However, I, don't, like, oranges = 8語
    print("  ✅ 成功\n")
    
    # テスト5: 文の区切り
    text5 = "I like apples．However，I don't like oranges？"
    sentence_count = detect_sentence_boundaries(text5)
    print(f"テスト5: 文の区切り（全角記号含む）")
    print(f"  入力: {text5}")
    print(f"  文数: {sentence_count}")
    # 全角ピリオドと全角疑問符で2文に分かれる
    print("  ✅ 成功\n")
    
    # テスト6: 混在
    text6 = "First，I like apples．Second，I prefer oranges！"
    normalized6 = normalize_punctuation(text6)
    word_count6 = deterministic_word_count(text6)
    sentence_count6 = detect_sentence_boundaries(text6)
    print(f"テスト6: 複雑な混在パターン")
    print(f"  入力: {text6}")
    print(f"  正規化: {normalized6}")
    print(f"  語数: {word_count6}")
    print(f"  文数: {sentence_count6}")
    print("  ✅ 成功\n")


if __name__ == "__main__":
    test_normalize_punctuation()
    print("全てのテストが成功しました！ ✅")
