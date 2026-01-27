#!/bin/bash
# サーバー再起動スクリプト

echo "🔄 サーバーを再起動します..."

# すべてのPythonプロセスを強制終了
pkill -9 python 2>/dev/null
sleep 2

# ポート8001が空いているか確認
if lsof -i :8001 >/dev/null 2>&1; then
    echo "⚠️  ポート8001がまだ使用中です。プロセスを強制終了します..."
    lsof -ti :8001 | xargs kill -9 2>/dev/null
    sleep 2
fi

# サーバーを起動
cd /workspaces/miyazaki_igaku_100words
echo "🚀 サーバーを起動中..."
/usr/local/bin/python app.py > /tmp/flask.log 2>&1 &

sleep 3

# 起動確認
if lsof -i :8001 >/dev/null 2>&1; then
    echo "✅ サーバーが正常に起動しました！"
    echo "📍 アクセス: http://localhost:8001"
    echo ""
    echo "📋 ログ確認: tail -f /tmp/flask.log"
else
    echo "❌ サーバーの起動に失敗しました"
    echo "📋 エラーログ:"
    tail -20 /tmp/flask.log
    exit 1
fi
