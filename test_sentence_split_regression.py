#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0修正の回帰テスト - 文分割の過剰を防ぐ

修正内容:
1. normalize_user_input(): 改行をスペースに変換（ピリオド追加しない）
2. split_into_sentences(): 大文字始まりのみ分割（小文字始まりは継続）
"""
from constraint_validator import normalize_punctuation
from points_normalizer import normalize_user_input, split_into_sentences


def test_case(name: str, input_text: str, expected_count: int, description: str = ""):
    """テストケースを実行"""
    print(f"\n{'='*80}")
    print(f"【テスト】{name}")
    if description:
        print(f"【説明】{description}")
    print(f"{'='*80}")
    print(f"入力: {input_text[:100]}...")
    
    # 正規化と分割
    normalized = normalize_user_input(normalize_punctuation(input_text))
    sentences = split_into_sentences(normalized)
    
    print(f"\n正規化後: {normalized[:150]}...")
    print(f"\n分割結果（{len(sentences)}文）:")
    for i, sent in enumerate(sentences, 1):
        print(f"  {i}. {sent[:80]}{'...' if len(sent) > 80 else ''}")
    
    # 判定
    result = "✅ PASS" if len(sentences) == expected_count else "❌ FAIL"
    print(f"\n結果: {result} (期待={expected_count}文, 実際={len(sentences)}文)")
    
    return len(sentences) == expected_count


def main():
    print("🔬 P0修正の回帰テスト")
    print("="*80)
    
    results = []
    
    # テストケース1: ピリオド直後にスペースなし
    results.append(test_case(
        "TC1: ピリオド直後にスペースなし",
        "I like apples.She likes oranges.",
        2,
        "survey.Japan のようなタイプミスを修正して分割"
    ))
    
    # テストケース2: 改行で文が途中で切れている
    results.append(test_case(
        "TC2: 改行で文が途中切れ",
        "I like apples\nbut she likes oranges.",
        1,
        "改行は文の区切りではなく、スペースに変換して結合"
    ))
    
    # テストケース3: 小文字始まりの文
    results.append(test_case(
        "TC3: 小文字始まり",
        "I like apples. so does she.",
        1,
        "小文字始まりは前の文の継続と見なす（過剰分割しない）"
    ))
    
    # テストケース4: BUG_REPORTの実例（最重要）
    # 注: ユーザーが原文にない4文目を追加しているため、実際は4文が正しい
    # 重要なのは「6文に過剰分割されない」こと
    bug_report_input = """According to a recent survey.Japan is getting older, and the demand for nursing home are increasing very fast.As the number of elderly people increase, care service cannot keep up, and many facilities are full by people
so a lot of families cannot get in.this situation is a big problem for local communities,and the government must act fast.If there was more staff, the services will be enough."""
    
    results.append(test_case(
        "TC4: BUG_REPORT実例（最重要）",
        bug_report_input,
        4,  # 実際は4文（原文3文 + ユーザー追加1文）
        "過剰分割（6文）を防ぎ、適切な文数（4文）に分割する"
    ))
    
    # テストケース5: 正常な3文（回帰チェック）
    results.append(test_case(
        "TC5: 正常な3文（回帰チェック）",
        "According to a recent survey, Japan is aging rapidly. As the elderly population grows, care services cannot keep up. This situation is a major challenge for local communities.",
        3,
        "既に正しく書かれた文は正しく分割される"
    ))
    
    # テストケース6: 大文字始まりは分割される
    results.append(test_case(
        "TC6: 大文字始まりは分割",
        "I like apples. She likes oranges. They like bananas.",
        3,
        "大文字始まりは新しい文として分割される"
    ))
    
    # テストケース7: 省略形（回帰チェック）
    results.append(test_case(
        "TC7: 省略形（p.m., U.S. など）",
        "The meeting is at 3 p.m. in the U.S. office.",
        1,
        "省略形のピリオドで分割されない"
    ))
    
    # 結果サマリー
    print("\n" + "="*80)
    print("📊 テスト結果サマリー")
    print("="*80)
    passed = sum(results)
    total = len(results)
    print(f"合格: {passed}/{total} ({100*passed//total}%)")
    
    if passed == total:
        print("\n✅ 全てのテストに合格しました！")
        return 0
    else:
        print(f"\n❌ {total - passed}件のテストが失敗しました")
        return 1


if __name__ == "__main__":
    exit(main())
