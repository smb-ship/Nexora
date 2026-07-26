/**
 * Nexora embeddable chat widget.
 *
 * Usage: drop this on any external site —
 *   <script src="https://your-nexora-domain.com/chat-widget.js"
 *           data-public-key="widget_xxx"
 *           data-api-base="https://your-nexora-domain.com/api/v1"
 *           async></script>
 *
 * data-public-key: required, from Settings > Chat Widget in Nexora.
 * data-api-base: optional, defaults to http://localhost:8000/api/v1 for local dev.
 *
 * Polling-based by design (mirrors the backend's documented approach —
 * no WebSockets/SSE). Polls every 3s while the panel is open.
 */
(function () {
  var currentScript = document.currentScript;
  if (!currentScript) return;

  var PUBLIC_KEY = currentScript.getAttribute("data-public-key");
  var API_BASE = currentScript.getAttribute("data-api-base") || "http://localhost:8000/api/v1";

  if (!PUBLIC_KEY) {
    console.error("[nexora-chat-widget] Missing required data-public-key attribute.");
    return;
  }

  var STORAGE_KEY = "nexora_chat_conversation_" + PUBLIC_KEY;
  var POLL_INTERVAL_MS = 3000;

  var state = {
    conversationId: null,
    open: false,
    messages: [],
    pollHandle: null,
    welcomeMessage: "Hi! How can we help?",
  };

  // --- API calls ---

  function apiFetch(path, options) {
    return fetch(API_BASE + path, Object.assign({
      headers: { "Content-Type": "application/json" },
    }, options)).then(function (res) {
      if (!res.ok) throw new Error("Request failed: " + res.status);
      return res.status === 204 ? null : res.json();
    });
  }

  function startSession() {
    return apiFetch("/chat/public/" + PUBLIC_KEY + "/sessions", {
      method: "POST",
      body: JSON.stringify({}),
    }).then(function (data) {
      state.conversationId = data.conversation_id;
      state.welcomeMessage = data.welcome_message;
      try {
        sessionStorage.setItem(STORAGE_KEY, data.conversation_id);
      } catch (e) {
        /* sessionStorage unavailable — degrade gracefully, session won't persist across reloads */
      }
      return data;
    });
  }

  function sendMessage(body) {
    return apiFetch("/chat/public/conversations/" + state.conversationId + "/messages", {
      method: "POST",
      body: JSON.stringify({ body: body }),
    });
  }

  function pollMessages() {
    return apiFetch("/chat/public/conversations/" + state.conversationId + "/messages", {
      method: "GET",
    }).then(function (messages) {
      state.messages = messages || [];
      renderMessages();
    }).catch(function () {
      /* silent — next poll will retry */
    });
  }

  // --- UI ---

  var styleTag = document.createElement("style");
  styleTag.textContent = [
    "#nexora-chat-bubble{position:fixed;bottom:20px;right:20px;width:56px;height:56px;border-radius:50%;",
    "background:#111;color:#fff;display:flex;align-items:center;justify-content:center;cursor:pointer;",
    "box-shadow:0 2px 10px rgba(0,0,0,.2);z-index:999999;font-family:sans-serif;font-size:24px;}",
    "#nexora-chat-panel{position:fixed;bottom:88px;right:20px;width:320px;max-height:440px;",
    "background:#fff;border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,.2);display:none;",
    "flex-direction:column;overflow:hidden;font-family:sans-serif;z-index:999999;}",
    "#nexora-chat-panel.open{display:flex;}",
    "#nexora-chat-header{background:#111;color:#fff;padding:12px 16px;font-size:14px;font-weight:600;}",
    "#nexora-chat-messages{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px;}",
    ".nexora-msg{max-width:80%;padding:8px 10px;border-radius:8px;font-size:13px;line-height:1.4;}",
    ".nexora-msg.visitor{align-self:flex-end;background:#111;color:#fff;}",
    ".nexora-msg.agent,.nexora-msg.system{align-self:flex-start;background:#f0f0f0;color:#111;}",
    "#nexora-chat-input-row{display:flex;border-top:1px solid #eee;padding:8px;gap:6px;}",
    "#nexora-chat-input{flex:1;border:1px solid #ddd;border-radius:6px;padding:6px 8px;font-size:13px;outline:none;}",
    "#nexora-chat-send{background:#111;color:#fff;border:none;border-radius:6px;padding:6px 12px;font-size:13px;cursor:pointer;}",
  ].join("");
  document.head.appendChild(styleTag);

  var bubble = document.createElement("div");
  bubble.id = "nexora-chat-bubble";
  bubble.innerHTML = "&#128172;";
  document.body.appendChild(bubble);

  var panel = document.createElement("div");
  panel.id = "nexora-chat-panel";
  panel.innerHTML =
    '<div id="nexora-chat-header">Chat with us</div>' +
    '<div id="nexora-chat-messages"></div>' +
    '<div id="nexora-chat-input-row">' +
    '<input id="nexora-chat-input" type="text" placeholder="Type a message..." />' +
    '<button id="nexora-chat-send">Send</button>' +
    "</div>";
  document.body.appendChild(panel);

  var messagesEl = panel.querySelector("#nexora-chat-messages");
  var inputEl = panel.querySelector("#nexora-chat-input");
  var sendBtn = panel.querySelector("#nexora-chat-send");

  function renderMessages() {
    messagesEl.innerHTML = "";
    if (state.messages.length === 0) {
      var welcome = document.createElement("div");
      welcome.className = "nexora-msg system";
      welcome.textContent = state.welcomeMessage;
      messagesEl.appendChild(welcome);
    }
    state.messages.forEach(function (m) {
      var el = document.createElement("div");
      el.className = "nexora-msg " + m.sender_type;
      el.textContent = m.body;
      messagesEl.appendChild(el);
    });
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function startPolling() {
    stopPolling();
    state.pollHandle = setInterval(pollMessages, POLL_INTERVAL_MS);
  }

  function stopPolling() {
    if (state.pollHandle) {
      clearInterval(state.pollHandle);
      state.pollHandle = null;
    }
  }

  function ensureSession() {
    if (state.conversationId) return Promise.resolve();

    var existing = null;
    try {
      existing = sessionStorage.getItem(STORAGE_KEY);
    } catch (e) {
      /* ignore */
    }

    if (existing) {
      state.conversationId = existing;
      return Promise.resolve();
    }
    return startSession();
  }

  function togglePanel() {
    state.open = !state.open;
    panel.classList.toggle("open", state.open);
    if (state.open) {
      ensureSession()
        .then(pollMessages)
        .then(startPolling)
        .catch(function () {
          renderError();
        });
    } else {
      stopPolling();
    }
  }

  function renderError() {
    messagesEl.innerHTML =
      '<div class="nexora-msg system">Sorry, chat is unavailable right now.</div>';
  }

  function handleSend() {
    var text = inputEl.value.trim();
    if (!text || !state.conversationId) return;
    inputEl.value = "";
    sendMessage(text).then(pollMessages).catch(function () {
      /* silent — next poll will resync */
    });
  }

  bubble.addEventListener("click", togglePanel);
  sendBtn.addEventListener("click", handleSend);
  inputEl.addEventListener("keydown", function (e) {
    if (e.key === "Enter") handleSend();
  });
})();