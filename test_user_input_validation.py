"""
ユーザー入力の異常パターンテスト
想定される様々な入力エラーをテストし、システムが適切に処理できるか確認
"""
from points_normalizer import normalize_user_input, split_into_sentences
from constraint_validator import normalize_punctuation


def print_test_result(test_name, input_text, output_text, expected_behavior):
    """テスト結果を見やすく表示"""
    print("=" * 80)
    print(f"【{test_name}】")
    print("=" * 80)
    print(f"入力:     {repr(input_text)}")
    print(f"出力:     {repr(output_text)}")
    print(f"期待動作: {expected_behavior}")
    print()


def test_full_width_characters():
    """全角文字のテスト"""
    print("\n" + "🔍" * 40)
    print("テストカテゴリ 1: 全角文字の処理")
    print("🔍" * 40 + "\n")
    
    # Test 1-1: 全角ピリオド
    input1 = "This is a test。Another sentence。"
    normalized1 = normalize_punctuation(input1)
    print_test_result(
        "1-1: 全角ピリオド",
        input1,
        normalized1,
        "全角「。」→ 半角「.」に変換"
    )
    
    # Test 1-2: 全角カンマ
    input2 = "First，second，third．"
    normalized2 = normalize_punctuation(input2)
    print_test_result(
        "1-2: 全角カンマとピリオド",
        input2,
        normalized2,
        "全角「，」→「,」、全角「．」→「.」に変換"
    )
    
    # Test 1-3: 全角スペース
    input3 = "This　is　a　test."
    normalized3 = normalize_punctuation(input3)
    result3 = normalize_user_input(normalized3)
    print_test_result(
        "1-3: 全角スペース",
        input3,
        result3,
        "全角スペース→半角スペースに変換"
    )
    
    # Test 1-4: 全角括弧
    input4 = "The study（conducted in 2023）showed results."
    normalized4 = normalize_punctuation(input4)
    print_test_result(
        "1-4: 全角括弧",
        input4,
        normalized4,
        "全角「（）」→「()」に変換"
    )


def test_missing_spaces():
    """スペース不足のテスト"""
    print("\n" + "🔍" * 40)
    print("テストカテゴリ 2: スペース不足の処理")
    print("🔍" * 40 + "\n")
    
    # Test 2-1: ピリオド後のスペースなし
    input1 = "First sentence.Second sentence.Third sentence."
    result1 = normalize_user_input(input1)
    print_test_result(
        "2-1: ピリオド直後にスペースなし",
        input1,
        result1,
        "ピリオドと大文字の間にスペースを挿入"
    )
    
    # Test 2-2: カンマ後のスペースなし
    input2 = "First,second,third."
    result2 = normalize_user_input(input2)
    print_test_result(
        "2-2: カンマ直後にスペースなし",
        input2,
        result2,
        "カンマ後のスペース挿入（必要に応じて）"
    )
    
    # Test 2-3: 実際のユーザー入力例（過去のエラー）
    input3 = "The project aims to reduce traffic jams.In particular, real-time data is analyzed."
    result3 = normalize_user_input(input3)
    print_test_result(
        "2-3: 実際のユーザー入力パターン",
        input3,
        result3,
        "'jams.In' → 'jams. In' に修正"
    )


def test_excessive_spaces():
    """余分なスペースのテスト"""
    print("\n" + "🔍" * 40)
    print("テストカテゴリ 3: 余分なスペースの処理")
    print("🔍" * 40 + "\n")
    
    # Test 3-1: 複数の連続スペース
    input1 = "This    is     a      test."
    result1 = normalize_user_input(input1)
    print_test_result(
        "3-1: 複数の連続スペース",
        input1,
        result1,
        "複数スペースを1つに統一"
    )
    
    # Test 3-2: 文頭・文末のスペース
    input2 = "   This is a test.   "
    result2 = normalize_user_input(input2)
    print_test_result(
        "3-2: 文頭・文末の余分なスペース",
        input2,
        result2,
        "前後のスペースを削除"
    )
    
    # Test 3-3: 改行とスペースの混在
    input3 = "This is a test.\n\n   Another sentence."
    result3 = normalize_user_input(input3)
    print_test_result(
        "3-3: 改行とスペースの混在",
        input3,
        result3,
        "改行を保持しつつ、余分なスペースを削除"
    )


def test_punctuation_errors():
    """句読点エラーのテスト"""
    print("\n" + "🔍" * 40)
    print("テストカテゴリ 4: 句読点エラーの処理")
    print("🔍" * 40 + "\n")
    
    # Test 4-1: 文末にピリオドなし
    input1 = "This is a test"
    result1 = normalize_user_input(input1)
    print_test_result(
        "4-1: 文末にピリオドなし",
        input1,
        result1,
        "文末にピリオドを自動追加"
    )
    
    # Test 4-2: カンマをピリオドの代わりに使用
    input2 = "This is the first sentence, This is the second sentence."
    result2 = normalize_user_input(input2)
    sentences = split_into_sentences(result2)
    print_test_result(
        "4-2: カンマをピリオル代わりに使用（文法エラー）",
        input2,
        f"{result2}\n文分割結果: {sentences}",
        "カンマは保持（文法エラーとして添削時に指摘）"
    )
    
    # Test 4-3: 複数のピリオド
    input3 = "This is a test... Another sentence."
    result3 = normalize_user_input(input3)
    sentences = split_into_sentences(result3)
    print_test_result(
        "4-3: 三点リーダー（...）",
        input3,
        f"{result3}\n文分割結果: {sentences}",
        "三点リーダーを保持、文分割は正しく実行"
    )
    
    # Test 4-4: 疑問符・感嘆符
    input4 = "Is this correct? Yes! It is."
    result4 = normalize_user_input(input4)
    sentences = split_into_sentences(result4)
    print_test_result(
        "4-4: 疑問符・感嘆符",
        input4,
        f"{result4}\n文分割結果: {sentences}",
        "? と ! で適切に文分割"
    )


