# 不具合レポート：ピリオドなしの文が❌として表示される

## 報告日時
2026-01-31 02:20 JST

## 問題の概要
ユーザーがピリオドなしで英文を入力した場合、バックエンドでは✅正しい表現と判定されているが、ブラウザの画面では❌として表示される。

## 再現手順
1. 以下の4文をピリオドなしで入力：
   - `This dataset examines the extent of fatigue that participants experience in their daily lives`
   - `First, people from a wide age range, from their 20s to their 60s, were asked to self-report their weekly sleep duration and fatigue levels`
   - `in addition, when a group sleeping less than five hours was compared with a group sleeping eight hours or more, the former tended to report stronger fatigue than the latter`
   - `These findings suggest that adequate sleep duration may contribute to reducing fatigue`

2. 添削ボタンをクリック

3. 結果：全て❌として表示される（ユーザー報告）

## 期待される動作
全て✅正しい表現として表示される（ピリオドなし・文頭小文字は形式ミスなので無視）

## 実際の動作（バックエンド）
APIレスポンスでは**全て✅正しい表現**として返されている：

```json
{
  "sentence_no": 1,
  "level": "✅正しい表現",
  "original_before": "This dataset examines the extent of fatigue that participants...",
  "before": "This dataset examines the extent of fatigue that participants....",
  "after": "This dataset examines the extent of fatigue that participants...."
}
```

（全4文とも同様に✅）

## 実際の動作（フロントエンド）
ユーザーのブラウザでは❌として表示される：

```
❌ This dataset examines the extent of fatigue that participants experience in their daily lives
→
✅ This dataset examines the extent of fatigue that participants experience in their daily lives.
```

## 原因の推測

### 可能性1: ブラウザのキャッシュ（最も可能性が高い）
- フロントエンドのJavaScript（main.js）を最近修正した
- ユーザーのブラウザが古いJavaScriptをキャッシュしている
- 修正前のコードが実行されている

**確認方法**：
- ブラウザでハードリロード（Ctrl+Shift+R または Cmd+Shift+R）
- または、ブラウザのキャッシュをクリア

### 可能性2: フロントエンドのロジックに問題
- `static/main.js` Line 1115-1145 で表示を制御
- 修正したが、まだ問題が残っている可能性

**現在のコード**：
```javascript
if (levelText.includes('✅')) {
  // ✅の場合: original_beforeを表示
  const formattedText = escapeHtml(originalBeforeText).replace(/\n/g, '<br>');
  beforeAfter.innerHTML = `
    <span class="${beforeClass}">${beforeIcon} ${formattedText}</span>
  `;
} else {
  // ❌の場合: original_before → after を表示
  const formattedOriginalBefore = escapeHtml(originalBeforeText).replace(/\n/g, '<br>');
  const formattedAfter = escapeHtml(afterText).replace(/\n/g, '<br>');
  beforeAfter.innerHTML = `
    <span class="${beforeClass}">${beforeIcon} ${formattedOriginalBefore}</span>
    <span class="arrow">→</span>
    <span class="after">✅ ${formattedAfter}</span>
  `;
}
```

**問題の可能性**：
- `levelText`の取得方法に問題がある？
- `beforeIcon`や`beforeClass`の値が間違っている？

### 可能性3: バックエンドとフロントエンドの同期問題
- サーバーを再起動したが、ブラウザが古い接続を保持している
- WebSocketやlong-pollingを使っている場合、再接続が必要

## 修正履歴

### コミット1: 6ddf01e
**タイトル**: Fix: マルチセンテンスモードで改行を保持

### コミット2: 03ff320
**タイトル**: Fix: CorrectionPointモデルにoriginal_beforeフィールドを追加

### コミット3: 882fe7e
**タイトル**: Fix: バックエンドで正規化後の文字列を比較してlevelを判定
- `points_normalizer.py`で`full_before == final_after`なら✅に変更

### コミット4: 79d293d
**タイトル**: Feature: 正規化を網羅的に拡張
- 全角記号・引用符・ダッシュ対応

### コミット5: 1197040
**タイトル**: Fix: フロントエンドでバックエンドのlevel判定を信頼
- フロントエンドの独自`isSame`判定を削除
- `levelText.includes('✅')`でバックエンドを信頼

