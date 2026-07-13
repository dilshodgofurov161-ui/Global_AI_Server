/**
 * AIYIM v4.0 — Offline Pentest AI Terminal
 * API-free: PentestBrain bilimlar bazasi bilan ishlaydi
 * Streaming simulyatsiya, chat tarix, Mermaid, code highlighting, export.
 */

// ═══════════════════════════════════════════
// [MED-02] STORAGE ENCRYPTION HELPERS
// ═══════════════════════════════════════════
const STORAGE_SECRET = (() => {
  let key = sessionStorage.getItem('_sk');
  if (!key) {
    key = [...crypto.getRandomValues(new Uint8Array(16))]
      .map(b => b.toString(16).padStart(2, '0')).join('');
    sessionStorage.setItem('_sk', key);
  }
  return key;
})();

function xorEncrypt(str, key) {
  let result = '';
  for (let i = 0; i < str.length; i++) {
    result += String.fromCharCode(str.charCodeAt(i) ^ key.charCodeAt(i % key.length));
  }
  return btoa(unescape(encodeURIComponent(result)));
}

function xorDecrypt(encoded, key) {
  try {
    const str = decodeURIComponent(escape(atob(encoded)));
    let result = '';
    for (let i = 0; i < str.length; i++) {
      result += String.fromCharCode(str.charCodeAt(i) ^ key.charCodeAt(i % key.length));
    }
    return result;
  } catch {
    return null;
  }
}

function secureStorageSet(storageKey, value) {
  const json = JSON.stringify(value);
  const encrypted = xorEncrypt(json, STORAGE_SECRET);
  localStorage.setItem(storageKey, encrypted);
}

function secureStorageGet(storageKey, fallback) {
  const raw = localStorage.getItem(storageKey);
  if (!raw) return fallback;
  try {
    const decrypted = xorDecrypt(raw, STORAGE_SECRET);
    if (decrypted) return JSON.parse(decrypted);
  } catch {}
  try { return JSON.parse(raw); } catch {}
  return fallback;
}

// ═══════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════
let chats = secureStorageGet('aiyim_chats', []);
let currentChatId = null;
let isGenerating = false;
let safetyBypass = true;
let currentImageBase64 = null;

// ═══════════════════════════════════════════
// DOM ELEMENTS
// ═══════════════════════════════════════════
const chatContainer = document.getElementById('chatContainer');
const welcomeScreen = document.getElementById('welcomeScreen');
const msgInput = document.getElementById('msgInput');
const sendBtn = document.getElementById('sendBtn');
const charCount = document.getElementById('charCount');
const searchStatus = document.getElementById('searchStatus');
const chatList = document.getElementById('chatList');
const currentChatTitle = document.getElementById('currentChatTitle');
const sidebar = document.getElementById('sidebar');
const statusText = document.getElementById('statusText');

const imageInput = document.getElementById('imageInput');
const attachBtn = document.getElementById('attachBtn');
const imagePreviewContainer = document.getElementById('imagePreviewContainer');
const imagePreview = document.getElementById('imagePreview');
const removeImageBtn = document.getElementById('removeImageBtn');

// ═══════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════
function init() {
  marked.setOptions({ gfm: true, breaks: true, headerIds: false });
  loadSettings();
  renderChatList();

  if (chats.length === 0 || !currentChatId) {
    startNewChat();
  } else {
    loadChat(currentChatId);
  }

  setupEventListeners();

  // Offline mode — server health check o'rniga
  statusText.textContent = 'OFFLINE ENGINE v4.0';
}

