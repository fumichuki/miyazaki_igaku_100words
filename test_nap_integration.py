"""
昼寝の研究データで統合テスト
- p.m. で文数が増殖しないか
- 文番号が 1〜4 に収まるか
- 未提出が誤って出ないか
- on 2 p.m. のミスが検出されるか
"""
import json

# テストデータ
question_text = """参加者はまず、昼寝を30分取るグループと、昼寝をしないグループに分けられた。
実験は午後2時に開始され、昼寝を取ったグループはその後、記憶テストを受けた。
その結果、昼寝を取ったグループは昼寝をしなかったグループよりも、記憶テストで高い成績を収めた。
特に、短期記憶の向上が顕著に見られた。"""

user_answer = """The participants was first divided into a group that took a 30-minute nap and a group that did not take a nap.
The experiment began on 2 p.m., and the nap group then took a memory test afterwards.
As a result, the group that took a nap scored higher on the memory test than the group that didn't napped.
In particular, a marked improvement in short-term memory was observed."""

hints = "participant：参加者（名詞）\nnap：昼寝（名詞）\nmemory test：記憶テスト（名詞）\nresult：結果（名詞）\nshort-term memory：短期記憶（名詞）"

# APIにリクエスト
import requests

# 問題生成と添削を分離
# 1. まず問題を生成
url_question = "http://localhost:8001/api/question"
payload_question = {
    "excerpt_type": "P2_P3",
    "theme": "研究紹介"
}

# 2. ユーザー回答を添削
url_correct = "http://localhost:8001/api/correct"

# 日本語原文を配列に変換
japanese_sentences = [s.strip() for s in question_text.strip().split('\n') if s.strip()]

payload_correct = {
    "question_id": "test_nap_001",
    "japanese_sentences": japanese_sentences,
    "user_answer": user_answer,
    "target_words": {"min": 60, "max": 160}
}

print("=" * 80)
print("統合テスト: 昼寝の研究")
print("=" * 80)
print()

print("日本語原文:")
for i, line in enumerate(question_text.split('\n'), 1):
    print(f"  {i}. {line}")
print()

print("ユーザー英文:")
for i, line in enumerate(user_answer.split('\n'), 1):
    print(f"  {i}. {line}")
print()

try:
    # 添削APIを実行
    response = requests.post(url_correct, json=payload_correct, timeout=60)
    
    if response.status_code == 200:
        result = response.json()
        
        print("✅ APIレスポンス成功")
        print()
        
        # points を確認
        points = result.get('points', [])
        print(f"📊 points: {len(points)}個")
        print()
        
        # 検証項目
        errors = []
        
        # 1. 文番号が 1〜4 に収まるか
        sentence_nos = [p.get('sentence_no') for p in points if p.get('sentence_no')]
        if sentence_nos:
            max_no = max(sentence_nos)
            min_no = min(sentence_nos)
            if max_no > 4 or min_no < 1:
                errors.append(f"❌ 文番号が範囲外: {min_no}〜{max_no} （期待: 1〜4）")
            else:
                print(f"✅ 文番号が正常範囲: {min_no}〜{max_no}")
        
        # 2. 未提出が誤って出ないか
        for i, point in enumerate(points, 1):
            before = point.get('before', '')
            if '未提出' in before:
                errors.append(f"❌ ポイント{i}: 未提出が誤って検出: {before[:50]}")
        
        if not any('未提出' in p.get('before', '') for p in points):
            print("✅ 未提出の誤検出なし")
        
        # 3. p.m. の文が正しく処理されているか
        pm_found = False
        for i, point in enumerate(points, 1):
            before = point.get('before', '')
            if '2 p.m.' in before:
                pm_found = True
                # 文全体が含まれているか確認
                if 'experiment began' in before.lower():
                    print(f"✅ ポイント{i}: p.m. を含む文が全文で処理されている")
                else:
                    errors.append(f"❌ ポイント{i}: p.m. を含む文が断片化")
        
        if not pm_found:
            print("⚠️  p.m. を含むポイントが見つかりません（on 2 p.m. のミスが未検出の可能性）")
        
        # 4. on 2 p.m. のミスが検出されるか
        on_pm_detected = False
        for i, point in enumerate(points, 1):
            before = point.get('before', '')
            after = point.get('after', '')
            if 'on 2 p.m.' in before.lower() and 'at 2 p.m.' in after.lower():
                on_pm_detected = True
                print(f"✅ ポイント{i}: 'on 2 p.m.' → 'at 2 p.m.' のミスを検出")
        
        if not on_pm_detected:
            errors.append("⚠️  'on 2 p.m.' のミスが未検出（理想: 'at 2 p.m.' に修正）")
        
        # 5. 各ポイントの詳細表示
        print()
        print("=" * 80)
        print("ポイント詳細:")
        print("=" * 80)
        for i, point in enumerate(points, 1):
            print(f"\n【ポイント {i}】")
            print(f"  sentence_no: {point.get('sentence_no')}")
            print(f"  level: {point.get('level')}")
            print(f"  before: {point.get('before', '')[:80]}...")
            print(f"  after: {point.get('after', '')[:80]}...")
        
        # 結果サマリ
        print()
        print("=" * 80)
        if errors:
            print("❌ テスト失敗:")
            for error in errors:
                print(f"  {error}")
        else:
            print("🎉 すべての検証項目がPASSしました")
        print("=" * 80)
        
    else:
        print(f"❌ APIエラー: {response.status_code}")
        print(response.text)
        exit(1)

except Exception as e:
    print(f"❌ 例外発生: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
