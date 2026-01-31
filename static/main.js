document.addEventListener('DOMContentLoaded', function() {

const chat = document.getElementById("chat-container");
const input = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const wordCountEl = document.getElementById("word-count");

let currentQuestion = null;
let currentQuestionId = null;
let currentSentenceCount = null; // マルチ入力モードでの文数

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

// 比較用に英文を正規化（ピリオド・スペース・大文字を統一）
function normalizeUserInputForComparison(text) {
  if (!text) return '';
  
  let normalized = text.trim();
  
  // 1. ピリオドの前のスペースを削除
  normalized = normalized.replace(/\s+\./g, '.');
  
  // 2. 文末にピリオドがない場合は追加
  if (normalized && !normalized.match(/[.!?]$/)) {
    normalized += '.';
  }
  
  // 3. ピリオド後のスペース不足を修正（. The → . The）
  normalized = normalized.replace(/([.!?])([A-Z])/g, '$1 $2');
  
  // 4. 文頭を大文字化
  normalized = normalized.replace(/^([a-z])/, (match) => match.toUpperCase());
  
  // 5. ピリオド後の文頭を大文字化
  normalized = normalized.replace(/([.!?])\s+([a-z])/g, (match, p1, p2) => p1 + ' ' + p2.toUpperCase());
  
  // 6. 複数スペースを1つに
  normalized = normalized.replace(/\s{2,}/g, ' ');
  
  return normalized.trim();
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
    // チャット履歴を消さずに、新しい問題を追加
    fetchNewQuestion();
  });
  
  content.appendChild(button);
  messageDiv.appendChild(content);
  chat.appendChild(messageDiv);
}

// マルチ入力UIをリセット
function resetMultiInputUI() {
  const multiInputContainer = document.getElementById('multi-input-container');
  if (multiInputContainer) {
    multiInputContainer.style.display = 'none';
  }
  
  const sentenceInputs = document.getElementById('sentence-inputs');
  if (sentenceInputs) {
    sentenceInputs.innerHTML = '';
  }
  
  const modelAnswerBtn = document.getElementById('model-answer-btn');
  if (modelAnswerBtn) {
    modelAnswerBtn.style.display = 'none';
  }
  
  const progressIndicator = document.getElementById('progress-indicator');
  if (progressIndicator) {
    progressIndicator.textContent = '';
  }
}

// 入力エリア下の模範解答をチャット履歴に移動
function moveModelAnswerToChat() {
  const modelAnswerSection = document.getElementById('model-answer-below-input');
  const nextQuestionDiv = document.getElementById('next-question-below-input');
  
  if (modelAnswerSection) {
    // 模範解答セクションのクローンを作成してチャット内に追加
    const container = document.createElement("div");
    container.className = "correction-container";
    
    const clonedSection = modelAnswerSection.cloneNode(true);
    clonedSection.removeAttribute('id'); // IDを削除（重複防止）
    clonedSection.style.marginTop = "0"; // チャット内ではマージンをリセット
    container.appendChild(clonedSection);
    
    addMessage(container, "ai");
    
    // 元の要素を削除
    modelAnswerSection.remove();
  }
  
  // 次の問題ボタンは削除（チャット内に追加しない）
  if (nextQuestionDiv) {
    nextQuestionDiv.remove();
  }
}

