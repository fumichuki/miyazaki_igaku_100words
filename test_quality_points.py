#!/usr/bin/env python3
"""
品質テスト：kagoshima風reasonフォーマット検証

N対応だけでなく、reason の品質（語彙比較A/B + 【参考】 + 例文2つ）も検証する
"""

import re
import json


def validate_point_quality(point, student_answer):
    """
    1つのpointがkagoshima風の品質要件を満たしているか検証
    
    必須要素:
    1. before が学生英文に含まれる OR "(未提出：" で始まる
    2. reason に "／" (語彙比較A/B) が含まれる
    3. reason に "【参考】" が含まれる
    4. reason に "例：" が含まれる
    5. 例文が2つある（"／" で区切られている）
    6. 例文が学生の英文と完全一致していない（コピペ防止）
    """
    errors = []
    
    before = point.get('before', '').strip()
    after = point.get('after', '').strip()
    reason = point.get('reason', '')
    level = point.get('level', '')
    
    # 内容評価は品質チェック対象外
    if '内容評価' in level or before == '(全体評価)':
        return True, []
    
    # 1. before バリデーション
    if not before:
        errors.append("❌ before が空")
    elif not before.startswith("(未提出："):
        # 学生英文に含まれるかチェック（部分一致許可）
        if before not in student_answer and not any(before in s for s in student_answer.split('.')):
            errors.append(f"❌ before が学生英文に存在しない: {before[:50]}")
    
    # 2. 語彙比較A/B チェック
    if "／" not in reason and "/" not in reason:
        errors.append("❌ reason に語彙比較（A／B）が含まれていない")
    
    # 3. 【参考】チェック
    if "【参考】" not in reason:
        errors.append("❌ reason に【参考】セクションが含まれていない")
    
    # 4. 例文チェック
    if "例：" not in reason:
        errors.append("❌ reason に例文セクション（例：）が含まれていない")
    else:
        # 例文部分を抽出
        example_match = re.search(r'例：(.+)', reason, re.DOTALL)
        if example_match:
            example_text = example_match.group(1)
            
            # 5. 例文が2つあるかチェック（"／" で区切られている）
            if "／" not in example_text and "/" not in example_text:
                errors.append("❌ 例文が1つしかない（2つ必須）")
            
            # 6. 例文が学生の英文と完全一致していないかチェック
            # before が例文にそのまま含まれていたらNG
            if before and before in example_text:
                errors.append(f"❌ 例文が学生の英文と同一（コピペ）: {before[:50]}")
    
    return len(errors) == 0, errors


def test_case(name, question_text, user_answer, expected_required_points):
    """テストケース実行"""
    print(f"\n{'='*80}")
    print(f"テストケース: {name}")
    print(f"{'='*80}")
    
    from llm_service import determine_required_points
    
    # required_points 計算
    required_points = determine_required_points(question_text, user_answer)
    
    print(f"📌 日本語原文: {question_text[:100]}...")
    print(f"📌 学生英文: {user_answer[:100]}...")
    print(f"📊 required_points: {required_points} (期待値: {expected_required_points})")
    
    # アサーション
    assert required_points == expected_required_points, \
        f"❌ required_points mismatch: got {required_points}, expected {expected_required_points}"
    
    print(f"✅ required_points 検証: PASS")
    
    # ここではrequired_pointsの計算のみテスト
    # 実際のLLM呼び出しと品質検証は別途実施（LLMコスト考慮）
    return required_points