def test_abbreviations():
    """略語のテスト"""
    print("\n" + "🔍" * 40)
    print("テストカテゴリ 5: 略語の処理")
    print("🔍" * 40 + "\n")
    
    # Test 5-1: p.m., a.m.
    input1 = "The meeting started at 2 p.m. and ended at 5 p.m."
    result1 = normalize_user_input(input1)
    sentences = split_into_sentences(result1)
    print_test_result(
        "5-1: 時間表記（p.m.）",
        input1,
        f"{result1}\n文数: {len(sentences)}文",
        "p.m. で文分割されない（1文として認識）"
    )
    
    # Test 5-2: U.S., U.K.
    input2 = "The U.S. government announced new policies. The U.K. followed."
    result2 = normalize_user_input(input2)
    sentences = split_into_sentences(result2)
    print_test_result(
        "5-2: 国名略語（U.S., U.K.）",
        input2,
        f"{result2}\n文数: {len(sentences)}文",
        "U.S. と U.K. で文分割されない（2文として認識）"
    )
    
    # Test 5-3: Dr., Mr., etc.
    input3 = "Dr. Smith met Mr. Johnson. They discussed the plan."
    result3 = normalize_user_input(input3)
    sentences = split_into_sentences(result3)
    print_test_result(
        "5-3: 敬称（Dr., Mr.）",
        input3,
        f"{result3}\n文数: {len(sentences)}文",
        "Dr. と Mr. で文分割されない（2文として認識）"
    )


def test_edge_cases():
    """エッジケースのテスト"""
    print("\n" + "🔍" * 40)
    print("テストカテゴリ 6: エッジケース")
    print("🔍" * 40 + "\n")
    
    # Test 6-1: 空文字列
    input1 = ""
    result1 = normalize_user_input(input1)
    print_test_result(
        "6-1: 空文字列",
        input1,
        result1,
        "空文字列を適切に処理（エラーなし）"
    )
    
    # Test 6-2: スペースのみ
    input2 = "     "
    result2 = normalize_user_input(input2)
    print_test_result(
        "6-2: スペースのみ",
        input2,
        result2,
        "スペースを削除して空文字列に"
    )
    
    # Test 6-3: 数字のみ
    input3 = "123 456 789"
    result3 = normalize_user_input(input3)
    print_test_result(
        "6-3: 数字のみ",
        input3,
        result3,
        "数字を保持、ピリオド追加"
    )
    
    # Test 6-4: 特殊文字
    input4 = "Test #1: @user said \"hello\" & goodbye."
    result4 = normalize_user_input(input4)
    print_test_result(
        "6-4: 特殊文字（#, @, &, \"\"）",
        input4,
        result4,
        "特殊文字を保持"
    )
    
    # Test 6-5: 非常に長い文
    input5 = "This is a very long sentence " * 20 + "with many repetitions."
    result5 = normalize_user_input(input5)
    print_test_result(
        "6-5: 非常に長い文（600文字超）",
        input5[:100] + "...",
        result5[:100] + "...",
        "長文を適切に処理"
    )


def test_real_world_scenarios():
    """実際のユーザー入力シナリオ"""
    print("\n" + "🔍" * 40)
    print("テストカテゴリ 7: 実際のユーザー入力シナリオ")
    print("🔍" * 40 + "\n")
    
    # Test 7-1: 全角と半角の混在
    input1 = "The project aims to reduce traffic jams。In particular，AI technology is used．"
    step1 = normalize_punctuation(input1)
    step2 = normalize_user_input(step1)
    sentences = split_into_sentences(step2)
    print_test_result(
        "7-1: 全角・半角混在 + スペース不足",
        input1,
        f"Step1（全角→半角）: {step1}\nStep2（正規化）: {step2}\n文数: {len(sentences)}文",
        "全角を半角に変換後、スペース挿入、正しく文分割"
    )
    
    # Test 7-2: コピペミスを想定
    input2 = "According to the study   ,participants were divided into groups.The results showed   significant differences."
    step1_2 = normalize_punctuation(input2)
    step2_2 = normalize_user_input(step1_2)
    sentences2 = split_into_sentences(step2_2)
    print_test_result(
        "7-2: コピペによる余分なスペース + スペース不足",
        input2,
        f"正規化後: {step2_2}\n文数: {len(sentences2)}文",
        "余分なスペース削除、ピリオド後にスペース挿入"
    )
    
    # Test 7-3: モバイル入力を想定（自動大文字化なし）
    input3 = "the experiment was conducted.participants were divided into groups.results were analyzed."
    step1_3 = normalize_punctuation(input3)
    step2_3 = normalize_user_input(step1_3)
    sentences3 = split_into_sentences(step2_3)
    print_test_result(
        "7-3: 小文字で始まる文（モバイル入力想定）",
        input3,
        f"正規化後: {step2_3}\n文数: {len(sentences3)}文",
        "スペース挿入、文分割は正しく実行（大文字化はしない）"
    )


def main():
    """全テストを実行"""
    print("\n" + "🚀" * 40)
    print("ユーザー入力バリデーション・正規化テスト開始")
    print("🚀" * 40 + "\n")
    
    try:
        test_full_width_characters()
        test_missing_spaces()
        test_excessive_spaces()
        test_punctuation_errors()
        test_abbreviations()
        test_edge_cases()
        test_real_world_scenarios()
        
        print("\n" + "✅" * 40)
        print("全テスト完了！")
        print("✅" * 40 + "\n")
        
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