// 新しい問題を取得
function fetchNewQuestion() {
  // 入力エリア下の模範解答をチャット履歴に移動
  moveModelAnswerToChat();
  
  // マルチ入力UIをリセット（新しい問題用に準備）
  resetMultiInputUI();
  
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
    currentSentenceCount = null; // リセット
    
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
    
    // テーマヘッダー（抜粋タイプを含める）
    const themeHeader = document.createElement("div");
    themeHeader.className = "theme-header-question";
    
    // トピックラベルを日本語名に変換
    let topicName = '';
    if (data.topic_label) {
      const topicLabels = {
        "研究紹介": {"A": "記憶", "B": "習慣", "C": "睡眠・集中", "D": "運動・健康", "E": "食事", "F": "感情", "G": "デジタル", "H": "社会"},
        "時事": {"A": "医療・公衆衛生", "B": "災害", "C": "国際", "D": "環境", "E": "経済・ビジネス", "F": "科学技術", "G": "教育", "H": "地域活性"},
        "ブログ": {"A": "健康・運動", "B": "勉強", "C": "習慣", "D": "趣味", "E": "人間関係", "F": "旅行", "G": "食事", "H": "睡眠"},
        "書評": {"A": "小説", "B": "ビジネス", "C": "自己啓発", "D": "健康", "E": "伝記", "F": "哲学", "G": "歴史", "H": "エッセイ"},
        "メール・レター": {"A": "お礼", "B": "依頼", "C": "案内", "D": "報告", "E": "謝罪", "F": "祝賀", "G": "提案", "H": "近況"},
        "体験記": {"A": "インターン", "B": "留学", "C": "記事・ドキュメンタリー", "D": "展示・イベント", "E": "ボランティア", "F": "図書館・施設", "G": "仕事・職業", "H": "場面・心に残る"},
        "コラム": {"A": "マナー", "B": "教育", "C": "働き方", "D": "医療", "E": "地域・多文化", "F": "デジタル", "G": "環境", "H": "若者・家庭"},
        "図表": {"A": "学習時間", "B": "睡眠時間", "C": "施設利用", "D": "交通", "E": "運動・健康", "F": "アンケート", "G": "年代別", "H": "地域別"}
      };
      topicName = topicLabels[theme]?.[data.topic_label] || '';
    }
    
    // テーマとトピックを見やすく表示
    let themeTopicText = `📌 ${theme}`;
    if (topicName) {
      themeTopicText += ` - ${topicName}`;
    }
    themeHeader.innerHTML = themeTopicText;
    
    // 抜粋タイプを追加（グレー色）
    if (data.excerpt_type) {
      const excerptLabels = {
        'P1_ONLY': '（抜粋：段落①のみ）',
        'P2_P3': '（抜粋：段落②〜③）',
        'P3_ONLY': '（抜粋：段落③のみ）',
        'P4_P5': '（抜粋：段落④〜⑤）',
        'MIDDLE': '（抜粋：中盤部分）'
      };
      const excerptSpan = document.createElement('span');
      excerptSpan.className = 'excerpt-type-gray';
      excerptSpan.textContent = ' ' + (excerptLabels[data.excerpt_type] || '（抜粋）');
      themeHeader.appendChild(excerptSpan);
    }
    
    container.appendChild(themeHeader);
    
    // 問題文を1つの段落として表示
    const problemTextDiv = document.createElement("div");
    problemTextDiv.className = "question-problem-text";
    
    // 全ての段落を連結して1つの段落として表示
    const allText = data.japanese_paragraphs
      .map(p => p.trim())
      .join('');
    
    const textElement = document.createElement("p");
    textElement.className = "question-sentence-line";
    textElement.textContent = allText;
    problemTextDiv.appendChild(textElement);
    
    container.appendChild(problemTextDiv);
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
  
  // ヒント単語（シンプル表示）
  const hintsTitle = document.createElement("div");
  hintsTitle.className = "hints-title";
  hintsTitle.textContent = "ヒント単語:";
  container.appendChild(hintsTitle);
  
  const hints = document.createElement("div");
  hints.className = "hints";
  data.hints.forEach(hint => {
    const span = document.createElement("span");
    span.className = "hint-item";
    span.textContent = `${hint.en}：${hint.ja}（${hint.pos}）`;
    hints.appendChild(span);
  });
  container.appendChild(hints);
  
  addMessage(container, "ai");
  
  // 新しいマルチ入力UIを表示（japanese_paragraphsまたはjapanese_sentences形式の場合のみ）
  if ((data.japanese_paragraphs && data.japanese_paragraphs.length > 0) || 
      (data.japanese_sentences && data.japanese_sentences.length > 0)) {
    renderMultiInputUI(data);
  }
}

// マルチ入力UIをレンダリング
async function renderMultiInputUI(questionData) {
  // 日本語文を取得
  let japaneseSentences = [];
  if (questionData.japanese_paragraphs && questionData.japanese_paragraphs.length > 0) {
    // 段落形式の場合、文に分割
    questionData.japanese_paragraphs.forEach(paragraph => {
      const sentences = paragraph.split('。').filter(s => s.trim()).map(s => s.trim() + '。');
      japaneseSentences = japaneseSentences.concat(sentences);
    });
  } else if (questionData.japanese_sentences && questionData.japanese_sentences.length > 0) {
    japaneseSentences = questionData.japanese_sentences;
  }
  
  if (japaneseSentences.length === 0) {
    return; // 日本語文がない場合は通常モード
  }
  
  const container = document.getElementById('sentence-inputs');
  container.innerHTML = '';
  
  // 各文に対応する入力カードを作成
  japaneseSentences.forEach((jpSentence, index) => {
    const card = document.createElement('div');
    card.className = 'sentence-input-card';
    card.dataset.index = index;
    
    // ヘッダー（ステータス + ラベル + 語数）
    const header = document.createElement('div');
    header.className = 'sentence-card-header';
    
    const statusIcon = document.createElement('span');
    statusIcon.className = 'sentence-status-icon';
    statusIcon.textContent = '⏳';
    statusIcon.dataset.index = index;
    
    const label = document.createElement('span');
    label.className = 'sentence-label';
    label.textContent = `${index + 1}文目`;
    
    const wordCount = document.createElement('span');
    wordCount.className = 'sentence-word-count';
    wordCount.textContent = '0語';
    wordCount.dataset.index = index;
    
    header.appendChild(statusIcon);
    header.appendChild(label);
    
    // セパレーター
    const separator = document.createElement('span');
    separator.textContent = '|';
    separator.style.cssText = 'margin: 0 12px; color: #cbd5e1; font-weight: normal;';
    header.appendChild(separator);
    
    // 日本語プレビュー（ヘッダー内に配置）
    const preview = document.createElement('span');
    preview.className = 'japanese-preview-inline';
    preview.textContent = jpSentence;
    header.appendChild(preview);
    
    // 語数カウント（右端）
    header.appendChild(wordCount);
    card.appendChild(header);
    
    // テキストエリア
    const textarea = document.createElement('textarea');
    textarea.className = 'sentence-textarea';
    textarea.placeholder = `英訳を入力...`;
    textarea.dataset.index = index;
    textarea.rows = 3;
    
    textarea.addEventListener('input', () => {
      updateSentenceWordCount(index);
      updateSentenceStatus(index);
      updateProgressIndicator();
    });
    
    card.appendChild(textarea);
    
    // 解説表示エリア（初期は非表示）
    const explanationDiv = document.createElement('div');
    explanationDiv.className = 'sentence-explanation';
    explanationDiv.dataset.index = index;
    explanationDiv.style.display = 'none';
    card.appendChild(explanationDiv);
    
    container.appendChild(card);
  });
  
  // 進捗インジケーターを初期化
  updateProgressIndicator();
  
  // マルチ入力UIを表示、通常の入力欄を非表示
  document.getElementById('multi-input-container').style.display = 'block';
  document.getElementById('user-input').style.display = 'none';
  
  // 模範解答ボタンを表示してイベントを設定
  const modelAnswerBtn = document.getElementById('model-answer-btn');
  if (modelAnswerBtn) {
    modelAnswerBtn.style.display = 'block';
    // 既存のイベントリスナーをクリア
    const newBtn = modelAnswerBtn.cloneNode(true);
    modelAnswerBtn.parentNode.replaceChild(newBtn, modelAnswerBtn);
    newBtn.addEventListener('click', fetchModelAnswerOnly);
  }
}

