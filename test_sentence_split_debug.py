#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ユーザー報告の文分割不具合を再現するテスト
"""
from constraint_validator import normalize_punctuation
from points_normalizer import normalize_user_input, split_into_sentences

# ユーザーの入力（実際の入力）
user_input = """According to a recent survey.Japan is getting older, and the demand for nursing home are increasing very fast.As the number of elderly people increase, care service cannot keep up, and many facilities are full by people
so a lot of families cannot get in.this situation is a big problem for local communities,and the government must act fast.If there was more staff, the services will be enough."""

print("=" * 80)
print("【ステップ1】元の入力:")
print("=" * 80)
print(user_input)
print()

print("=" * 80)
print("【ステップ2】normalize_punctuation 後:")
print("=" * 80)
normalized_punct = normalize_punctuation(user_input)
print(normalized_punct)
print()

print("=" * 80)
print("【ステップ3】normalize_user_input 後:")
print("=" * 80)
normalized = normalize_user_input(normalized_punct)
print(normalized)
print()

print("=" * 80)
print("【ステップ4】split_into_sentences 後:")
print("=" * 80)
sentences = split_into_sentences(normalized)
for i, sent in enumerate(sentences, 1):
    print(f"{i}文目: {sent}")
print()

print("=" * 80)
print("【期待される文数】: 3文")
print(f"【実際の文数】: {len(sentences)}文")
print("=" * 80)

# 問題点の確認
print("\n【問題点の詳細分析】")
print("-" * 80)
print("1. ピリオドの後にスペースがない箇所:")
issues = [
    "survey.Japan",
    "fast.As", 
    "in.this"
]
for issue in issues:
    if issue in user_input:
        print(f"   ✗ {issue} が見つかりました")
    
print("\n2. 改行の途中で文が切れている:")
if "\n" in user_input:
    print("   ✗ 改行あり（改行前に文末記号なし）")
    print(f"   改行位置: '...full by people\\nso a lot...'")

print("\n3. 小文字で始まる文:")
lowercase_starts = []
for line in user_input.split("\n"):
    if line and line[0].islower():
        lowercase_starts.append(line[:30] + "...")
        
if lowercase_starts:
    print("   ✗ 小文字始まりあり:")
    for start in lowercase_starts:
        print(f"     - {start}")
