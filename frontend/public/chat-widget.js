(function () {
  const currentScript = document.currentScript;
  const publicKey = currentScript.getAttribute("data-public-key");
  const apiBase = currentScript.getAttribute("data-api-base") || "http://localhost:8000/api/v1";

  if (!publicKey) {
    console.error("[Nexora Chat Widget] Missing data-public-key attribute on script tag.");
    return;
  }

  const STORAGE_KEY = `nexora_chat_${publicKey}`;
  let conversationId = null;
  let pollInterval = null;
  let lastMessageCount = 0;

  // --- Styles (scoped via a single wrapper id, no external CSS needed) ---
  const style = document.createElement("style");
  style.textContent = `
    #nexora-chat-bubble {
      position: fixed; bottom: 20px; right: 20px; width: 56px; height: 56px;
      border-radius: 50%; background: #111827; color: #fff; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 4px 12px rgba(0,0,0,0.25); z-index: 999998; border: none;
      font-size: 24px; transition: transform 0.15s ease;
    }
    #nexora-chat-bubble:hover { transform: scale(1.05); }
    #nexora-chat-window {
      position: fixed; bottom: 88px; right: 20px; width: 320px; height: 440px;
      background: #fff; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.25);
      display: none; flex-direction: column; overflow: hidden; z-index: 999999;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    #nexora-chat-window.open { display: flex; }
    #nexora-chat-header {
      background: #111827; color: #fff; padding: 12px 16px; font-size: 14px; font-weight: 600;
      display: flex; justify-content: space-between; align-items: center;
    }
    #nexora-chat-close { background: none; border: none; color: #fff; cursor: pointer; font-size: 18px; line-height: 1; }
    #nexora-chat-messages {
      flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 8px;
      background: #f9fafb;
    }
    .nexora-msg {
      max-width: 80%; padding: 8px 12px; border-radius: 10px; font-size: 13px; line-height: 1.4;
      word-wrap: break-word;
    }
    .nexora-msg-visitor { align-self: flex-end; background: #111827; color: #fff; }
    .nexora-msg-agent { align-self: flex-start; background: #e5e7eb; color: #111827; }
    #nexora-chat-form {
      display: flex; gap: 8px; padding: 10px; border-top: 1px solid #e5e7eb; background: #fff;
    }
    #nexora-chat-input {
      flex: 1; border: 1px solid #d1d5db; border-radius: 8px; padding: 8px 10px; font-size: 13px; outline: none;
    }
    #nexora-chat-send {
      background: #111827; color: #fff; border: none; border-radius: 8px; padding: 8px 12px;
      font-size: 13px; cursor: pointer;
    }
    #nexora-chat-send:disabled { opacity: 0.5; cursor: default; }
  `;
  document.head.appendChild(style);

  // --- DOM ---
  const bubble = document.createElement("button");
  bubble.id = "nexora-chat-bubble";
  bubble.innerHTML = "💬";
  bubble.setAttribute("aria-label", "Open chat");

  const win = document.createElement("div");
  win.id = "nexora-chat-window";
  win.innerHTML = `
    <div id="nexora-chat-header">
      <span>Chat with us</span>
      <button id="nexora-chat-close" aria-label="Close chat">&times;</button>
    </div>
    <div id="nexora-chat-messages"></div>
    <form id="nexora-chat-form">
      <input id="nexora-chat-input" type="text" placeholder="Type a message..." autocomplete="off" />
      <button id="nexora-chat-send" type="submit">Send</button>
    </form>
  `;

  document.body.appendChild(win);
  document.body.appendChild(bubble);

  const messagesEl = win.querySelector("#nexora-chat-messages");
  const formEl = win.querySelector("#nexora-chat-form");
  const inputEl = win.querySelector("#nexora-chat-input");
  const sendBtn = win.querySelector("#nexora-chat-send");
  const closeBtn = win.querySelector("#nexora-chat-close");

  function renderMessages(messages) {
    messagesEl.innerHTML = "";
    messages.forEach((m) => {
      if (m.sender_type === "system") return;
      const div = document.createElement("div");
      div.className = `nexora-msg nexora-msg-${m.sender_type === "agent" ? "agent" : "visitor"}`;
      div.textContent = m.body;
      messagesEl.appendChild(div);
    });
    messagesEl.scrollTop = messagesEl.scrollHeight;
    lastMessageCount = messages.length;
  }

  async function startSession() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      conversationId = stored;
      return;
    }
    const res = await fetch(`${apiBase}/chat/public/${publicKey}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    if (!res.ok) {
      console.error("[Nexora Chat Widget] Failed to start session:", res.status);
      return;
    }
    const data = await res.json();
    conversationId = data.conversation_id;
    localStorage.setItem(STORAGE_KEY, conversationId);
    renderMessages([{ sender_type: "agent", body: data.welcome_message }]);
  }

  async function poll() {
    if (!conversationId) return;
    try {
      const res = await fetch(`${apiBase}/chat/public/conversations/${conversationId}/messages`);
      if (!res.ok) return; // conversation may have been closed; fail quietly
      const messages = await res.json();
      if (messages.length !== lastMessageCount) renderMessages(messages);
    } catch {
      // network hiccup — next poll tick will retry, no need to surface an error to the visitor
    }
  }

  async function sendMessage(body) {
    if (!conversationId || !body.trim()) return;
    sendBtn.disabled = true;
    try {
      await fetch(`${apiBase}/chat/public/conversations/${conversationId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body: body.trim() }),
      });
      await poll();
    } finally {
      sendBtn.disabled = false;
    }
  }

  bubble.addEventListener("click", async () => {
    const isOpen = win.classList.toggle("open");
    if (isOpen) {
      if (!conversationId) await startSession();
      await poll();
      if (!pollInterval) pollInterval = setInterval(poll, 4000);
    }
  });

  closeBtn.addEventListener("click", () => {
    win.classList.remove("open");
  });

  formEl.addEventListener("submit", (e) => {
    e.preventDefault();
    const value = inputEl.value;
    inputEl.value = "";
    sendMessage(value);
  });
})();