// 各文の語数をカウント
function updateSentenceWordCount(index) {
  const textarea = document.querySelector(`.sentence-textarea[data-index="${index}"]`);
  const wordCountEl = document.querySelector(`.sentence-word-count[data-index="${index}"]`);
  
  if (!textarea || !wordCountEl) return;
  
  const text = textarea.value.trim();
  const words = text.match(/\b[\w'-]+\b/g) || [];
  const wordCount = words.filter(w => /[a-zA-Z]/.test(w)).length;
  
  wordCountEl.textContent = `${wordCount}語`;
}

// 各文のステータスを更新
function updateSentenceStatus(index) {
  const textarea = document.querySelector(`.sentence-textarea[data-index="${index}"]`);
  const statusIcon = document.querySelector(`.sentence-status-icon[data-index="${index}"]`);
  const card = document.querySelector(`.sentence-input-card[data-index="${index}"]`);
  
  if (!textarea || !statusIcon || !card) return;
  
  const text = textarea.value.trim();
  
  if (text.length > 0) {
    statusIcon.textContent = '✅';
    card.classList.add('filled');
  } else {
    statusIcon.textContent = '⏳';
    card.classList.remove('filled');
  }
}

// 進捗インジケーターを更新
function updateProgressIndicator() {
  const progressEl = document.getElementById('progress-indicator');
  if (!progressEl) return;
  
  const textareas = document.querySelectorAll('.sentence-textarea');
  let completed = 0;
  
  textareas.forEach(textarea => {
    if (textarea.value.trim().length > 0) {
      completed++;
    }
  });
  
  const total = textareas.length;
  const dots = Array(total).fill(0).map((_, i) => i < completed ? '●' : '○').join('');
  
  progressEl.textContent = `進捗：${completed}/${total}完了 ${dots}`;
}

// マルチ文を送信
function submitMultiSentences() {
  console.log("🚀 submitMultiSentences() started");
  
  const textareas = document.querySelectorAll('.sentence-textarea');
  console.log(`📝 Found ${textareas.length} textareas`);
  
  const userSentences = [];
  
  // 🚨重要：空の文も配列に含める（文の順序を保持するため）
  textareas.forEach((textarea, index) => {
    let text = textarea.value.trim();
    console.log(`  Textarea ${index + 1}: "${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"`);
    
    if (text.length > 0) {
      // 全角記号を半角に変換
      text = text.replace(/。$/g, '.').replace(/！$/g, '!').replace(/？$/g, '?');
      
      // 末尾に句読点がない場合、文の種類に応じて追加
      if (!/[.!?]$/.test(text)) {
        // 疑問文の判定（疑問詞または疑問形の助動詞で始まる）
        const questionWords = /^(what|where|when|why|who|whom|whose|which|how|do|does|did|can|could|would|should|will|shall|may|might|must|is|are|was|were|has|have|had|am)\b/i;
        if (questionWords.test(text)) {
          text += '?';
        } else {
          text += '.';
        }
      }
      userSentences.push(text);
    } else {
      // 空の文は空文字列として配列に追加（順序保持のため）
      userSentences.push('');
    }
  });
  
  if (userSentences.length === 0) {
    alert("少なくとも1文は入力してください。");
    return;
  }
  
  if (!currentQuestion || !currentQuestionId) {
    alert("問題が読み込まれていません。");
    return;
  }
  
  // 日本語文を取得
  let japaneseSentences = [];
  if (currentQuestion.japanese_paragraphs && currentQuestion.japanese_paragraphs.length > 0) {
    currentQuestion.japanese_paragraphs.forEach(paragraph => {
      const sentences = paragraph.split('。').filter(s => s.trim()).map(s => s.trim() + '。');
      japaneseSentences = japaneseSentences.concat(sentences);
    });
  } else if (currentQuestion.japanese_sentences && currentQuestion.japanese_sentences.length > 0) {
    japaneseSentences = currentQuestion.japanese_sentences;
  }
  
  // ユーザーの回答を表示（コメントアウト）
  const combinedAnswer = userSentences.join('\n');
  // addMessage(combinedAnswer, "user"); // 不要
  
  // 文数を保存
  currentSentenceCount = userSentences.length;
  
  // 入力欄は保持（クリアしない）
  // textareas.forEach(textarea => {
  //   textarea.value = '';
  // });
  // updateProgressIndicator();
  
  // 添削リクエスト（ローディングメッセージを入力セクションの下に表示）
  showLoadingBelowInput();
  
  // 語数をカウント
  const words = combinedAnswer.match(/\b[\w'-]+\b/g) || [];
  const wordCount = words.filter(w => /[a-zA-Z]/.test(w)).length;
  
  console.log(`📊 Word count: ${wordCount}`);
  console.log(`📤 Sending API request to /api/correct-multi...`);
  
  fetch('/api/correct-multi', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question_id: currentQuestionId,
      user_sentences: userSentences,
      japanese_sentences: japaneseSentences,
      target_words: currentQuestion.target_words,
      word_count: wordCount
    })
  })
  .then(res => {
    console.log(`📥 API response received, status: ${res.status}`);
    return res.json();
  })
  .then(data => {
    console.log(`✅ API response parsed successfully`);
    console.log(`📦 Response data:`, data);
    
    // ローディングメッセージを削除
    removeLoadingBelowInput();
    
    if (data.error) {
      console.error(`❌ API returned error:`, data.error);
      let errorMsg = `❌ エラー: ${data.error}`;
      // バリデーションエラーの詳細を追加
      if (data.details && Array.isArray(data.details)) {
        const detailsMsg = data.details.map(d => d.msg || JSON.stringify(d)).join(', ');
        errorMsg += `\n詳細: ${detailsMsg}`;
      }
      addMessage(errorMsg, "ai");
      return;
    }
    
    console.log(`🎯 currentSentenceCount: ${currentSentenceCount}`);
    
    // 添削結果を表示（マルチ入力モードでは模範解答のみ）
    if (currentSentenceCount !== null && currentSentenceCount > 0) {
      console.log(`📋 Multi-input mode: displaying explanations in cards`);
      // マルチ入力モード：各カードに解説を表示し、模範解答は入力エリアの下に表示
      displayExplanationsInCards(data.points);
      displayModelAnswerBelowInput(data);
    } else {
      // 通常モード：全ての添削結果を表示
      displayCorrection(data);
    }
  })
  .catch(err => {
    removeLoadingBelowInput();
    addMessage(`❌ エラー: ${err.message}`, "ai");
  });
}

// ローディングメッセージを入力セクションの下に表示
function showLoadingBelowInput() {
  const loadingDiv = document.createElement('div');
  loadingDiv.id = 'loading-below-input';
  loadingDiv.style.marginTop = '20px';
  loadingDiv.style.padding = '16px';
  loadingDiv.style.backgroundColor = '#f0f9ff';
  loadingDiv.style.borderRadius = '8px';
  loadingDiv.style.border = '2px solid #bae6fd';
  loadingDiv.style.textAlign = 'center';
  loadingDiv.style.fontSize = '15px';
  loadingDiv.style.fontWeight = '600';
  loadingDiv.style.color = '#0369a1';
  loadingDiv.innerHTML = '🔍 添削中...（1~2分かかります）';
  
  const multiInputContainer = document.getElementById('multi-input-container');
  if (multiInputContainer && multiInputContainer.parentNode) {
    multiInputContainer.parentNode.insertBefore(loadingDiv, multiInputContainer.nextSibling);
  }
}

// ローディングメッセージを削除
function removeLoadingBelowInput() {
  const loadingDiv = document.getElementById('loading-below-input');
  if (loadingDiv) {
    loadingDiv.remove();
  }
}

// 各文の解説をカードに表示
function displayExplanationsInCards(points) {
  if (currentSentenceCount === null || currentSentenceCount === 0) {
    return; // マルチ入力モードでない
  }
  
  // 各ポイントを対応するカードに表示
  let pointCounter = 0;
  points.forEach((point, idx) => {
    // 全体評価はスキップ
    if (point.level === "内容評価") {
      return;
    }
    
    pointCounter++;
    const cardIndex = pointCounter - 1;
    const explanationDiv = document.querySelector(`.sentence-explanation[data-index="${cardIndex}"]`);
    const textarea = document.querySelector(`.sentence-textarea[data-index="${cardIndex}"]`);
    const card = document.querySelector(`.sentence-input-card[data-index="${cardIndex}"]`);
    
    if (!explanationDiv || !textarea || !card) {
      return;
    }
    
    // levelに基づいてアイコンを決定
    const levelText = (point.level || '').trim();
    let icon = '❓';
    let iconClass = 'explanation-icon-improvement';
    
    if (levelText.includes('❌')) {
      icon = '❌';
      iconClass = 'explanation-icon-error';
    } else if (levelText.includes('✅')) {
      icon = '✅';
      iconClass = 'explanation-icon-correct';
    }
    
    // 表示するbefore/afterを決定
    // - ✅ のとき: 形式差分（ピリオド/大文字など）でも❌表示しない。正規化済みのbeforeを表示。
    // - ❌ のとき: ユーザー入力（original_beforeがあればそれ）→ after を表示。
    const normalizedBeforeText = (point.before || '').trim();
    const originalBeforeText = (point.original_before || textarea.value || '').trim();
    const afterText = (point.after || '').split('\n')[0].trim();
    
    // 解説内容を生成
    let explanationHTML = `<div class="explanation-content">`;
    
    // 英文表示（バックエンドのlevelを信頼）
    if (levelText.includes('✅')) {
      explanationHTML += `<div class="explanation-sentence ${iconClass}">${icon} ${escapeHtml(normalizedBeforeText)}</div>`;
    } else {
      explanationHTML += `<div class="explanation-sentence explanation-icon-error">❌ ${escapeHtml(originalBeforeText)}</div>`;
      explanationHTML += `<div class="explanation-arrow">→</div>`;
      explanationHTML += `<div class="explanation-sentence explanation-icon-correct">✅ ${escapeHtml(afterText)}</div>`;
    }
    
    // reasonから不要な部分を削除
    let reasonText = point.reason || '';
    const reasonLines = reasonText.split('\n');
    const filteredLines = [];
    
    for (let line of reasonLines) {
      // N文目: で始まる行をスキップ
      if (line.match(/^\d+文目:/)) {
        continue;
      }
      // 括弧だけの行をスキップ
      if (line.match(/^（.+）$/)) {
        continue;
      }
      if (line.trim()) {
        filteredLines.push(line);
      }
    }
    
    const cleanReason = filteredLines.join('\n');
    if (cleanReason) {
      explanationHTML += `<div class="explanation-reason">${escapeHtml(cleanReason).replace(/\n/g, '<br>')}</div>`;
    }
    
    explanationHTML += `</div>`;
    
    // 解説をカードに追加
    explanationDiv.innerHTML = explanationHTML;
    explanationDiv.style.display = 'block';
    
    // textareaを非表示
    textarea.style.display = 'none';
    
    // カードのステータスを更新
    const statusIcon = card.querySelector('.sentence-status-icon');
    if (statusIcon) {
      statusIcon.textContent = icon;
    }
  });
}

// テキストをN個の文に分割
// テキストをN個の文に分割
function splitIntoSentences(text, count) {
  // ピリオド、感嘆符、疑問符で分割
  const sentences = [];
  const regex = /[.!?]+\s+/g;
  let lastIndex = 0;
  let match;
  
  while ((match = regex.exec(text)) !== null && sentences.length < count - 1) {
    sentences.push(text.substring(lastIndex, match.index + match[0].length).trim());
    lastIndex = regex.lastIndex;
  }
  
  // 残りのテキストを最後の文として追加
  if (lastIndex < text.length) {
    sentences.push(text.substring(lastIndex).trim());
  }
  
  return sentences;
}

// 回答を提出
function submitAnswer() {
  // マルチ入力モードかチェック
  const multiContainer = document.getElementById('multi-input-container');
  if (multiContainer && multiContainer.style.display !== 'none') {
    // マルチ文入力モード
    submitMultiSentences();
    return;
  }
  
  // 通常モード
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
  
  // 通常モードではsentenceCountをnullにリセット
  currentSentenceCount = null;
  
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
      let errorMsg = `❌ エラー: ${data.error}`;
      // バリデーションエラーの詳細を追加
      if (data.details && Array.isArray(data.details)) {
        const detailsMsg = data.details.map(d => d.msg || JSON.stringify(d)).join(', ');
        errorMsg += `\n詳細: ${detailsMsg}`;
      }
      addMessage(errorMsg, "ai");
      return;
    }
    
    // デバッグ：レスポンスをログ出力
    console.log("Correction response:", data);
    console.log("Points count:", data.points ? data.points.length : 0);
    
    // 添削結果を表示
    displayCorrection(data);
  })
  .catch(err => {
    chat.lastChild.remove();
    console.error("Correction error:", err);
    addMessage(`❌ エラー: ${err.message}`, "ai");
  });
}

