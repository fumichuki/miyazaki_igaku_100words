#!/bin/bash
# サーバー状態確認スクリプト

echo "🔍 サーバー状態を確認中..."
echo ""

# プロセス確認
if ps aux | grep -v grep | grep "python app.py" >/dev/null 2>&1; then
    echo "✅ Pythonプロセス: 起動中"
    ps aux | grep -v grep | grep "python app.py" | head -1
else
    echo "❌ Pythonプロセス: 停止中"
fi

echo ""

# ポート確認
if lsof -i :8002 >/dev/null 2>&1; then
    echo "✅ ポート8002: 使用中"
    lsof -i :8002 | head -3
else
    echo "❌ ポート8002: 使用されていません"
fi

echo ""

# 最新ログ
echo "📋 最新ログ（最後の10行）:"
tail -10 /tmp/flask.log 2>/dev/null || echo "ログファイルが見つかりません"