## デバッグ情報

### バックエンド（確認済み）
```bash
# APIレスポンス
curl -X POST http://localhost:8001/api/correct-multi ...
# 結果: 全て "level": "✅正しい表現"
```

### サーバーログ
```bash
tail -100 /workspaces/miyazaki_igaku_100words/server.log | grep "Normalized input matches"
# 結果: ログなし（LLMが最初から✅を返している）
```

### コード確認
- `points_normalizer.py` Line 404-413: A==B判定ロジック
- `static/main.js` Line 1124-1145: 表示ロジック

## 推奨される対処法

### ユーザーへの指示
1. **ブラウザのハードリロード**
   - Windows/Linux: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`

2. **ブラウザのキャッシュクリア**
   - Chrome: 設定 → プライバシーとセキュリティ → 閲覧履歴データの削除
   - Firefox: 設定 → プライバシーとセキュリティ → データを消去
   - Safari: 環境設定 → 詳細 → キャッシュを空にする

3. **それでも解決しない場合**
   - ブラウザの開発者コンソールを開く（F12）
   - Console タブで以下を確認：
     - エラーメッセージがないか
     - `Point X: isSame=false` のようなデバッグログがないか
   - Network タブで `/api/correct-multi` のレスポンスを確認
     - `level` フィールドが `✅正しい表現` になっているか

### 開発者向けデバッグ手順
1. **ブラウザコンソールで確認**
   ```javascript
   // main.jsのLine 1121付近のデバッグログを確認
   // levelText.includes('✅') がfalseになっている可能性
   ```

2. **HTMLソースを確認**
   ```bash
   # ブラウザで「ページのソースを表示」
   # <script src="/static/main.js?v=..."></script> のバージョンを確認
   # 古いバージョンが読み込まれていないか
   ```

3. **強制的にキャッシュを無効化**
   ```html
   <!-- app.py の templates/index.html に追加 -->
   <script src="/static/main.js?v={{ timestamp }}"></script>
   ```

## 環境情報
- **OS**: Debian GNU/Linux 13 (trixie)
- **Python**: 3.12
- **Flask**: デバッグモード有効
- **ブラウザ**: 不明（ユーザー環境）
- **サーバー**: http://localhost:8001

## 追加調査が必要な点
1. ユーザーのブラウザ種類とバージョン
2. ブラウザのコンソールログ
3. Network タブでのAPIレスポンス内容
4. HTMLソースのJavaScriptファイルのバージョン

## まとめ
- **バックエンド**: 正常動作（✅を返している）
- **フロントエンド**: 問題あり（❌と表示している）
- **最も可能性が高い原因**: ブラウザのキャッシュ
- **推奨対処**: ハードリロード（Ctrl+Shift+R）

---

## GPTへの質問案

```
以下の状況で、ピリオドなしの英文が❌として表示される問題を解決したいです：

【バックエンド】
- APIレスポンスでは全て "level": "✅正しい表現" として返されている
- normalize_user_input()でピリオドを自動補完
- normalize_points()で正規化後の文字列を比較してlevelを判定
- A（正規化後のユーザー入力）== B（LLMのafter）なら✅に変更

【フロントエンド】
- static/main.js で levelText.includes('✅') を判定して表示
- ✅なら original_before のみ表示
- ❌なら original_before → after を表示

【問題】
- ユーザーのブラウザでは❌として表示される
- APIレスポンスは✅を返しているのに、画面では❌

【コードスニペット】
```javascript
// static/main.js Line 1124-1145
if (levelText.includes('✅')) {
  // ✅の場合: original_beforeを表示
  beforeAfter.innerHTML = `<span class="${beforeClass}">${beforeIcon} ${formattedText}</span>`;
} else {
  // ❌の場合: original_before → after を表示
  beforeAfter.innerHTML = `<span class="${beforeClass}">${beforeIcon} ${formattedOriginalBefore}</span><span class="arrow">→</span><span class="after">✅ ${formattedAfter}</span>`;
}
```

【推測】
- ブラウザのキャッシュが原因？
- levelTextの取得方法に問題？
- beforeIcon/beforeClassの値が間違っている？

どこを調査すれば原因を特定できますか？
```
