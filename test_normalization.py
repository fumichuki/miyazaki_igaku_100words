"""
ユーザー入力正規化のテスト
"""
from points_normalizer import normalize_user_input, split_into_sentences


def test_normalize_user_input():
    """normalize_user_input() のテスト"""
    print("=" * 60)
    print("Test 1: ピリオド直後にスペースなく大文字が続く")
    print("=" * 60)
    
    input1 = "As a result, we found...daytime.In particular, many people felt..."
    result1 = normalize_user_input(input1)
    print(f"Input:  {input1}")
    print(f"Output: {result1}")
    print(f"✅ Expected: スペースが挿入される ('daytime.In' → 'daytime. In')")
    print()
    
    print("=" * 60)
    print("Test 2: 省略形（p.m.）を含む文")
    print("=" * 60)
    
    input2 = "The experiment began at 2 p.m.In particular, the results were clear."
    result2 = normalize_user_input(input2)
    print(f"Input:  {input2}")
    print(f"Output: {result2}")
    print(f"✅ Expected: 'p.m.' は保護され、'p.m.In' → 'p.m. In'")
    print()
    
    print("=" * 60)
    print("Test 3: 複数スペースの統一")
    print("=" * 60)
    
    input3 = "This is   a    test."
    result3 = normalize_user_input(input3)
    print(f"Input:  {input3}")
    print(f"Output: {result3}")
    print(f"✅ Expected: 複数スペースが1つに統一")
    print()
    
    print("=" * 60)
    print("Test 4: 文末にピリオドがない場合")
    print("=" * 60)
    
    input4 = "This is a test"
    result4 = normalize_user_input(input4)
    print(f"Input:  {input4}")
    print(f"Output: {result4}")
    print(f"✅ Expected: 末尾にピリオドが追加される")
    print()


def test_split_into_sentences():
    """split_into_sentences() のテスト"""
    print("=" * 60)
    print("Test 5: スペースなしでも分割可能")
    print("=" * 60)
    
    input5 = "As a result, we found that cutting down on caffeine can improve the quality of sleep at night.In particular, many people felt that reducing caffeine intake made it easier to fall asleep."
    result5 = split_into_sentences(input5)
    print(f"Input:  {input5}")
    print(f"Output: {result5}")
    print(f"文数: {len(result5)}")
    print(f"✅ Expected: 2文に分割される")
    for i, sent in enumerate(result5, 1):
        print(f"  [{i}] {sent}")
    print()
    
    print("=" * 60)
    print("Test 6: 省略形（p.m.）を含む文の分割")
    print("=" * 60)
    
    input6 = "The experiment began at 2 p.m., and the nap group then took a memory test afterwards. As a result, the group that took a nap scored higher on the memory test."
    result6 = split_into_sentences(input6)
    print(f"Input:  {input6}")
    print(f"Output: {result6}")
    print(f"文数: {len(result6)}")
    print(f"✅ Expected: 2文に分割される（'p.m.' で分割されない）")
    for i, sent in enumerate(result6, 1):
        print(f"  [{i}] {sent}")
    print()
    
    print("=" * 60)
    print("Test 7: U.S. を含む文の分割")
    print("=" * 60)
    
    input7 = "We live in the U.S. It is big."
    result7 = split_into_sentences(input7)
    print(f"Input:  {input7}")
    print(f"Output: {result7}")
    print(f"文数: {len(result7)}")
    print(f"✅ Expected: 2文に分割される（'U.S.' で分割されない）")
    for i, sent in enumerate(result7, 1):
        print(f"  [{i}] {sent}")
    print()
    
    print("=" * 60)
    print("Test 8: 小数を含む文の分割")
    print("=" * 60)
    
    input8 = "The value is 3.14. The result is clear."
    result8 = split_into_sentences(input8)
    print(f"Input:  {input8}")
    print(f"Output: {result8}")
    print(f"文数: {len(result8)}")
    print(f"✅ Expected: 2文に分割される（'3.14' で分割されない）")
    for i, sent in enumerate(result8, 1):
        print(f"  [{i}] {sent}")
    print()


def test_real_case():
    """実際のユーザー入力をテスト"""
    print("=" * 60)
    print("Test 9: 実際のユーザー入力（問題ありの例）")
    print("=" * 60)
    
    input9 = "As a result, we found that cutting down on caffeine can improve the quality of sleep at night and keep concentration in the daytime.In particular, many people felt that reducing caffeine intake after the afternoon made it easier to fall asleep and made them wake up hardly in the morning."
    
    print("【処理前】")
    print(f"Input: {input9}")
    print()
    
    # ステップ1: 正規化
    normalized = normalize_user_input(input9)
    print("【ステップ1: 正規化後】")
    print(f"Normalized: {normalized}")
    print()
    
    # ステップ2: 分割
    sentences = split_into_sentences(normalized)
    print("【ステップ2: 分割後】")
    print(f"文数: {len(sentences)}")
    for i, sent in enumerate(sentences, 1):
        print(f"  [{i}] {sent}")
    print()
    print(f"✅ Expected: 2文に分割される")
    print()


if __name__ == "__main__":
    test_normalize_user_input()
    test_split_into_sentences()
    test_real_case()
    
    print("=" * 60)
    print("✅ 全てのテスト完了")
    print("=" * 60)
