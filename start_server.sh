#!/bin/bash

# サーバー起動スクリプト
# ポート8001を確実にクリーンアップしてからFlaskを起動

PORT=8001
LOG_FILE="/tmp/flask.log"

echo "=== サーバー起動処理開始 ==="

# 1. ポートを使用している全プロセスを強制終了
echo "ポート${PORT}を使用しているプロセスを確認中..."
PIDS=$(lsof -ti:${PORT} 2>/dev/null)

if [ -n "$PIDS" ]; then
    echo "以下のプロセスを終了します: $PIDS"
    kill -9 $PIDS 2>/dev/null
    sleep 1
else
    echo "ポート${PORT}は使用されていません"
fi

# 2. app.pyを実行している残留プロセスも念のため終了
echo "残留Pythonプロセスを確認中..."
pkill -9 -f "python.*app.py" 2>/dev/null
sleep 1

# 3. ポートが解放されたか確認
if lsof -i:${PORT} > /dev/null 2>&1; then
    echo "❌ エラー: ポート${PORT}がまだ使用されています"
    lsof -i:${PORT}
    exit 1
fi

echo "✅ ポート${PORT}は解放されました"

# 4. ログファイルをクリア
> "$LOG_FILE"

# 5. Flaskサーバーを起動
echo "Flaskサーバーを起動中..."
cd /workspaces/kagoshima_100words
python app.py > "$LOG_FILE" 2>&1 &

# 6. 起動確認
sleep 3

if lsof -i:${PORT} > /dev/null 2>&1; then
    echo "✅ サーバーが正常に起動しました"
    echo "URL: http://localhost:${PORT}"
    tail -10 "$LOG_FILE" | grep -E "(起動|Running)" || tail -10 "$LOG_FILE"
else
    echo "❌ サーバーの起動に失敗しました"
    echo "=== ログ内容 ==="
    tail -20 "$LOG_FILE"
    exit 1
fi

echo "=== サーバー起動処理完了 ==="