// ═══════════════════════════════════════════
// EVENT LISTENERS
// ═══════════════════════════════════════════
function setupEventListeners() {
  // Input
  msgInput.addEventListener('input', () => {
    msgInput.style.height = 'auto';
    msgInput.style.height = Math.min(msgInput.scrollHeight, 200) + 'px';
    const len = msgInput.value.length;
    charCount.textContent = `${len}/8000`;
    if (len > 8000) {
      msgInput.value = msgInput.value.substring(0, 8000);
      charCount.textContent = '8000/8000';
    }
    sendBtn.disabled = (len === 0 && !currentImageBase64) || isGenerating;
  });

  // Enter to send
  msgInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  sendBtn.addEventListener('click', handleSend);
  document.getElementById('newChatBtn').addEventListener('click', startNewChat);
  document.getElementById('clearAllBtn').addEventListener('click', clearAllChats);

  // Sidebar toggle
  document.getElementById('toggleSidebar').addEventListener('click', () => {
    sidebar.classList.remove('open');
  });
  document.getElementById('openSidebar').addEventListener('click', () => {
    sidebar.classList.add('open');
  });

  // Export
  document.getElementById('exportBtn').addEventListener('click', showExportModal);
  document.getElementById('exportMd').addEventListener('click', () => exportChat('md'));
  document.getElementById('exportTxt').addEventListener('click', () => exportChat('txt'));
  document.getElementById('exportCancel').addEventListener('click', () => {
    document.getElementById('exportModal').style.display = 'none';
  });

  // Safety modal — professional mode
  const safetyModalEl = document.getElementById('safetyModal');
  if (safetyModalEl) safetyModalEl.style.display = 'none';

  // Image upload
  attachBtn.addEventListener('click', () => {
    imageInput.click();
  });
  imageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleImageSelect(file);
  });
  removeImageBtn.addEventListener('click', removeSelectedImage);
}

// ═══════════════════════════════════════════
// SETTINGS
// ═══════════════════════════════════════════
function loadSettings() {
  const saved = secureStorageGet('aiyim_settings', {});
  if (saved.lastChatId) currentChatId = saved.lastChatId;
}

function saveSettings() {
  secureStorageSet('aiyim_settings', {
    lastChatId: currentChatId
  });
}

// ═══════════════════════════════════════════
// CHAT MANAGEMENT
// ═══════════════════════════════════════════
function startNewChat() {
  currentChatId = Date.now().toString();
  const newChat = {
    id: currentChatId,
    title: 'Yangi Sessiya',
    messages: [],
    updatedAt: Date.now()
  };
  chats.unshift(newChat);
  saveChats();
  renderChatList();

  chatContainer.innerHTML = '';
  chatContainer.appendChild(welcomeScreen);
  welcomeScreen.style.display = 'flex';
  currentChatTitle.textContent = 'YANGI SESSIYA';

  if (window.innerWidth <= 768) sidebar.classList.remove('open');
  msgInput.focus();
}

function getChat(id) { return chats.find(c => c.id === id); }

function saveChats() {
  if (chats.length > 50) chats = chats.slice(0, 50);
  chats.sort((a, b) => b.updatedAt - a.updatedAt);
  secureStorageSet('aiyim_chats', chats);
  saveSettings();
}

function loadChat(id) {
  const chat = getChat(id);
  if (!chat) { startNewChat(); return; }

  currentChatId = id;
  currentChatTitle.textContent = chat.title;
  chatContainer.innerHTML = '';

  if (chat.messages.length === 0) {
    chatContainer.appendChild(welcomeScreen);
    welcomeScreen.style.display = 'flex';
  } else {
    welcomeScreen.style.display = 'none';
    chat.messages.forEach(msg => {
      appendMessageUI(msg.role, msg.content, null, false, msg.image);
    });
    scrollToBottom();
  }

  renderChatList();
  saveSettings();
  if (window.innerWidth <= 768) sidebar.classList.remove('open');
}

function deleteChat(id, e) {
  e.stopPropagation();
  chats = chats.filter(c => c.id !== id);
  saveChats();
  renderChatList();
  if (currentChatId === id) startNewChat();
  showToast('Sessiya o\'chirildi', 'success');
}

function clearAllChats() {
  if (confirm('Barcha sessiyalar o\'chiriladi. Rozimisiz?')) {
    chats = [];
    localStorage.removeItem('aiyim_chats');
    sessionStorage.removeItem('aiyim_safety_bypass');
    safetyBypass = false;
    startNewChat();
    showToast('Barcha sessiyalar tozalandi', 'success');
  }
}

