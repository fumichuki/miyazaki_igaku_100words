document.addEventListener('DOMContentLoaded', function() {

const chat = document.getElementById("chat-container");
const input = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const wordCountEl = document.getElementById("word-count");

let currentQuestion = null;
let currentQuestionId = null;

// ページ読み込み時に初期画面を表示
showInitialScreen();

// 送信ボタン
sendBtn.addEventListener("click", () => {
  submitAnswer();
});

// Enterキーは改行として動作（送信はボタンのみ）
// キーボードショートカットでの送信は無効化（誤送信防止）

// 英語チェック関数（アルファベットが主体かどうか）
function isEnglishText(text) {
  // 空白を除いた文字数をカウント
  const noSpaces = text.replace(/\s/g, '');
  if (noSpaces.length === 0) return false;
  
  // アルファベットの文字数をカウント
  const alphabetCount = (text.match(/[a-zA-Z]/g) || []).length;
  
  // アルファベットが全体の50%以上であればOK
  return alphabetCount / noSpaces.length >= 0.5;
}

// 語数カウンター + 英語チェック
input.addEventListener("input", () => {
  let text = input.value.trim();
  
  // 全角記号を半角に自動正規化
  const originalText = text;
  text = text.replace(/　/g, ' ')   // 全角スペース → 半角スペース
             .replace(/ー/g, '-')   // 全角ハイフン → 半角ハイフン
             .replace(/－/g, '-')   // 全角マイナス → 半角ハイフン
             .replace(/—/g, '-')    // emダッシュ → 半角ハイフン
             .replace(/–/g, '-')    // enダッシュ → 半角ハイフン
             .replace(/！/g, '!')   // 全角感嘆符 → 半角感嘆符
             .replace(/？/g, '?')   // 全角疑問符 → 半角疑問符
             .replace(/．/g, '.')   // 全角ピリオド → 半角ピリオド
             .replace(/。/g, '.')   // 全角句点 → 半角ピリオド
             .replace(/，/g, ',')   // 全角カンマ → 半角カンマ
             .replace(/、/g, ',')   // 全角読点 → 半角カンマ
             .replace(/：/g, ':')   // 全角コロン → 半角コロン
             .replace(/；/g, ';')   // 全角セミコロン → 半角セミコロン
             .replace(/"/g, '"')    // 全角開き引用符 → 半角引用符
             .replace(/"/g, '"')    // 全角閉じ引用符 → 半角引用符
             .replace(/'/g, "'")    // 全角開きアポストロフィ → 半角アポストロフィ
             .replace(/'/g, "'")    // 全角閉じアポストロフィ → 半角アポストロフィ
             .replace(/（/g, '(')   // 全角括弧（開き） → 半角
             .replace(/）/g, ')')   // 全角括弧（閉じ） → 半角
             .replace(/［/g, '[')   // 全角角括弧（開き） → 半角
             .replace(/］/g, ']');  // 全角角括弧（閉じ） → 半角
  
  // 正規化が行われた場合、テキストエリアを更新
  if (text !== originalText) {
    const cursorPos = input.selectionStart;
    input.value = text;
    // カーソル位置を復元（可能な限り）
    input.setSelectionRange(cursorPos, cursorPos);
  }
  
  // バックエンドと同じ語数カウントロジック（句読点を除外）
  const words = text.match(/\b[\w'-]+\b/g) || [];
  const wordCount = words.filter(w => /[a-zA-Z]/.test(w)).length;
  
  // 英語チェック
  const isEnglish = isEnglishText(text);
  
  // 送信不可の理由を明確に表示
  if (!isEnglish && text.length > 0) {
    wordCountEl.textContent = `❌ 英語で入力してください（日本語は不可）`;
    wordCountEl.style.color = "#ff6b6b";
    wordCountEl.style.fontWeight = "bold";
    sendBtn.disabled = true;
    sendBtn.title = "英語で入力してください";
    return;
  }
  
  // 和文英訳スタイル：語数範囲チェック（10語以上、160語以下）
  if (wordCount > 0 && wordCount < 10) {
    wordCountEl.textContent = `最低10語以上必要です（現在: ${wordCount} words）`;
    wordCountEl.style.color = "#94a3b8";  // グレー
    wordCountEl.style.fontWeight = "normal";
    sendBtn.disabled = true;
    sendBtn.title = "10語以上入力してください";
    return;
  }
  
  if (wordCount > 160) {
    wordCountEl.textContent = `❌ 語数が多過ぎます。160語以内で提出可（現在: ${wordCount} words）`;
    wordCountEl.style.color = "#ff6b6b";  // 赤
    wordCountEl.style.fontWeight = "bold";
    sendBtn.disabled = true;
    sendBtn.title = "160語以内にしてください";
    return;
  }
  
  // 和文英訳スタイル：10-160語すべて送信可能（緑で統一）
  if (wordCount >= 10 && wordCount <= 160) {
    wordCountEl.textContent = `✅ ${wordCount} words（送信可能）`;
    wordCountEl.style.color = "#51cf66";  // 緑
    wordCountEl.style.fontWeight = "bold";
  } else if (wordCount === 0) {
    wordCountEl.textContent = `0 words`;
    wordCountEl.style.color = "";  // デフォルト
    wordCountEl.style.fontWeight = "normal";
  }
  
  sendBtn.disabled = false;
  sendBtn.title = "添削を受ける";
});

// メッセージを追加
function addMessage(content, type) {
  const div = document.createElement("div");
  div.className = `message ${type}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  
  if (typeof content === 'string') {
    bubble.innerHTML = content;
  } else {
    bubble.appendChild(content);
  }

  div.appendChild(bubble);

  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

// 初期画面を表示
function showInitialScreen() {
  const messageDiv = document.createElement("div");
  messageDiv.className = "message ai-message";
  
  const content = document.createElement("div");
  content.className = "message-content";
  
  const button = document.createElement("button");
  button.textContent = "問題を作成";
  button.style.cssText = `
    padding: 16px 48px;
    font-size: 18px;
    font-weight: 600;
    border: none;
    border-radius: 12px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    transition: all 0.3s;
    margin-top: 10px;
  `;
  
  button.addEventListener("mouseover", () => {
    button.style.transform = "translateY(-2px)";
    button.style.boxShadow = "0 6px 16px rgba(102, 126, 234, 0.5)";
  });
  
  button.addEventListener("mouseout", () => {
    button.style.transform = "translateY(0)";
    button.style.boxShadow = "0 4px 12px rgba(102, 126, 234, 0.4)";
  });
  
  button.addEventListener("click", () => {
    chat.innerHTML = "";
    fetchNewQuestion();
  });
  
  content.appendChild(button);
  messageDiv.appendChild(content);
  chat.appendChild(messageDiv);
}

// 新しい問題を取得
function fetchNewQuestion() {
  addMessage("📝 新しい問題を生成中...", "ai");
  
  fetch('/api/question', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      difficulty: "intermediate",
      excluded_themes: []
    })
  })
  .then(res => res.json())
  .then(data => {
    // ローディングメッセージを削除
    chat.lastChild.remove();
    
    if (data.error) {
      let errorMsg = `❌ エラー: ${data.error}`;
      if (data.details) {
        console.error('Validation details:', data.details);
        errorMsg += '<br>詳細はブラウザコンソールを確認してください';
      }
      addMessage(errorMsg, "ai");
      return;
    }
    
    currentQuestion = data;
    currentQuestionId = data.question_id;
    
    // 問題を表示
    displayQuestion(data);
  })
  .catch(err => {
    chat.lastChild.remove();
    addMessage(`❌ エラー: ${err.message}`, "ai");
  });
}

// 問題を表示
function displayQuestion(data) {
  const container = document.createElement("div");
  container.className = "question-container";
  
  // 問題文（英語）
  if (data.question_text) {
    // テーマ
    const theme = document.createElement("div");
    theme.className = "question-theme";
    theme.textContent = `📌 テーマ: ${data.theme}`;
    container.appendChild(theme);
    const questionText = document.createElement("div");
    questionText.className = "question-text";
    questionText.textContent = data.question_text;
    container.appendChild(questionText);
    
    // 語数指示
    const wordCountInfo = document.createElement("div");
    wordCountInfo.className = "word-count-info-display";
    wordCountInfo.textContent = "📝 100-120語の英語で答えてください";
    container.appendChild(wordCountInfo);
  } else if (data.japanese_paragraphs && data.japanese_paragraphs.length > 0) {
    // 翻訳形式（段落→一文一文箇条書き）の場合
    const theme = data.theme || "学術";
    
    // テーマヘッダー
    const themeHeader = document.createElement("div");
    themeHeader.className = "theme-header-question";
    themeHeader.textContent = `📌 テーマ: ${theme}　　下記を英訳せよ`;
    container.appendChild(themeHeader);
    
    // 抜粋タイプの表示を追加
    if (data.excerpt_type) {
      const excerptInfo = document.createElement("div");
      excerptInfo.className = "excerpt-type-info";
      
      const excerptLabels = {
        'P1_ONLY': '（抜粋：段落①のみ）',
        'P2_P3': '（抜粋：段落②〜③）',
        'P3_ONLY': '（抜粋：段落③のみ）',
        'P4_P5': '（抜粋：段落④〜⑤）',
        'MIDDLE': '（抜粋：中盤部分）'
      };
      
      excerptInfo.textContent = excerptLabels[data.excerpt_type] || '（抜粋）';
      container.appendChild(excerptInfo);
    }
    
    // 問題文の表示（箇条書き）
    const ul = document.createElement("ul");
    ul.className = "question-sentences-list";
    data.japanese_paragraphs.forEach((paragraph, idx) => {
      // 段落内の文を句点で分割
      const sentences = paragraph.split('。').filter(s => s.trim());
      sentences.forEach((sentence, sentenceIdx) => {
        const li = document.createElement("li");
        li.className = "question-sentence-item";
        li.textContent = sentence.trim() + '。';
        ul.appendChild(li);
      });
    });
    container.appendChild(ul);
  } else if (data.japanese_sentences && data.japanese_sentences.length > 0) {
    // 旧形式（日本語文）の場合
    const sentences = document.createElement("div");
    sentences.className = "question-sentences";
    data.japanese_sentences.forEach((sentence, idx) => {
      const p = document.createElement("p");
      p.textContent = sentence;
      sentences.appendChild(p);
    });
    container.appendChild(sentences);
  }
  
  // ヒント
  const hintsTitle = document.createElement("div");
  hintsTitle.className = "hints-title";
  hintsTitle.textContent = "ヒント単語:";
  container.appendChild(hintsTitle);
  
  const hints = document.createElement("div");
  hints.className = "hints";
  data.hints.forEach(hint => {
    const span = document.createElement("span");
    span.className = "hint-item";
    
    // 動詞の場合は用法も表示
    if (hint.pos === "動詞" && hint.usage) {
      span.innerHTML = `<strong>${hint.en}</strong>：${hint.ja}（${hint.pos}）<br><span style="font-size: 0.9em; color: #64748b;">例：${hint.usage}</span>`;
    } else {
      span.textContent = `${hint.en}：${hint.ja}（${hint.pos}）`;
    }
    
    hints.appendChild(span);
  });
  container.appendChild(hints);
  
  addMessage(container, "ai");
  
  // メッセージとボタンをコンテナにまとめる
  const instructionContainer = document.createElement("div");
  instructionContainer.className = "instruction-container";
  instructionContainer.style.cssText = `
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  `;
  
  const instructionText = document.createElement("span");
  instructionText.textContent = "✍️ 英作文を入力して、添削を受けてください。";
  instructionText.style.cssText = `
    font-size: 15px;
    color: #1e293b;
  `;
  
  const modelAnswerBtn = document.createElement("button");
  modelAnswerBtn.textContent = "模範解答のみ閲覧";
  modelAnswerBtn.className = "model-answer-inline-btn";
  modelAnswerBtn.style.cssText = `
    padding: 8px 16px;
    background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  `;
  
  modelAnswerBtn.addEventListener("mouseover", () => {
    modelAnswerBtn.style.transform = "translateY(-1px)";
    modelAnswerBtn.style.boxShadow = "0 4px 12px rgba(243, 156, 18, 0.4)";
  });
  
  modelAnswerBtn.addEventListener("mouseout", () => {
    modelAnswerBtn.style.transform = "translateY(0)";
    modelAnswerBtn.style.boxShadow = "none";
  });
  
  modelAnswerBtn.addEventListener("click", () => {
    fetchModelAnswerOnly();
  });
  
  instructionContainer.appendChild(instructionText);
  instructionContainer.appendChild(modelAnswerBtn);
  
  addMessage(instructionContainer, "ai");
}

// 回答を提出
function submitAnswer() {
  const text = input.value.trim();
  
  if (!text) {
    alert("英文を入力してください。");
    return;
  }
  
  if (!currentQuestion || !currentQuestionId) {
    alert("問題が読み込まれていません。");
    return;
  }
  
  // 語数をカウント（バックエンドと同じロジック：句読点を除外）
  const words = text.match(/\b[\w'-]+\b/g) || [];
  const wordCount = words.filter(w => /[a-zA-Z]/.test(w)).length;
  
  // ユーザーの回答を表示
  addMessage(text, "user");
  input.value = "";
  wordCountEl.textContent = "0 words";
  
  // 添削リクエスト
  addMessage("🔍 添削中...（1~2分かかります）", "ai");
  
  fetch('/api/correct', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question_id: currentQuestionId,
      japanese_sentences: currentQuestion.japanese_sentences || [],
      japanese_paragraphs: currentQuestion.japanese_paragraphs || [],
      question_text: currentQuestion.question_text || "",
      user_answer: text,
      target_words: currentQuestion.target_words,
      word_count: wordCount  // フロントエンドで計算した語数を追加
    })
  })
  .then(res => res.json())
  .then(data => {
    // ローディングメッセージを削除
    chat.lastChild.remove();
    
    if (data.error) {
      addMessage(`❌ エラー: ${data.error}`, "ai");
      return;
    }
    
    // 添削結果を表示
    displayCorrection(data);
  })
  .catch(err => {
    chat.lastChild.remove();
    addMessage(`❌ エラー: ${err.message}`, "ai");
  });
}

// 添削結果を表示
function displayCorrection(data) {
  const container = document.createElement("div");
  container.className = "correction-container";
  
  // 採点結果は表示不要
  
  // 比較表示（「📝 あなたの英文 vs 修正版」セクションは非表示）
  // このセクションは削除されました
  
  // 添削ポイント
  const pointsSection = document.createElement("div");
  pointsSection.className = "points-section";
  
  // 全体評価を先に表示
  const overallEvaluation = data.points.find(p => p.level === "内容評価");
  if (overallEvaluation) {
    const pointDiv = document.createElement("div");
    pointDiv.className = "point-item overall-evaluation";
    
    const pointContent = document.createElement("div");
    pointContent.className = "point-content";
    
    const beforeAfter = document.createElement("div");
    beforeAfter.className = "before-after";
    
    let evalIcon = '✅';
    let evalClass = 'before-correct';
    
    if (overallEvaluation.after.includes('問題文の趣旨に合っています')) {
      evalIcon = '✅';
      evalClass = 'before-correct';
    } else if (overallEvaluation.after.includes('問題文の趣旨に合っていません')) {
      evalIcon = '❌';
      evalClass = 'before-error';
    } else if (overallEvaluation.after.includes('部分的に合っています')) {
      evalIcon = '⚠️';
      evalClass = 'before-improvement';
    }
    
    // 「全体評価：✅ 問題文の趣旨に合っています」の形式で表示
    beforeAfter.innerHTML = `<span class="${evalClass}"><strong>全体評価：</strong>${evalIcon} ${escapeHtml(overallEvaluation.after)}</span>`;
    pointContent.appendChild(beforeAfter);
    
    const reasonDiv = document.createElement("div");
    reasonDiv.className = "point-reason";
    // reasonから「全体評価\n」を削除して表示
    const cleanedReason = overallEvaluation.reason.replace(/^全体評価\n?/g, '');
    reasonDiv.innerHTML = escapeHtml(cleanedReason).replace(/\n/g, '<br>');
    pointContent.appendChild(reasonDiv);
    
    // 全体評価の後に語数情報を追加
    const wordCountInfo = document.createElement("div");
    wordCountInfo.className = "word-count-info";
    wordCountInfo.style.marginTop = "10px";
    wordCountInfo.style.fontSize = "14px";
    
    const wordCount = data.constraint_checks.word_count; // バックエンドから取得
    let wordCountText = '';
    let wordCountColor = '';
    
    // 翻訳問題では語数の範囲判定を表示しない（10-160語が有効範囲）
    // 単純に語数のみを表示
    wordCountText = `📝 ${wordCount} words`;
    wordCountColor = "#495057"; // グレー
    
    wordCountInfo.textContent = wordCountText;
    wordCountInfo.style.color = wordCountColor;
    wordCountInfo.style.fontWeight = "bold";
    pointContent.appendChild(wordCountInfo);
    
    pointDiv.appendChild(pointContent);
    pointsSection.appendChild(pointDiv);
  }
  
  // 文法・表現のポイントのタイトル
  const pointsTitle = document.createElement("h3");
  // 全体評価を除いた数をカウント
  const nonEvaluationPoints = data.points.filter(p => p.level !== "内容評価").length;
  pointsTitle.textContent = `文法・表現のポイント解説（${nonEvaluationPoints}項目）`;
  pointsSection.appendChild(pointsTitle);
  
  let pointCounter = 0;
  data.points.forEach((point, idx) => {
    // 全体評価はスキップ（既に表示済み）
    if (point.level === "内容評価") {
      return; // 番号カウントせずに次へ
    }
    
    // 通常の文法・表現ポイント
    pointCounter++;
    const pointDiv = document.createElement("div");
    pointDiv.className = "point-item";
    
    const pointNumber = document.createElement("div");
    pointNumber.className = "point-number";
    pointNumber.textContent = pointCounter;
    
    const pointContent = document.createElement("div");
    pointContent.className = "point-content";
    
    const beforeAfter = document.createElement("div");
    beforeAfter.className = "before-after";
    
    // 新仕様：levelに完全依存（💡廃止）
    const levelText = (point.level || '').trim();
    let beforeIcon = '❓'; // fallback
    let beforeClass = 'before-improvement';
    
    // levelに基づいて判定（シンプル）
    if (levelText.includes('❌')) {
      beforeIcon = '❌';
      beforeClass = 'before-error';
    } else if (levelText.includes('✅')) {
      beforeIcon = '✅';
      beforeClass = 'before-correct';
    }
    
    // before と after が同じかどうかで表示を分ける
    const afterEnglishOnly = point.after.split('\n')[0].trim();
    const isSame = point.before.trim() === afterEnglishOnly;
    
    // 日本語原文を表示（sentence_no を使用）
    const sentenceNoText = point.sentence_no ? `${point.sentence_no}文目` : `${pointCounter}文目`;
    const japaneseText = point.japanese_sentence || '';
    
    if (isSame) {
      // ✅ の場合：beforeのみ表示
      const formattedText = escapeHtml(point.before).replace(/\n/g, '<br>');
      beforeAfter.innerHTML = `
        <span class="${beforeClass}">${beforeIcon} ${formattedText}</span>
      `;
    } else {
      // ❌ の場合：before → after を表示
      const formattedBefore = escapeHtml(point.before).replace(/\n/g, '<br>');
      const formattedAfter = escapeHtml(point.after).replace(/\n/g, '<br>');
      beforeAfter.innerHTML = `
        <span class="${beforeClass}">${beforeIcon} ${formattedBefore}</span>
        <span class="arrow">→</span>
        <span class="after">✅ ${formattedAfter}</span>
      `;
    }
    
    pointContent.appendChild(beforeAfter);
    
    // 日本語原文をbefore/afterの後に表示
    if (japaneseText) {
      const japaneseLine = document.createElement("div");
      japaneseLine.className = "japanese-line";
      japaneseLine.style.fontSize = "14px";
      japaneseLine.style.color = "#64748b";
      japaneseLine.style.marginTop = "4px";
      japaneseLine.style.marginBottom = "8px";
      japaneseLine.textContent = `${sentenceNoText}: （${japaneseText}）`;
      pointContent.appendChild(japaneseLine);
    }
    
    const reason = document.createElement("div");
    reason.className = "point-reason";
    
    // reasonから重複英文行を削除（N文目: 英文... の行）
    let reasonText = point.reason || '';
    const reasonLines = reasonText.split('\n');
    const filteredLines = [];
    
    for (let line of reasonLines) {
      // N文目: で始まる行
      if (line.match(/^\d+文目:\s+[A-Z]/)) {
        // 英文行と判定（大文字で始まる）→ スキップ
        continue;
      }
      // その他の行は保持
      filteredLines.push(line);
    }
    
    // フィルタリング後のreasonを表示（改行も<br>に変換）
    reason.innerHTML = escapeHtml(filteredLines.join('\n')).replace(/\n/g, '<br>');
    
    pointContent.appendChild(reason);
    
    // altフィールドは表示しない（reasonで代替表現を紹介済み）
    
    pointDiv.appendChild(pointNumber);
    pointDiv.appendChild(pointContent);
    pointsSection.appendChild(pointDiv);
  });
  
  container.appendChild(pointsSection);
  
  // 理想的な英文セクション（model_answerがある場合のみ表示）
  if (data.model_answer && data.model_answer_explanation) {
    const modelAnswerSection = document.createElement("div");
    modelAnswerSection.className = "model-answer-section";
    
    // タイトルと本文は非表示（解説のみ表示）
    // const modelTitle = document.createElement("h3");
    // const modelAnswerBox = document.createElement("div");
    
    // 解説の見出しを「🌟 理想的な英文と文法・表現のポイント解説」に変更
    const explanationTitle = document.createElement("h3");
    explanationTitle.className = "model-answer-title";
    explanationTitle.textContent = "🌟 理想的な英文と文法・表現のポイント解説";
    modelAnswerSection.appendChild(explanationTitle);
    
    const modelExplanation = document.createElement("div");
    modelExplanation.className = "model-explanation";
    // 解説のみ表示（模範解答の英文は非表示）
    let fullText = data.model_answer_explanation;
    // 「文法・表現のポイント解説」という見出しを削除（重複を防ぐ）
    fullText = fullText.replace(/^文法・表現のポイント解説\s*\n*/g, '');
    
    // 「N文目:」表記を削除し、英文部分を太字にする処理
    let lines = fullText.split('\n');
    let processedLines = [];
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      // N文目: 英文 のパターンを検出（英文と日本語訳が別行の場合）
      const match = line.match(/^(\d+)文目:\s*(.+)$/);
      if (match) {
        // 「N文目:」表記を削除し、英文を太字化
        const englishText = escapeHtml(match[2].trim());
        processedLines.push('<strong>' + englishText + '</strong>');
      } else if (line.match(/^（.+）$/)) {
        // 日本語訳（全角括弧で囲まれた行）
        processedLines.push(escapeHtml(line));
      } else {
        // その他の行
        processedLines.push(escapeHtml(line));
      }
    }
    
    // 改行を<br>に変換して表示
    modelExplanation.innerHTML = processedLines.join('<br>');
    modelAnswerSection.appendChild(modelExplanation);
    
    container.appendChild(modelAnswerSection);
  }
  
  addMessage(container, "ai");
  
  // 次の問題を促す
  setTimeout(() => {
    const container = document.createElement('div');
    container.style.display = 'flex';
    container.style.alignItems = 'center';
    container.style.gap = '12px';
    container.style.flexWrap = 'wrap';
    
    const textSpan = document.createElement('span');
    textSpan.textContent = '次の問題にチャレンジしますか？';
    
    const newBtn = document.createElement('button');
    newBtn.textContent = '新しい問題を出題';
    newBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    newBtn.style.color = 'white';
    newBtn.style.border = 'none';
    newBtn.style.padding = '8px 16px';
    newBtn.style.borderRadius = '6px';
    newBtn.style.cursor = 'pointer';
    newBtn.style.fontSize = '14px';
    newBtn.style.fontWeight = '600';
    newBtn.style.transition = 'all 0.2s';
    newBtn.addEventListener('click', () => fetchNewQuestion());
    newBtn.addEventListener('mouseenter', () => {
      newBtn.style.transform = 'translateY(-2px)';
      newBtn.style.boxShadow = '0 4px 8px rgba(102, 126, 234, 0.3)';
    });
    newBtn.addEventListener('mouseleave', () => {
      newBtn.style.transform = 'translateY(0)';
      newBtn.style.boxShadow = 'none';
    });
    
    container.appendChild(textSpan);
    container.appendChild(newBtn);
    addMessage(container, "ai");
  }, 500);
}

// HTMLエスケープ
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// 模範解答のみ閲覧
function fetchModelAnswerOnly() {
  if (!currentQuestionId || !currentQuestion) {
    addMessage("⚠️ まず問題を生成してください。", "ai");
    return;
  }
  
  addMessage("🔍 模範解答を生成中...（１〜２分かかります）", "ai");
  
  fetch('/api/model_answer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question_id: currentQuestionId,
      question_text: currentQuestion.question_text || ""
    })
  })
  .then(res => res.json())
  .then(data => {
    // ローディングメッセージを削除
    chat.lastChild.remove();
    
    if (data.error) {
      addMessage(`❌ エラー: ${data.error}`, "ai");
      return;
    }
    
    // 模範解答セクションを表示
    const container = document.createElement("div");
    container.className = "correction-result-container";
    
    const modelAnswerSection = document.createElement("div");
    modelAnswerSection.className = "model-answer-section";
    
    const modelTitle = document.createElement("h3");
    modelTitle.className = "model-answer-title";
    // タイトルを「🌟 理想的な英文と文法・表現のポイント解説」に変更
    modelTitle.textContent = "🌟 理想的な英文と文法・表現のポイント解説";
    modelAnswerSection.appendChild(modelTitle);
    
    // 解説のみ表示（模範解答の英文は非表示）
    const modelExplanation = document.createElement("div");
    modelExplanation.className = "model-explanation";
    let fullText = data.model_answer_explanation;
    // 「文法・表現のポイント解説」という見出しを削除（重複を防ぐ）
    fullText = fullText.replace(/^文法・表現のポイント解説\s*\n*/g, '');
    
    // 「N文目:」表記を削除し、英文部分を太字にする処理
    let lines = fullText.split('\n');
    let processedLines = [];
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      // N文目: 英文 のパターンを検出（英文と日本語訳が別行の場合）
      const match = line.match(/^(\d+)文目:\s*(.+)$/);
      if (match) {
        // 「N文目:」表記を削除し、英文を太字化
        const englishText = escapeHtml(match[2].trim());
        processedLines.push('<strong>' + englishText + '</strong>');
      } else if (line.match(/^（.+）$/)) {
        // 日本語訳（全角括弧で囲まれた行）
        processedLines.push(escapeHtml(line));
      } else {
        // その他の行
        processedLines.push(escapeHtml(line));
      }
    }
    
    // 改行を<br>に変換して表示
    modelExplanation.innerHTML = processedLines.join('<br>');
    modelAnswerSection.appendChild(modelExplanation);
    
    container.appendChild(modelAnswerSection);
    addMessage(container, "ai");
    
    // 次の問題を促す
    setTimeout(() => {
      const container = document.createElement('div');
      container.style.display = 'flex';
      container.style.alignItems = 'center';
      container.style.gap = '12px';
      container.style.flexWrap = 'wrap';
      
      const textSpan = document.createElement('span');
      textSpan.textContent = 'この模範解答を参考に自分で英作文を書いてみましょう！';
      
      const newBtn = document.createElement('button');
      newBtn.textContent = '新しい問題を出題';
      newBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
      newBtn.style.color = 'white';
      newBtn.style.border = 'none';
      newBtn.style.padding = '8px 16px';
      newBtn.style.borderRadius = '6px';
      newBtn.style.cursor = 'pointer';
      newBtn.style.fontSize = '14px';
      newBtn.style.fontWeight = '600';
      newBtn.style.transition = 'all 0.2s';
      newBtn.addEventListener('click', () => fetchNewQuestion());
      newBtn.addEventListener('mouseenter', () => {
        newBtn.style.transform = 'translateY(-2px)';
        newBtn.style.boxShadow = '0 4px 8px rgba(102, 126, 234, 0.3)';
      });
      newBtn.addEventListener('mouseleave', () => {
        newBtn.style.transform = 'translateY(0)';
        newBtn.style.boxShadow = 'none';
      });
      
      container.appendChild(textSpan);
      container.appendChild(newBtn);
      addMessage(container, "ai");
    }, 500);
  })
  .catch(err => {
    chat.lastChild.remove();
    addMessage(`❌ エラー: ${err.message}`, "ai");
  });
}

// システム説明モーダル
const systemInfoBtn = document.getElementById('system-info-btn');
const systemInfoModal = document.getElementById('system-info-modal');
const modalClose = systemInfoModal.querySelector('.modal-close');
const modalOverlay = systemInfoModal.querySelector('.modal-overlay');

// モーダルを開く
systemInfoBtn.addEventListener('click', () => {
  systemInfoModal.classList.add('active');
  document.body.style.overflow = 'hidden'; // 背景のスクロールを防止
});

// モーダルを閉じる
const closeModal = () => {
  systemInfoModal.classList.remove('active');
  document.body.style.overflow = ''; // スクロールを復元
};

modalClose.addEventListener('click', closeModal);
modalOverlay.addEventListener('click', closeModal);

// Escキーでモーダルを閉じる
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && systemInfoModal.classList.contains('active')) {
    closeModal();
  }
});

});

