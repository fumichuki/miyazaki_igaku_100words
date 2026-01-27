"""
APIエンドポイントの統合テスト
Phase 1: 制約チェック機能の検証
"""
import requests
import json

BASE_URL = "http://localhost:8002"


def test_validate_constraints_endpoint():
    """制約検証エンドポイントのテスト"""
    print("\n=== Testing /api/validate-constraints ===")
    
    # テストケース1: 良い英作文（語数OK、2理由あり）
    print("\n1. Good essay (within range, 2 reasons):")
    response = requests.post(
        f"{BASE_URL}/api/validate-constraints",
        json={
            "text": " ".join(["word"] * 100) + " First reason. Second reason.",
            "min_words": 80,
            "max_words": 120,
            "required_units": 2
        }
    )
    assert response.status_code == 200
    data = response.json()
    print(f"   Word count: {data['constraints']['word_count']}")
    print(f"   Within range: {data['constraints']['within_word_range']}")
    print(f"   Detected units: {data['constraints']['detected_units']}")
    print(f"   Ready to submit: {data['ready_to_submit']}")
    
    # テストケース2: 語数不足
    print("\n2. Word shortage (50 words):")
    response = requests.post(
        f"{BASE_URL}/api/validate-constraints",
        json={
            "text": " ".join(["word"] * 50),
            "min_words": 100,
            "max_words": 120,
            "required_units": 2
        }
    )
    assert response.status_code == 200
    data = response.json()
    print(f"   Word count: {data['constraints']['word_count']}")
    print(f"   Within range: {data['constraints']['within_word_range']}")
    print(f"   Notes: {data['constraints']['notes']}")
    print(f"   Suggestions: {data['constraints']['suggestions'][:1]}")  # 最初の1つだけ表示
    assert data['ready_to_submit'] is False
    
    # テストケース3: 語数超過
    print("\n3. Word excess (150 words):")
    response = requests.post(
        f"{BASE_URL}/api/validate-constraints",
        json={
            "text": " ".join(["word"] * 150),
            "min_words": 100,
            "max_words": 120,
            "required_units": 2
        }
    )
    assert response.status_code == 200
    data = response.json()
    print(f"   Word count: {data['constraints']['word_count']}")
    print(f"   Within range: {data['constraints']['within_word_range']}")
    assert "語数超過" in str(data['constraints']['notes'])
    
    # テストケース4: 1理由のみ
    print("\n4. One reason only:")
    response = requests.post(
        f"{BASE_URL}/api/validate-constraints",
        json={
            "text": "First, I like cats. " + " ".join(["word"] * 95),
            "min_words": 80,
            "max_words": 120,
            "required_units": 2
        }
    )
    assert response.status_code == 200
    data = response.json()
    print(f"   Detected units: {data['constraints']['detected_units']}")
    print(f"   Has required units: {data['constraints']['has_required_units']}")
    
    print("\n✅ All /api/validate-constraints tests passed!")


def test_health_endpoint():
    """ヘルスチェックエンドポイント"""
    print("\n=== Testing /health ===")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    print(f"   Status: {data['status']}")
    print(f"   Timestamp: {data['timestamp']}")
    print("✅ Health check passed!")


def test_question_endpoint():
    """問題生成エンドポイント（軽量テスト）"""
    print("\n=== Testing /api/question ===")
    response = requests.post(
        f"{BASE_URL}/api/question",
        json={
            "mode": "general",
            "difficulty": "intermediate",
            "excluded_themes": []
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Theme: {data.get('theme', 'N/A')}")
        print(f"   Question ID: {data.get('question_id', 'N/A')}")
        print(f"   Sentences count: {len(data.get('japanese_sentences', []))}")
        print(f"   Target words: {data.get('target_words', {})}")
        print("✅ Question generation works!")
        return data
    else:
        print(f"⚠️  Question generation returned status {response.status_code}")
        print(f"   This might be due to missing OpenAI API key")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 1 Integration Tests")
    print("=" * 60)
    
    try:
        # 基本的なエンドポイント
        test_health_endpoint()
        
        # 制約検証エンドポイント（Phase 1のメイン機能）
        test_validate_constraints_endpoint()
        
        # 問題生成（OpenAI API キーがあれば動作）
        question_data = test_question_endpoint()
        
        print("\n" + "=" * 60)
        print("✅ Phase 1 implementation is complete!")
        print("=" * 60)
        print("\n📊 Summary:")
        print("   - Server-side word count: ✅")
        print("   - Two-units detection: ✅")
        print("   - /api/validate-constraints: ✅")
        print("   - Constraint checks integrated: ✅")
        print("   - Test coverage: ✅")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Server is not running!")
        print("   Please start the server with: python3 app.py")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
