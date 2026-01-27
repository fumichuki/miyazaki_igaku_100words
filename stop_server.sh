#!/bin/bash

# サーバー停止スクリプト
# ポート8002を使用している全プロセスを確実に終了

PORT=8002

echo "=== サーバー停止処理開始 ==="

# 1. ポートを使用しているプロセスを確認
echo "ポート${PORT}を使用しているプロセスを確認中..."
PIDS=$(lsof -ti:${PORT} 2>/dev/null)

if [ -n "$PIDS" ]; then
    echo "以下のプロセスを終了します:"
    lsof -i:${PORT}
    kill -9 $PIDS 2>/dev/null
    sleep 1
    echo "✅ プロセスを終了しました"
else
    echo "ポート${PORT}は使用されていません"
fi

# 2. app.pyを実行している残留プロセスも終了
echo "残留Pythonプロセスを確認中..."
pkill -9 -f "python.*app.py" 2>/dev/null
sleep 1

# 3. 最終確認
if lsof -i:${PORT} > /dev/null 2>&1; then
    echo "⚠️ 警告: まだプロセスが残っています"
    lsof -i:${PORT}
else
    echo "✅ ポート${PORT}は完全に解放されました"
fi

echo "=== サーバー停止処理完了 ==="
