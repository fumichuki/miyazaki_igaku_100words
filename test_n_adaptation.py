"""
N対応テスト：required_points決定とpoints生成の検証
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_service import determine_required_points
from models import SubmissionRequest, CorrectionResponse
import json

# テストケース
TEST_CASES = [
    {
        "name": "標準（4文）",
        "japanese": "日記をつけることの精神的・感情的効果はデータで実証されており、専門家も勧めている。15〜20分の記録を3〜5回続けることで、トラウマやストレスと折り合いをつけられた人もいる。がんなどの深刻な病気を抱える人には特に効果があり、専門的な療法として確立されている。これは誰にでも試す価値がある。",
        "english": "The mental and emotional effects of journaling are supported by data, and experts recommend it. Some people have been able to cope with trauma and stress by continuing to record for 15 to 20 minutes 3 to 5 times. It is particularly effective for people with serious illnesses such as cancer, and it has been established as a specialized therapy. This is worth trying for everyone.",
        "expected_required_points": 4
    },
    {
        "name": "標準（5文）",
        "japanese": "ある研究によると、右手を握りしめることで記憶が良くなり、左手を握りしめることで思い出す能力が高まることが明らかになった。参加者は4つのグループに分けられ、まず72語のリストを記憶し、その後で思い出すという課題を行った。1つのグループは右手を握りしめて記憶した。別のグループは左手を握りしめて記憶した。残り2つのグループは左右を入れ替えた。",
        "english": "According to a study, it has been found that clenching the right hand improves memory, and clenching the left hand enhances the ability to recall. Participants were divided into four groups and first memorized a list of 72 words and then recalled them. One group memorized by clenching their right hand. Another group memorized by clenching their left hand. The remaining two groups switched between left and right.",
        "expected_required_points": 5
    },
    {
        "name": "標準（3文）",
        "japanese": "主人公ジョンの仕事は、孤独死した人の身元を調査し、葬儀を執り行うことだった。彼の丁寧な仕事ぶりに胸を打たれた。主人公の表情が心地よかった。",
        "english": "John's job was to investigate the identity of people who died lonely deaths and to conduct their funerals. I was deeply moved by his meticulous work. The expression on John's face was comforting.",
        "expected_required_points": 3
    },
    {
        "name": "要約（5→3）",
        "japanese": "ある研究によると、右手を握りしめることで記憶が良くなり、左手を握りしめることで思い出す能力が高まることが明らかになった。参加者は4つのグループに分けられ、まず72語のリストを記憶し、その後で思い出すという課題を行った。1つのグループは右手を握りしめて記憶した。別のグループは左手を握りしめて記憶した。残り2つのグループは左右を入れ替えた。",
        "english": "A study found that clenching the right hand improves memory while the left hand enhances recall. Participants were divided into four groups, memorizing and recalling a 72-word list. The group that clenched their right hand during memorization and left hand during recall performed best.",
        "expected_required_points": 5  # 原文基準
    },
    {
        "name": "統合（2→1）",
        "japanese": "主人公の表情が心地よかった。荒んだ心を浄化してくれるような作品だった。",
        "english": "The expression on the protagonist's face was comforting, which seemed to purify my troubled heart.",
        "expected_required_points": 2  # 原文基準
    },
    {
        "name": "原文なし（3文）",
        "japanese": "",
        "english": "Knowledge accumulates over time. Experience shapes our understanding. Practice makes perfect.",
        "expected_required_points": 3  # 学生英文基準
    }
]

def test_required_points_determination():
    """required_points決定ロジックのテスト"""
    print("=" * 80)
    print("テスト1: required_points決定ロジック")
    print("=" * 80)
    
    for i, case in enumerate(TEST_CASES, 1):
        print(f"\nケース{i}: {case['name']}")
        print(f"原文: {case['japanese'][:100]}..." if len(case['japanese']) > 100 else f"原文: {case['japanese']}")
        print(f"英文: {case['english'][:100]}..." if len(case['english']) > 100 else f"英文: {case['english']}")
        
        actual = determine_required_points(case['japanese'], case['english'])
        expected = case['expected_required_points']
        
        status = "✅ PASS" if actual == expected else "❌ FAIL"
        print(f"期待値: {expected}, 実測値: {actual} ... {status}")

def test_fill_logic_simulation():
    """埋め合わせロジックのシミュレーション"""
    print("\n" + "=" * 80)
    print("テスト2: 埋め合わせロジックのシミュレーション")
    print("=" * 80)
    
    # シミュレーション: LLMが2個しか返さなかった場合
    required_points = 4
    current_points = [
        {"before": "test1", "after": "test1", "reason": "OK", "level": "✅"},
        {"before": "test2", "after": "test2", "reason": "OK", "level": "✅"}
    ]
    
    print(f"\nシナリオ: required_points={required_points}, 現在のpoints={len(current_points)}")
    print(f"不足数: {required_points - len(current_points)}")
    
    # 埋め合わせシミュレーション
    normalized_answer = "This is a test. Another sentence here. Third one. Fourth sentence."
    shortage = required_points - len(current_points)
    
    for i in range(shortage):
        filler_point = {
            "before": normalized_answer.split('.')[min(i, len(normalized_answer.split('.')) - 1)].strip(),
            "after": normalized_answer.split('.')[min(i, len(normalized_answer.split('.')) - 1)].strip(),
            "reason": f"解説: この表現は適切です。（項目{len(current_points) + i + 1}）",
            "level": "✅正しい表現"
        }
        current_points.append(filler_point)
        print(f"埋め合わせ {i+1}/{shortage}: {filler_point['before'][:50]}...")
    
    print(f"\n最終的なpoints数: {len(current_points)}")
    status = "✅ PASS" if len(current_points) == required_points else "❌ FAIL"
    print(f"required_points達成: {status}")

if __name__ == "__main__":
    print("\n🔬 N対応テストスイート 🔬\n")
    
    test_required_points_determination()
    test_fill_logic_simulation()
    
    print("\n" + "=" * 80)
    print("テスト完了")
    print("=" * 80)