function renderChatList() {
  chatList.innerHTML = '';
  if (chats.length === 0) {
    chatList.innerHTML = '<div style="padding:10px;text-align:center;color:var(--text-muted);font-size:12px;">Hali sessiyalar yo\'q</div>';
    return;
  }
  chats.forEach(chat => {
    const div = document.createElement('div');
    div.className = `chat-item ${chat.id === currentChatId ? 'active' : ''}`;
    div.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      <span>${escapeHTML(chat.title)}</span>
      <button class="chat-delete-btn" onclick="deleteChat('${chat.id}', event)" title="O'chirish">✕</button>
    `;
    div.onclick = () => loadChat(chat.id);
    chatList.appendChild(div);
  });
}

// ═══════════════════════════════════════════
// GLOBAL SUGGESTION FUNCTION
// ═══════════════════════════════════════════
window.sendSuggestion = function(text) {
  msgInput.value = text;
  msgInput.dispatchEvent(new Event('input'));
  handleSend();
};

// ═══════════════════════════════════════════
// UI HELPERS
// ═══════════════════════════════════════════
function escapeHTML(str) {
  return str.replace(/[&<>'"]/g, tag => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[tag]));
}

function scrollToBottom() {
  setTimeout(() => { chatContainer.scrollTop = chatContainer.scrollHeight; }, 60);
}

function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  toast.className = `toast show ${type}`;
  toast.innerHTML = type === 'success'
    ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/></svg> ${message}`
    : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg> ${message}`;
  setTimeout(() => { toast.classList.remove('show'); }, 3500);
}

// ═══════════════════════════════════════════
// MESSAGE UI
// ═══════════════════════════════════════════
function appendMessageUI(role, content, sources = null, animate = true, image = null) {
  welcomeScreen.style.display = 'none';

  const div = document.createElement('div');
  div.className = `message ${role}`;
  if (animate) div.classList.add('msg-animate');

  const avatar = role === 'user' ? 'USR' : 'AI';
  const author = role === 'user' ? 'OPERATOR' : 'AIYIM';

  let htmlContent = escapeHTML(content);
  if (role === 'assistant') {
    htmlContent = renderMarkdown(content);
  }

  let imageHTML = '';
  if (image) {
    imageHTML = `<div style="margin-top: 8px;"><img src="${image}" style="max-width: 100%; max-height: 250px; border-radius: var(--radius); border: 1px solid var(--border); display: block;" alt="Uploaded Image" onclick="window.open(this.src, '_blank')"></div>`;
  }

  div.innerHTML = `
    <div class="avatar">${avatar}</div>
    <div class="message-content-wrapper">
      <div class="message-author">${author}</div>
      <div class="message-bubble ${role === 'assistant' ? 'markdown-body' : ''}">
        ${htmlContent}
        ${imageHTML}
      </div>
    </div>
  `;

  chatContainer.appendChild(div);
  
  if (role === 'assistant') {
    postProcessMessage(div);
  }
  
  scrollToBottom();
  return div;
}

function createStreamingMessage() {
  welcomeScreen.style.display = 'none';

  const div = document.createElement('div');
  div.className = 'message assistant msg-animate';
  div.id = 'streamingMessage';
  div.innerHTML = `
    <div class="avatar">AI</div>
    <div class="message-content-wrapper">
      <div class="message-author">AIYIM</div>
      <div class="message-bubble markdown-body" id="streamingContent">
        <span class="cursor-blink">▊</span>
      </div>
    </div>
  `;
  chatContainer.appendChild(div);
  scrollToBottom();
  return div;
}

function updateStreamingMessage(text) {
  const el = document.getElementById('streamingContent');
  if (!el) return;
  el.innerHTML = renderMarkdown(text) + '<span class="cursor-blink">▊</span>';
  scrollToBottom();
}

function finalizeStreamingMessage(text) {
  const el = document.getElementById('streamingContent');
  if (!el) return;
  el.innerHTML = renderMarkdown(text);

  const msgDiv = document.getElementById('streamingMessage');
  if (msgDiv) {
    msgDiv.id = '';
    postProcessMessage(msgDiv);
  }
}

// ═══════════════════════════════════════════
// MARKDOWN & CODE RENDERING
// ═══════════════════════════════════════════
function renderMarkdown(text) {
  let rawHTML = marked.parse(text);
  let safeHTML = DOMPurify.sanitize(rawHTML, {
    ADD_TAGS: ['pre', 'code', 'span'],
    ADD_ATTR: ['class', 'data-lang']
  });
  return safeHTML;
}

function postProcessMessage(msgDiv) {
  // Highlight code blocks & add copy buttons
  msgDiv.querySelectorAll('pre code').forEach(block => {
    hljs.highlightElement(block);
    addCopyButton(block.closest('pre'));
  });

  // Render mermaid diagrams
  msgDiv.querySelectorAll('code.language-mermaid').forEach(async (block) => {
    const pre = block.closest('pre');
    const code = block.textContent;
    const container = document.createElement('div');
    container.className = 'mermaid-container';
    
    try {
      const id = 'mermaid-' + Math.random().toString(36).substr(2, 9);
      const { svg } = await mermaid.render(id, code);
      if (svg.includes('Syntax error')) throw new Error('Mermaid syntax error generated');
      container.innerHTML = `
        <div class="mermaid-label">📊 Attack Flow Diagram</div>
        <div class="mermaid-svg">${svg}</div>
      `;
    } catch (e) {
      container.innerHTML = `<div class="mermaid-error" style="display: none;">⚠️ Diagram render xatosi</div>`;
      console.warn('Mermaid error:', e);
    }
    
    pre.replaceWith(container);
  });

  // Handle images
  msgDiv.querySelectorAll('img').forEach(img => {
    if (img.src.includes('pollinations.ai')) {
      img.classList.add('ai-generated-image');
      img.style.cursor = 'pointer';
      img.onclick = () => window.open(img.src, '_blank');
    }
  });
}

function addCopyButton(pre) {
  if (!pre || pre.querySelector('.copy-btn')) return;
  
  const btn = document.createElement('button');
  btn.className = 'copy-btn';
  btn.innerHTML = '📋 Copy';
  btn.onclick = async () => {
    const code = pre.querySelector('code');
    try {
      await navigator.clipboard.writeText(code.textContent);
      btn.innerHTML = '✅ Copied!';
      btn.classList.add('copied');
      setTimeout(() => {
        btn.innerHTML = '📋 Copy';
        btn.classList.remove('copied');
      }, 2000);
    } catch {
      const textarea = document.createElement('textarea');
      textarea.value = code.textContent;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      btn.innerHTML = '✅ Copied!';
      setTimeout(() => { btn.innerHTML = '📋 Copy'; }, 2000);
    }
  };
  pre.style.position = 'relative';
  pre.appendChild(btn);
}

// ═══════════════════════════════════════════
// THINKING INDICATOR
// ═══════════════════════════════════════════
function showThinking() {
  const div = document.createElement('div');
  div.className = 'message assistant';
  div.id = 'thinkingIndicator';
  div.innerHTML = `
    <div class="avatar">🤖</div>
    <div class="message-content-wrapper">
      <div class="message-author">AIYIM</div>
      <div class="thinking-box">
        <div class="dot"></div><div class="dot"></div><div class="dot"></div>
        <span class="thinking-text">Bilimlar bazasi tahlil qilinmoqda...</span>
      </div>
    </div>
  `;
  chatContainer.appendChild(div);
  scrollToBottom();
}

function hideThinking() {
  const el = document.getElementById('thinkingIndicator');
  if (el) el.remove();
}

// ═══════════════════════════════════════════
// SEND LOGIC — OFFLINE (PentestBrain)
// ═══════════════════════════════════════════
async function handleSend() {
  const text = msgInput.value.trim();
  if ((!text && !currentImageBase64) || isGenerating) return;

  const chat = getChat(currentChatId);
  if (!chat) return;

  // Capture current image & reset
  const tempImage = currentImageBase64;
  currentImageBase64 = null;
  imageInput.value = '';
  imagePreviewContainer.style.display = 'none';
  imagePreview.src = '';

  // UI Updates
  msgInput.value = '';
  msgInput.style.height = 'auto';
  charCount.textContent = '0/8000';
  sendBtn.disabled = true;
  isGenerating = true;

  // User message
  appendMessageUI('user', text, null, true, tempImage);
  chat.messages.push({ role: 'user', content: text, image: tempImage });

  // Set title from first message
  if (chat.messages.length === 1) {
    const titleText = text || 'Rasm tahlili';
    chat.title = titleText.substring(0, 35) + (titleText.length > 35 ? '...' : '');
    currentChatTitle.textContent = chat.title;
    renderChatList();
  }

  chat.updatedAt = Date.now();
  saveChats();

  // ======= OFFLINE RESPONSE (PentestBrain) =======
  await handleOfflineResponse(text, chat);

  isGenerating = false;
  sendBtn.disabled = false;
  msgInput.focus();
}

async function handleOfflineResponse(query, chat) {
  // Fikrlash animatsiyasi
  showThinking();

  // Biroz kutish (tabiiy ko'rinish uchun)
  await new Promise(r => setTimeout(r, 400 + Math.random() * 600));

  // PentestBrain dan javob olish
  const brain = window.PentestBrain;
  let responseText = '';

  if (brain) {
    responseText = brain.getResponse(query);
  } else {
    responseText = '⚠️ PentestBrain yuklanmadi. Sahifani yangilang.';
  }

  hideThinking();

  // Streaming simulyatsiya (harf-harf chiqarish)
  createStreamingMessage();

  const totalChars = responseText.length;
  let currentIndex = 0;

  // Adaptive tezlik: qisqa javoblarga sekinroq, uzunlarga tezroq
  const baseDelay = totalChars > 2000 ? 1 : totalChars > 1000 ? 2 : 3;

  await new Promise((resolve) => {
    const chunkSize = Math.max(3, Math.floor(totalChars / 200)); // Har safar necha belgi

    function streamNext() {
      if (currentIndex >= totalChars) {
        finalizeStreamingMessage(responseText);
        resolve();
        return;
      }

      currentIndex = Math.min(currentIndex + chunkSize, totalChars);
      updateStreamingMessage(responseText.substring(0, currentIndex));

      setTimeout(streamNext, baseDelay);
    }

    streamNext();
  });

  // Saqlash
  chat.messages.push({ role: 'assistant', content: responseText });
  chat.updatedAt = Date.now();
  saveChats();
}

// ═══════════════════════════════════════════
// EXPORT
// ═══════════════════════════════════════════
function showExportModal() {
  const chat = getChat(currentChatId);
  if (!chat || chat.messages.length === 0) {
    showToast('Export uchun xabarlar yo\'q', 'error');
    return;
  }
  document.getElementById('exportModal').style.display = 'flex';
}

function exportChat(format) {
  const chat = getChat(currentChatId);
  if (!chat) return;

  let content = '';
  const title = chat.title || 'AIYIM Chat';

  if (format === 'md') {
    content = `# ${title}\n\n*AIYIM Pentest AI v4.0 — ${new Date().toLocaleString()}*\n\n---\n\n`;
    chat.messages.forEach(msg => {
      const label = msg.role === 'user' ? '## 👤 OPERATOR' : '## 🤖 AIYIM';
      content += `${label}\n\n${msg.content}\n\n---\n\n`;
    });
    content += `\n> ⚠️ Bu ma'lumotlar faqat ta'lim va authorized penetration testing uchun.\n`;
  } else {
    content = `${title}\nAIYIM Pentest AI v4.0 — ${new Date().toLocaleString()}\n${'='.repeat(60)}\n\n`;
    chat.messages.forEach(msg => {
      const label = msg.role === 'user' ? '[OPERATOR]' : '[AIYIM]';
      content += `${label}\n${msg.content}\n\n${'-'.repeat(40)}\n\n`;
    });
  }

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `aiyim-${chat.id}.${format}`;
  a.click();
  URL.revokeObjectURL(url);

  document.getElementById('exportModal').style.display = 'none';
  showToast(`Chat ${format.toUpperCase()} formatda yuklandi`, 'success');
}

// ═══════════════════════════════════════════
// IMAGE UPLOAD & COMPRESSION (4K Support)
// ═══════════════════════════════════════════
function handleImageSelect(file) {
  if (!file.type.startsWith('image/')) {
    showToast('Faqat rasm yuklash mumkin!', 'error');
    return;
  }

  showToast('Rasm qayta ishlanmoqda...', 'success');
  const reader = new FileReader();
  reader.readAsDataURL(file);
  reader.onload = function(event) {
    const img = new Image();
    img.src = event.target.result;
    img.onload = function() {
      const maxDim = 2048;
      let width = img.width;
      let height = img.height;

      if (width > maxDim || height > maxDim) {
        if (width > height) {
          height = Math.round((height * maxDim) / width);
          width = maxDim;
        } else {
          width = Math.round((width * maxDim) / height);
          height = maxDim;
        }
      }

      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;

      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, width, height);

      currentImageBase64 = canvas.toDataURL('image/jpeg', 0.85);

      imagePreview.src = currentImageBase64;
      imagePreviewContainer.style.display = 'flex';
      sendBtn.disabled = false;
      showToast('Rasm tayyor', 'success');
    };
  };
  reader.onerror = function() {
    showToast('Rasmni o\'qishda xatolik', 'error');
  };
}

function removeSelectedImage() {
  currentImageBase64 = null;
  imageInput.value = '';
  imagePreviewContainer.style.display = 'none';
  imagePreview.src = '';
  sendBtn.disabled = msgInput.value.trim().length === 0;
  showToast('Rasm olib tashlandi', 'success');
}

// ═══════════════════════════════════════════
// START
// ═══════════════════════════════════════════
init();