def test_point_quality_assertions():
    """品質assert のテスト（モックデータで検証）"""
    print(f"\n{'='*80}")
    print("品質assert テスト（モックデータ）")
    print(f"{'='*80}")
    
    student_answer = "A number of students submitted the form online. She is likely to arrive late."
    
    # 良い例（全ての要件を満たす）
    good_point = {
        "before": "A number of students submitted the form online.",
        "after": "A number of students submitted the form online.",
        "reason": """1文目: A number of students submitted the form online.
（多くの学生がその用紙をオンラインで提出した。）
a number of（名詞句：多くの～）／the number of（名詞句：～の数）で、a number of は「たくさん」という量、the number of は「数そのもの」という数量を表します。
【参考】a number of + 複数名詞（多くの～）／the number of + 複数名詞（～の数）
例：A number of people were absent. (多くの人が欠席した。)／The number of people was increasing. (人の数が増えていた。)""",
        "level": "✅ 正しい表現"
    }
    
    is_valid, errors = validate_point_quality(good_point, student_answer)
    print(f"\n【良い例】")
    print(f"before: {good_point['before'][:50]}...")
    if is_valid:
        print(f"✅ 品質検証: PASS")
    else:
        print(f"❌ 品質検証: FAIL")
        for error in errors:
            print(f"  {error}")
        raise AssertionError("Good point should pass quality check")
    
    # 悪い例1: 語彙比較なし
    bad_point1 = {
        "before": "She is likely to arrive late.",
        "after": "She is likely to arrive late.",
        "reason": "解説：この表現は適切です。例：She is likely to arrive late.",
        "level": "✅ 正しい表現"
    }
    
    is_valid, errors = validate_point_quality(bad_point1, student_answer)
    print(f"\n【悪い例1: 語彙比較なし】")
    print(f"before: {bad_point1['before'][:50]}...")
    if not is_valid:
        print(f"✅ 品質検証: 正しく FAIL を検出")
        for error in errors:
            print(f"  {error}")
    else:
        print(f"❌ 品質検証: FAILすべきなのにPASSした")
        raise AssertionError("Bad point1 should fail quality check")
    
    # 悪い例2: 例文が学生英文と同一
    bad_point2 = {
        "before": "She is likely to arrive late.",
        "after": "She is likely to arrive late.",
        "reason": """解説：likely（形容詞：～しそうだ）／possible（形容詞：あり得る）で違います。
【参考】be likely to do
例：She is likely to arrive late. (遅れそうだ。)／She is likely to arrive late. (遅れそうだ。)""",
        "level": "✅ 正しい表現"
    }
    
    is_valid, errors = validate_point_quality(bad_point2, student_answer)
    print(f"\n【悪い例2: 例文が学生英文と同一】")
    print(f"before: {bad_point2['before'][:50]}...")
    if not is_valid:
        print(f"✅ 品質検証: 正しく FAIL を検出")
        for error in errors:
            print(f"  {error}")
    else:
        print(f"❌ 品質検証: FAILすべきなのにPASSした")
        raise AssertionError("Bad point2 should fail quality check")
    
    # 悪い例3: 学生が提出していない英文を添削
    bad_point3 = {
        "before": "Research suggests that spaced learning is effective.",  # 学生英文に存在しない
        "after": "Research suggests that spaced learning is effective.",
        "reason": """解説：suggest／show で違います。
【参考】suggest that S+V
例：Research suggests effectiveness. (研究は効果を示唆している。)／Data show results. (データは結果を示している。)""",
        "level": "✅ 正しい表現"
    }
    
    is_valid, errors = validate_point_quality(bad_point3, student_answer)
    print(f"\n【悪い例3: 学生が提出していない英文】")
    print(f"before: {bad_point3['before'][:50]}...")
    if not is_valid:
        print(f"✅ 品質検証: 正しく FAIL を検出")
        for error in errors:
            print(f"  {error}")
    else:
        print(f"❌ 品質検証: FAILすべきなのにPASSした")
        raise AssertionError("Bad point3 should fail quality check")
    
    print(f"\n{'='*80}")
    print("✅ 品質assert テスト: 全てPASS")
    print(f"{'='*80}")


def main():
    """メインテスト実行"""
    print("🔬 品質テストスイート（N対応 + kagoshima風reason検証）🔬\n")
    
    # テストケース1: 標準（4文）
    test_case(
        "標準（4文）",
        "原文1。原文2。原文3。原文4。",
        "English 1. English 2. English 3. English 4.",
        4
    )
    
    # テストケース2: 標準（5文）
    test_case(
        "標準（5文）",
        "原文1。原文2。原文3。原文4。原文5。",
        "English 1. English 2. English 3. English 4. English 5.",
        5
    )
    
    # テストケース3: 要約（5→3）
    test_case(
        "要約（5→3）",
        "原文1。原文2。原文3。原文4。原文5。",
        "English 1. English 2. English 3.",
        5  # 原文基準で5
    )
    
    # テストケース4: 統合（2→1）
    test_case(
        "統合（2→1）",
        "原文1。原文2。",
        "English 1 which combines both.",
        2  # 原文基準で2
    )
    
    # テストケース5: 原文なし（3文）
    test_case(
        "原文なし（3文）",
        "",
        "English 1. English 2. English 3.",
        3  # 学生基準で3
    )
    
    # テストケース6: 標準（3文）
    test_case(
        "標準（3文）",
        "原文1。原文2。原文3。",
        "English 1. English 2. English 3.",
        3
    )
    
    # 品質assert テスト
    test_point_quality_assertions()
    
    print("\n" + "="*80)
    print("🎉 全テストケース PASS 🎉")
    print("="*80)
    print("\n【次のステップ】")
    print("1. サーバーを再起動: ./restart_server.sh")
    print("2. 実際の英文で動作確認")
    print("3. 各テストケース（3文/4文/5文/要約/統合）で項目数と品質を確認")
    print("4. reason が kagoshima風（語彙比較A/B + 【参考】 + 例文2つ）になっているか確認")


if __name__ == '__main__':
    main()