// 添削結果を表示
function displayCorrection(data) {
  console.log("✅ displayCorrection called");
  console.log("📦 Full data:", JSON.stringify(data, null, 2));
  console.log(`📊 Points count: ${data.points ? data.points.length : 0}`);
  
  const container = document.createElement("div");
  container.className = "correction-container";
  
  // 採点結果は表示不要
  
  // 比較表示（「📝 あなたの英文 vs 修正版」セクションは非表示）
  // このセクションは削除されました
  
  // 添削ポイント
  const pointsSection = document.createElement("div");
  pointsSection.className = "points-section";
  
  // データの存在確認
  if (!data.points || data.points.length === 0) {
    console.error("No points in correction data!");
    pointsSection.innerHTML = "<p>❌ 添削データの取得に失敗しました。ページを更新してやり直してください。</p>";
    container.appendChild(pointsSection);
    chat.appendChild(container);
    return;
  }
  
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
  
  // 文法・表現のポイントのタイトル（マルチ入力モードでは非表示）
  if (currentSentenceCount === null || currentSentenceCount === 0) {
    const pointsTitle = document.createElement("h3");
    // 全体評価を除いた数をカウント
    const nonEvaluationPoints = data.points.filter(p => p.level !== "内容評価").length;
    pointsTitle.textContent = `文法・表現のポイント解説（${nonEvaluationPoints}項目）`;
    pointsSection.appendChild(pointsTitle);
  }
  
  let pointCounter = 0;
  console.log(`🔄 Starting to process ${data.points.length} points...`);
  data.points.forEach((point, idx) => {
    console.log(`🔍 Point ${idx + 1}/${data.points.length}: level="${point.level}"`);
    
    // 全体評価はスキップ（既に表示済み）
    if (point.level === "内容評価") {
      console.log(`   ⏭️ Skipping 内容評価`);
      return; // 番号カウントせずに次へ
    }
    
    // マルチ入力モードでは個別のカードに表示するため、この一覧表示はスキップ
    if (currentSentenceCount !== null && currentSentenceCount > 0) {
      console.log(`   ⏭️ Skipping (multi-input mode, will be shown in cards)`);
      return;
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
    
    // 🔍 デバッグログ追加
    console.log(`🔍 Point ${pointCounter}: level="${levelText}"`);
    console.log(`   before="${point.before ? point.before.substring(0, 50) : 'null'}..."`);
    console.log(`   after="${point.after ? point.after.substring(0, 50) : 'null'}..."`);
    
    // levelに基づいて判定（シンプル）
    if (levelText.includes('❌')) {
      beforeIcon = '❌';
      beforeClass = 'before-error';
      console.log(`   ✅ Detected ❌ in level`);
    } else if (levelText.includes('✅')) {
      beforeIcon = '✅';
      beforeClass = 'before-correct';
      console.log(`   ✅ Detected ✅ in level`);
    } else {
      console.log(`   ⚠️ No ❌ or ✅ detected in level="${levelText}"`);
    }
    
    // マルチ入力モードの場合、beforeとafterを文番号で分割
    let beforeText = point.before;
    let afterText = point.after;
    let originalBeforeText = point.original_before || point.before;  // 正規化前の入力
    
    if (currentSentenceCount !== null && currentSentenceCount > 0) {
      // 文を分割
      const beforeSentences = splitIntoSentences(point.before, currentSentenceCount);
      const afterSentences = splitIntoSentences(point.after.split('\n')[0], currentSentenceCount);
      const originalBeforeSentences = splitIntoSentences(originalBeforeText, currentSentenceCount);
      
      // pointCounterに対応する文を抽出（pointCounter - 1 はインデックス）
      const sentenceIndex = pointCounter - 1;
      if (sentenceIndex < beforeSentences.length) {
        beforeText = beforeSentences[sentenceIndex];
      }
      if (sentenceIndex < afterSentences.length) {
        afterText = afterSentences[sentenceIndex];
      }
      if (sentenceIndex < originalBeforeSentences.length) {
        originalBeforeText = originalBeforeSentences[sentenceIndex];
      }
    } else {
      // 通常モード：afterの最初の行のみ使用
      afterText = point.after.split('\n')[0].trim();
    }
    
    // 正規化前の入力と修正後を比較（デバッグ用）
    const normalizedOriginalBefore = normalizeUserInputForComparison(originalBeforeText);
    const normalizedAfter = normalizeUserInputForComparison(afterText);
    const isSameNormalized = normalizedOriginalBefore === normalizedAfter;
    
    // デバッグログ（isSame判定の矛盾を検出）
    if (!isSameNormalized && levelText.includes('✅')) {
      console.log(`⚠️ Point ${pointCounter}: Normalized strings differ but level is ✅`);
      console.log(`  originalBeforeText: "${originalBeforeText}"`);
      console.log(`  normalizedOriginalBefore: "${normalizedOriginalBefore}"`);
      console.log(`  afterText: "${afterText}"`);
      console.log(`  normalizedAfter: "${normalizedAfter}"`);
      console.log(`  levelText: "${levelText}"`);
    }
    
    // 日本語原文を表示（sentence_no を使用）
    const sentenceNoText = point.sentence_no ? `${point.sentence_no}文目` : `${pointCounter}文目`;
    const japaneseText = point.japanese_sentence || '';
    
    // ★★★ バックエンドのlevelを信頼して表示 ★★★
    // バックエンドで既にA==B判定済みなので、フロントエンドは結果を表示するだけ
    if (levelText.includes('✅')) {
      // ✅ の場合：beforeを表示（整形済み英文＝学習者が読むのに気持ちいい形）
      const formattedText = escapeHtml(beforeText).replace(/\n/g, '<br>');
      beforeAfter.innerHTML = `
        <span class="${beforeClass}">${beforeIcon} ${formattedText}</span>
      `;
    } else {
      // ❌ の場合：original_before → after を表示
      const formattedOriginalBefore = escapeHtml(originalBeforeText).replace(/\n/g, '<br>');
      const formattedAfter = escapeHtml(afterText).replace(/\n/g, '<br>');
      beforeAfter.innerHTML = `
        <span class="${beforeClass}">${beforeIcon} ${formattedOriginalBefore}</span>
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
    
    // reasonから不要な行を削除（N文目: の行と括弧だけの行）
    let reasonText = point.reason || '';
    const reasonLines = reasonText.split('\n');
    const filteredLines = [];
    
    for (let line of reasonLines) {
      // N文目: で始まる行（日本語・英語問わず）→ スキップ
      if (line.match(/^\d+文目:/)) {
        continue;
      }
      // 括弧だけの行（日本語訳）→ スキップ
      if (line.match(/^[（(].*[）)]$/)) {
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
    
    // マルチ入力モードの場合、文数に基づいて処理
    if (currentSentenceCount !== null && currentSentenceCount > 0) {
      modelExplanation.innerHTML = processModelAnswerBySentenceCount(fullText, currentSentenceCount);
    } else {
      // 通常モード：「N文目:」表記を削除し、英文部分を太字にする処理
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
    }
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

// マルチ入力モード用：模範解答を入力エリアの下に表示
function displayModelAnswerBelowInput(data) {
  // 既存の模範解答セクションを削除
  const existingSection = document.getElementById('model-answer-below-input');
  if (existingSection) {
    existingSection.remove();
  }
  const existingNextBtn = document.getElementById('next-question-below-input');
  if (existingNextBtn) {
    existingNextBtn.remove();
  }
  
  // 理想的な英文セクション（model_answerがある場合のみ表示）
  if (data.model_answer && data.model_answer_explanation) {
    const modelAnswerSection = document.createElement("div");
    modelAnswerSection.id = 'model-answer-below-input';
    modelAnswerSection.className = "model-answer-section";
    modelAnswerSection.style.marginTop = "24px";
    modelAnswerSection.style.padding = "20px";
    modelAnswerSection.style.backgroundColor = "#f8f9fa";
    modelAnswerSection.style.borderRadius = "12px";
    modelAnswerSection.style.border = "2px solid #e9ecef";
    
    // 解説の見出し
    const explanationTitle = document.createElement("h3");
    explanationTitle.className = "model-answer-title";
    explanationTitle.textContent = "🌟 理想的な英文と文法・表現のポイント解説";
    explanationTitle.style.marginTop = "0";
    explanationTitle.style.marginBottom = "16px";
    explanationTitle.style.fontSize = "18px";
    explanationTitle.style.fontWeight = "700";
    explanationTitle.style.color = "#1e293b";
    modelAnswerSection.appendChild(explanationTitle);
    
    const modelExplanation = document.createElement("div");
    modelExplanation.className = "model-explanation";
    let fullText = data.model_answer_explanation;
    // 「文法・表現のポイント解説」という見出しを削除
    fullText = fullText.replace(/^文法・表現のポイント解説\s*\n*/g, '');
    
    // マルチ入力モードの場合、文数に基づいて処理
    if (currentSentenceCount !== null && currentSentenceCount > 0) {
      modelExplanation.innerHTML = processModelAnswerBySentenceCount(fullText, currentSentenceCount);
    } else {
      // 通常モード
      let lines = fullText.split('\n');
      let processedLines = [];
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const match = line.match(/^(\d+)文目:\s*(.+)$/);
        if (match) {
          const englishText = escapeHtml(match[2].trim());
          processedLines.push('<strong>' + englishText + '</strong>');
        } else if (line.match(/^（.+）$/)) {
          processedLines.push(escapeHtml(line));
        } else {
          processedLines.push(escapeHtml(line));
        }
      }
      modelExplanation.innerHTML = processedLines.join('<br>');
    }
    modelAnswerSection.appendChild(modelExplanation);
    
    // 入力エリアの後に挿入（DOM上の位置：画面下部）
    const inputArea = document.getElementById('input-area');
    if (inputArea && inputArea.parentNode) {
      inputArea.parentNode.insertBefore(modelAnswerSection, inputArea.nextSibling);
    }
    
    // 「次の問題」ボタンを模範解答の下に追加
    const nextQuestionDiv = document.createElement('div');
    nextQuestionDiv.id = 'next-question-below-input';
    nextQuestionDiv.style.marginTop = '20px';
    nextQuestionDiv.style.padding = '20px';
    nextQuestionDiv.style.display = 'flex';
    nextQuestionDiv.style.alignItems = 'center';
    nextQuestionDiv.style.gap = '12px';
    nextQuestionDiv.style.flexWrap = 'wrap';
    
    const textSpan = document.createElement('span');
    textSpan.textContent = '次の問題にチャレンジしますか？';
    textSpan.style.fontSize = '15px';
    textSpan.style.fontWeight = '600';
    
    const newBtn = document.createElement('button');
    newBtn.textContent = '新しい問題を出題';
    newBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    newBtn.style.color = 'white';
    newBtn.style.border = 'none';
    newBtn.style.padding = '10px 20px';
    newBtn.style.borderRadius = '8px';
    newBtn.style.cursor = 'pointer';
    newBtn.style.fontSize = '15px';
    newBtn.style.fontWeight = '600';
    newBtn.style.transition = 'all 0.2s';
    newBtn.addEventListener('click', () => {
      // fetchNewQuestion内でmoveModelAnswerToChatが呼ばれるため、
      // ここでは削除処理を行わずに直接fetchNewQuestionを呼ぶ
      fetchNewQuestion();
    });
    newBtn.addEventListener('mouseenter', () => {
      newBtn.style.transform = 'translateY(-2px)';
      newBtn.style.boxShadow = '0 4px 8px rgba(102, 126, 234, 0.3)';
    });
    newBtn.addEventListener('mouseleave', () => {
      newBtn.style.transform = 'translateY(0)';
      newBtn.style.boxShadow = 'none';
    });
    
    nextQuestionDiv.appendChild(textSpan);
    nextQuestionDiv.appendChild(newBtn);
    
    if (modelAnswerSection.parentNode) {
      modelAnswerSection.parentNode.insertBefore(nextQuestionDiv, modelAnswerSection.nextSibling);
    }
  }
}

// マルチ入力モード用：模範解答のみを表示（チャット内）
function displayModelAnswerOnly(data) {
  const container = document.createElement("div");
  container.className = "correction-container";
  
  // 理想的な英文セクション（model_answerがある場合のみ表示）
  if (data.model_answer && data.model_answer_explanation) {
    const modelAnswerSection = document.createElement("div");
    modelAnswerSection.className = "model-answer-section";
    
    // 解説の見出し
    const explanationTitle = document.createElement("h3");
    explanationTitle.className = "model-answer-title";
    explanationTitle.textContent = "🌟 理想的な英文と文法・表現のポイント解説";
    modelAnswerSection.appendChild(explanationTitle);
    
    const modelExplanation = document.createElement("div");
    modelExplanation.className = "model-explanation";
    let fullText = data.model_answer_explanation;
    // 「文法・表現のポイント解説」という見出しを削除
    fullText = fullText.replace(/^文法・表現のポイント解説\s*\n*/g, '');
    
    // マルチ入力モードの場合、文数に基づいて処理
    if (currentSentenceCount !== null && currentSentenceCount > 0) {
      modelExplanation.innerHTML = processModelAnswerBySentenceCount(fullText, currentSentenceCount);
    } else {
      // 通常モード
      let lines = fullText.split('\n');
      let processedLines = [];
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const match = line.match(/^(\d+)文目:\s*(.+)$/);
        if (match) {
          const englishText = escapeHtml(match[2].trim());
          processedLines.push('<strong>' + englishText + '</strong>');
        } else if (line.match(/^（.+）$/)) {
          processedLines.push(escapeHtml(line));
        } else {
          processedLines.push(escapeHtml(line));
        }
      }
      modelExplanation.innerHTML = processedLines.join('<br>');
    }
    modelAnswerSection.appendChild(modelExplanation);
    container.appendChild(modelAnswerSection);
  }
  
  addMessage(container, "ai");
  
  // 次の問題を促す
  setTimeout(() => {
    const promptContainer = document.createElement('div');
    promptContainer.style.display = 'flex';
    promptContainer.style.alignItems = 'center';
    promptContainer.style.gap = '12px';
    promptContainer.style.flexWrap = 'wrap';
    
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
    
    promptContainer.appendChild(textSpan);
    promptContainer.appendChild(newBtn);
    addMessage(promptContainer, "ai");
  }, 500);
}

// マルチ入力モード用：文数に基づいて模範解答を処理
function processModelAnswerBySentenceCount(fullText, sentenceCount) {
  const lines = fullText.split('\n');
  const processedLines = [];
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    // N文目: 英文 のパターンを検出（英文と日本語訳が別行の場合）
    const match = line.match(/^(\d+)文目:\s*(.+)$/);
    if (match) {
      const sentenceNum = parseInt(match[1]);
      // currentSentenceCount以下の文のみ表示
      if (sentenceNum <= sentenceCount) {
        // 「N文目:」表記を削除し、英文を太字化
        const englishText = escapeHtml(match[2].trim());
        processedLines.push('<strong>' + englishText + '</strong>');
      }
    } else if (line.match(/^（.+）$/)) {
      // 日本語訳（全角括弧で囲まれた行）
      // 直前に英文があれば表示
      if (processedLines.length > 0) {
        processedLines.push(escapeHtml(line));
      }
    } else {
      // その他の行（説明など）
      // 直前に英文があれば表示（文の説明として）
      if (processedLines.length > 0 && line.trim().length > 0) {
        processedLines.push(escapeHtml(line));
      } else if (line.trim().length > 0) {
        // 独立した行（タイトルなど）
        processedLines.push(escapeHtml(line));
      }
    }
  }
  
  return processedLines.join('<br>');
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
    
    // マルチ入力モードの場合、文数に基づいて処理
    if (currentSentenceCount !== null && currentSentenceCount > 0) {
      modelExplanation.innerHTML = processModelAnswerBySentenceCount(fullText, currentSentenceCount);
    } else {
      // 通常モード：「N文目:」表記を削除し、英文部分を太字にする処理
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
    }
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

