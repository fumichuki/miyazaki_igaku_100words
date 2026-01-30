#!/usr/bin/env python3
"""
マルチ文入力UIのテスト：実際にAPIを呼び出して文の分割が正しいか確認
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_multi_sentence_correction():
    """3文の翻訳問題をテスト"""
    
    print("=" * 60)
    print("テスト：マルチ文入力の添削結果確認")
    print("=" * 60)
    
    # まず問題を生成
    print("\n1. 問題生成中...")
    question_response = requests.post(
        f"{BASE_URL}/api/question",
        json={"difficulty": "intermediate", "excluded_themes": []}
    )
    
    if question_response.status_code != 200:
        print(f"❌ 問題生成失敗: {question_response.status_code}")
        return False
    
    question_data = question_response.json()
    question_id = question_data["question_id"]
    
    # 日本語文を取得
    japanese_sentences = []
    if "japanese_paragraphs" in question_data and question_data["japanese_paragraphs"]:
        for para in question_data["japanese_paragraphs"]:
            sentences = [s.strip() + '。' for s in para.split('。') if s.strip()]
            japanese_sentences.extend(sentences)
    
    print(f"✅ 問題生成完了（ID: {question_id}）")
    print(f"   文数: {len(japanese_sentences)}")
    
    # テスト用の英文（意図的にピリオドなしを含める）
    user_sentences = [
        "the last scene of this movie gave the audience a deep feeling",  # ピリオドなし
        "The smile that the main character showed at the end was a symbol of his growth and change, and it stayed in many people's hearts",  # ピリオドなし
        "the movie shows that by telling about personal growth, it can be more than just an entertainment and can give us a lesson for life."
    ]
    
    print(f"\n2. 添削リクエスト送信中...")
    print(f"   入力文数: {len(user_sentences)}")
    for i, sent in enumerate(user_sentences, 1):
        print(f"   {i}文目: {sent[:50]}...")
    
    # 添削リクエスト
    correct_response = requests.post(
        f"{BASE_URL}/api/correct-multi",
        json={
            "question_id": question_id,
            "user_sentences": user_sentences,
            "japanese_sentences": japanese_sentences[:len(user_sentences)],
            "target_words": question_data.get("target_words", []),
            "word_count": sum(len(s.split()) for s in user_sentences)
        }
    )
    
    if correct_response.status_code != 200:
        print(f"❌ 添削失敗: {correct_response.status_code}")
        print(f"   エラー: {correct_response.text}")
        return False
    
    result = correct_response.json()
    
    print(f"\n✅ 添削完了")
    
    # 添削ポイントを確認
    print(f"\n3. 添削ポイント解析:")
    print(f"   ポイント数: {len(result['points'])}")
    
    # 各ポイントを表示
    for i, point in enumerate(result['points'], 1):
        print(f"\n   --- ポイント {i} ---")
        print(f"   レベル: {point['level']}")
        
        if point['before']:
            before_preview = point['before'][:80] + "..." if len(point['before']) > 80 else point['before']
            print(f"   修正前: {before_preview}")
        
        if point['after']:
            after_preview = point['after'][:80] + "..." if len(point['after']) > 80 else point['after']
            print(f"   修正後: {after_preview}")
    
    # 模範解答を確認
    if "model_answer_explanation" in result:
        explanation = result["model_answer_explanation"]
        lines = explanation.split('\n')
        
        print(f"\n4. 模範解答の構造確認:")
        print(f"   総行数: {len(lines)}")
        
        # 「N文目:」のパターンをカウント
        sentence_markers = [line for line in lines if line.strip().endswith('文目:')]
        print(f"   「N文目:」マーカー: {len(sentence_markers)}")
        
        # ポイント番号をカウント
        point_numbers = []
        for line in lines:
            if line.strip().isdigit():
                point_numbers.append(int(line.strip()))
        
        print(f"   ポイント番号: {point_numbers}")
        
        # 各ポイントが正しく認識されているか
        expected_points = list(range(1, len(user_sentences) + 1))
        if point_numbers == expected_points:
            print(f"   ✅ ポイント番号が正しい（{point_numbers}）")
        else:
            print(f"   ⚠️ ポイント番号が期待と異なる")
            print(f"      期待: {expected_points}")
            print(f"      実際: {point_numbers}")
    
    print("\n" + "=" * 60)
    print("✅ テスト完了")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    test_multi_sentence_correction()
