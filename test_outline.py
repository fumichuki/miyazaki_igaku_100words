"""
Phase 3: アウトライン生成のテストケース
構造化された回答骨組みの検証
"""
from outline_generator import (
    generate_outline,
    generate_introduction_section,
    generate_body_section,
    generate_conclusion_section,
    estimate_word_count,
    customize_outline_for_archetype
)
from models import TargetWords


# ===== セクション生成テスト =====

def test_introduction_section():
    """導入部セクションの生成"""
    section = generate_introduction_section("Preventive Care", "reasons", 2)
    
    assert section.label == "Introduction"
    assert section.marker is None
    assert section.suggested_sentences == 2
    assert len(section.key_points) >= 2
    assert len(section.example_phrases) >= 3
    assert "2 reasons" in section.purpose.lower()
    
    print(f"✓ Introduction section generated")
    print(f"  Purpose: {section.purpose}")
    print(f"  Key points: {len(section.key_points)}")


def test_body_section_first():
    """本論セクション（First reason）の生成"""
    section = generate_body_section(1, "reasons", "Preventive Care")
    
    assert section.label == "First reason"
    assert section.marker == "First"
    assert section.suggested_sentences == 3
    assert len(section.key_points) >= 3
    assert "first reason" in section.purpose.lower()
    
    print(f"✓ First reason section generated")
    print(f"  Label: {section.label}")
    print(f"  Example phrases: {section.example_phrases[:2]}")


def test_body_section_second():
    """本論セクション（Second suggestion）の生成"""
    section = generate_body_section(2, "suggestions", "Animal Obesity")
    
    assert section.label == "Second suggestion"
    assert section.marker == "Second"
    assert section.suggested_sentences == 3
    assert "second suggestion" in section.purpose.lower()
    
    print(f"✓ Second suggestion section generated")


def test_conclusion_section():
    """結論部セクションの生成"""
    section = generate_conclusion_section("Preventive Care", 2, "reasons")
    
    assert section.label == "Conclusion"
    assert section.marker is None
    assert section.suggested_sentences == 2
    assert len(section.key_points) >= 2
    assert "2 reasons" in section.purpose.lower()
    
    print(f"✓ Conclusion section generated")
    print(f"  Purpose: {section.purpose}")


# ===== 完全アウトライン生成テスト =====

def test_generate_outline_two_reasons():
    """2つの理由を持つアウトライン生成"""
    outline = generate_outline(
        mode="veterinary",
        theme="Preventive Veterinary Care",
        required_units=2,
        unit_type="reasons",
        target_words=TargetWords(min=80, max=120)
    )
    
    # 基本検証
    assert outline.theme == "Preventive Veterinary Care"
    assert outline.structure_type == "2-reasons"
    assert outline.total_sections == 4  # Intro + 2 Body + Conclusion
    assert len(outline.sections) == 4
    
    # セクションラベルの検証
    assert outline.sections[0].label == "Introduction"
    assert outline.sections[1].label == "First reason"
    assert outline.sections[2].label == "Second reason"
    assert outline.sections[3].label == "Conclusion"
    
    # 推定語数
    assert 50 <= outline.estimated_words <= 200
    
    # ヒントの存在
    assert len(outline.tips) >= 4
    
    print(f"\n✓ Two-reasons outline generated:")
    print(f"  Theme: {outline.theme}")
    print(f"  Structure: {outline.structure_type}")
    print(f"  Total sections: {outline.total_sections}")
    print(f"  Estimated words: {outline.estimated_words}")
    print(f"  Tips: {len(outline.tips)} items")


def test_generate_outline_two_suggestions():
    """2つの提案を持つアウトライン生成"""
    outline = generate_outline(
        mode="veterinary",
        theme="Animal Obesity",
        required_units=2,
        unit_type="suggestions",
        target_words=TargetWords(min=100, max=150)
    )
    
    assert outline.structure_type == "2-suggestions"
    assert outline.sections[1].label == "First suggestion"
    assert outline.sections[2].label == "Second suggestion"
    assert "suggestion" in outline.sections[1].purpose.lower()
    
    print(f"\n✓ Two-suggestions outline generated:")
    print(f"  Structure: {outline.structure_type}")


def test_generate_outline_three_things():
    """3つのthingsを持つアウトライン生成"""
    outline = generate_outline(
        mode="general",
        theme="Study Methods",
        required_units=3,
        unit_type="things",
        target_words=TargetWords(min=100, max=150)
    )
    
    assert outline.structure_type == "3-things"
    assert outline.total_sections == 5  # Intro + 3 Body + Conclusion
    assert len(outline.sections) == 5
    
    # 3つのthingsセクション
    assert outline.sections[1].label == "First thing"
    assert outline.sections[2].label == "Second thing"
    assert outline.sections[3].label == "Third thing"
    
    print(f"\n✓ Three-things outline generated:")
    print(f"  Total sections: {outline.total_sections}")


# ===== アーキタイプカスタマイズテスト =====

def test_customize_for_archetype_a1():
    """A1アーキタイプ用カスタマイズ"""
    base_outline = generate_outline(
        mode="veterinary",
        theme="Pet Vaccination",
        required_units=2,
        unit_type="reasons"
    )
    
    # カスタマイズ前のヒント数
    original_tips_count = len(base_outline.tips)
    
    # A1用にカスタマイズ
    customized = customize_outline_for_archetype(base_outline, "A1")
    
    # ヒントが追加されているか
    assert len(customized.tips) > original_tips_count
    
    # A1固有のヒントが含まれているか
    tips_text = " ".join(customized.tips).lower()
    assert "yes" in tips_text or "no" in tips_text
    
    print(f"\n✓ A1 archetype customization:")
    print(f"  Original tips: {original_tips_count}")
    print(f"  Customized tips: {len(customized.tips)}")
    print(f"  Added: {customized.tips[-1]}")


def test_customize_for_archetype_c3():
    """C3アーキタイプ用カスタマイズ"""
    base_outline = generate_outline(
        mode="veterinary",
        theme="Zoonotic Diseases",
        required_units=2,
        unit_type="suggestions"
    )
    
    customized = customize_outline_for_archetype(base_outline, "C3")
    
    # C3固有のヒントが含まれているか
    tips_text = " ".join(customized.tips).lower()
    assert "problem" in tips_text
    
    print(f"\n✓ C3 archetype customization:")
    print(f"  Added tip: {customized.tips[-1]}")


# ===== 推定語数テスト =====

def test_estimate_word_count():
    """推定語数の計算"""
    outline = generate_outline(
        mode="veterinary",
        theme="Test Theme",
        required_units=2,
        unit_type="reasons"
    )
    
    # 4セクション: Intro(2文) + Body1(3文) + Body2(3文) + Conclusion(2文) = 10文
    # 10文 × 15語/文 = 150語
    expected_words = (2 + 3 + 3 + 2) * 15
    
    assert outline.estimated_words == expected_words
    
    print(f"\n✓ Word count estimation:")
    print(f"  Total sentences: {sum(s.suggested_sentences for s in outline.sections)}")
    print(f"  Estimated words: {outline.estimated_words}")


# ===== エッジケーステスト =====

def test_outline_with_four_benefits():
    """4つのbenefitsアウトライン"""
    outline = generate_outline(
        mode="general",
        theme="Exercise",
        required_units=4,
        unit_type="benefits"
    )
    
    assert outline.total_sections == 6  # Intro + 4 Body + Conclusion
    assert outline.structure_type == "4-benefits"
    
    print(f"\n✓ Four-benefits outline generated:")
    print(f"  Sections: {[s.label for s in outline.sections]}")


def test_outline_with_single_reason():
    """1つの理由アウトライン（エッジケース）"""
    outline = generate_outline(
        mode="general",
        theme="Test",
        required_units=1,
        unit_type="reasons"
    )
    
    assert outline.total_sections == 3  # Intro + 1 Body + Conclusion
    assert len(outline.sections) == 3
    
    print(f"\n✓ Single-reason outline generated")


# ===== 統合テスト =====

def test_full_workflow_veterinary():
    """獣医学部の完全ワークフロー"""
    print("\n=== Full Veterinary Workflow ===")
    
    # 1. アウトライン生成
    outline = generate_outline(
        mode="veterinary",
        theme="Antibiotic Use in Livestock",
        required_units=2,
        unit_type="reasons",
        target_words=TargetWords(min=100, max=120),
        question_text="Do you think farmers should reduce antibiotic use?",
        archetype_id="A1"
    )
    
    # 2. アーキタイプカスタマイズ
    outline = customize_outline_for_archetype(outline, "A1")
    
    # 3. 検証
    assert outline.total_sections == 4
    assert outline.structure_type == "2-reasons"
    assert len(outline.tips) >= 5  # Base + A1 specific
    
    # 4. 各セクションの詳細確認
    for i, section in enumerate(outline.sections):
        print(f"\n  Section {i+1}: {section.label}")
        print(f"    Purpose: {section.purpose[:60]}...")
        print(f"    Suggested sentences: {section.suggested_sentences}")
        print(f"    Key points: {len(section.key_points)}")
    
    print(f"\n✓ Full workflow test passed")


# ===== 実行 =====

if __name__ == "__main__":
    print("=" * 70)
    print("Phase 3: Outline Generation Tests")
    print("=" * 70)
    
    try:
        # セクション生成テスト
        print("\n1. Section Generation Tests")
        test_introduction_section()
        test_body_section_first()
        test_body_section_second()
        test_conclusion_section()
        
        # 完全アウトライン生成テスト
        print("\n2. Complete Outline Generation Tests")
        test_generate_outline_two_reasons()
        test_generate_outline_two_suggestions()
        test_generate_outline_three_things()
        
        # カスタマイズテスト
        print("\n3. Archetype Customization Tests")
        test_customize_for_archetype_a1()
        test_customize_for_archetype_c3()
        
        # 推定語数テスト
        print("\n4. Word Count Estimation Test")
        test_estimate_word_count()
        
        # エッジケース
        print("\n5. Edge Case Tests")
        test_outline_with_four_benefits()
        test_outline_with_single_reason()
        
        # 統合テスト
        print("\n6. Integration Test")
        test_full_workflow_veterinary()
        
        print("\n" + "=" * 70)
        print("✅ All Phase 3 tests passed!")
        print("=" * 70)
        print("\n📊 Summary:")
        print("   - Section generation: ✅")
        print("   - Complete outline generation: ✅")
        print("   - Archetype customization: ✅")
        print("   - Word count estimation: ✅")
        print("   - Edge cases: ✅")
        print("   - Full workflow: ✅")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise
