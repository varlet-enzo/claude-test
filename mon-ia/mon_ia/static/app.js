"use strict";

// ---------- Petits utilitaires ----------

const $ = (selector) => document.querySelector(selector);

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

const saved = {
  get(key, fallback) {
    try {
      const value = localStorage.getItem(`monia.${key}`);
      return value === null ? fallback : JSON.parse(value);
    } catch {
      return fallback;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(`monia.${key}`, JSON.stringify(value));
    } catch {
      // Navigation privée ou stockage désactivé : tant pis, ce n'est qu'un confort.
    }
  },
};

async function errorMessage(response) {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") return data.detail;
  } catch {
    // Réponse sans JSON.
  }
  return `Erreur ${response.status}`;
}

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  if (!response.ok) throw new Error(await errorMessage(response));
  return response.json();
}

function networkMessage(error) {
  if (error instanceof TypeError) return "Impossible de joindre le serveur de ton IA. Est-il toujours lancé ?";
  return error.message || String(error);
}

async function readEvents(response, onEvent) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let end;
    while ((end = buffer.indexOf("\n\n")) !== -1) {
      const block = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      for (const line of block.split("\n")) {
        if (line.startsWith("data: ")) onEvent(JSON.parse(line.slice(6)));
      }
    }
  }
}

function formatSize(bytes) {
  if (!bytes) return "";
  return bytes >= 1e9 ? `${(bytes / 1e9).toFixed(1).replace(".", ",")} Go` : `${Math.round(bytes / 1e6)} Mo`;
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const area = el("textarea");
    area.value = text;
    document.body.append(area);
    area.select();
    document.execCommand("copy");
    area.remove();
  }
}

// ---------- Affichage du texte mis en forme (Markdown) ----------

if (window.DOMPurify) {
  DOMPurify.addHook("afterSanitizeAttributes", (node) => {
    if (node.tagName === "A") {
      node.setAttribute("target", "_blank");
      node.setAttribute("rel", "noopener noreferrer");
    }
  });
}

function renderMarkdown(target, text) {
  if (window.marked && window.DOMPurify) {
    target.innerHTML = DOMPurify.sanitize(marked.parse(text, { gfm: true, breaks: true }));
  } else {
    target.textContent = text;
    target.style.whiteSpace = "pre-wrap";
  }
  for (const pre of target.querySelectorAll("pre")) {
    const button = el("button", "copy-code", "Copier");
    button.type = "button";
    button.addEventListener("click", async () => {
      await copyText((pre.querySelector("code") || pre).innerText);
      button.textContent = "Copié !";
      setTimeout(() => (button.textContent = "Copier"), 1200);
    });
    pre.append(button);
  }
}

// ---------- État et éléments de la page ----------

const state = {
  name: "Mon IA",
  conversationId: null,
  conversations: [],
  models: [],
  defaultModel: null,
  attachments: [],
  trayWarning: null,
  streaming: false,
  controller: null,
  pulling: false,
};

const ui = {
  sidebar: $("#sidebar"),
  backdrop: $("#sidebar-backdrop"),
  conversations: $("#conversations"),
  messages: $("#messages"),
  thread: $("#thread"),
  welcome: $("#welcome"),
  banner: $("#banner"),
  status: $("#status"),
  modelSelect: $("#model-select"),
  composer: $("#composer"),
  input: $("#input"),
  send: $("#send"),
  fileInput: $("#file-input"),
  tray: $("#tray"),
  thinking: $("#thinking"),
  thinkingLabel: $("#thinking-label"),
  thinkingText: $("#thinking-text"),
  dropZone: $("#drop-zone"),
};

const TOOL_ICONS = {
  recherche_web: "🔎",
  lire_page_web: "📄",
  calculer: "🧮",
  memoriser: "💾",
  oublier: "🗑️",
  date_heure: "🕒",
};

// ---------- Défilement ----------

let stickToBottom = true;
ui.messages.addEventListener("scroll", () => {
  const { scrollHeight, scrollTop, clientHeight } = ui.messages;
  stickToBottom = scrollHeight - scrollTop - clientHeight < 120;
});

function scrollToBottom(force = false) {
  if (force || stickToBottom) ui.messages.scrollTop = ui.messages.scrollHeight;
}

// ---------- Messages ----------

function showThread() {
  ui.welcome.hidden = true;
}

function addUserMessage({ text, images = [], documents = [] }) {
  const root = el("article", "message-user");
  if (images.length) {
    const box = el("div", "user-images");
    for (const src of images) {
      const image = el("img");
      image.src = src;
      image.alt = "Image jointe";
      box.append(image);
    }
    root.append(box);
  }
  if (documents.length) {
    const chips = el("div", "chips");
    for (const name of documents) {
      const chip = el("span", "chip");
      chip.append("📄 ", el("span", "", name));
      chips.append(chip);
    }
    root.append(chips);
  }
  if (text) root.append(el("div", "user-bubble", text));
  ui.thread.append(root);
  return root;
}

class AssistantView {
  constructor(name) {
    this.root = el("article", "message-assistant");
    const head = el("div", "assistant-head");
    head.append(el("span", "avatar"), el("span", "", name));
    this.tools = el("div", "tools");
    this.tools.hidden = true;
    this.body = el("div", "markdown");
    this.typing = el("div", "typing");
    this.typing.append(el("i"), el("i"), el("i"));
    this.notices = el("div", "notices");
    this.foot = el("div", "message-foot");
    this.root.append(head, this.tools, this.body, this.typing, this.notices, this.foot);
    this.text = "";
    this.thinkingText = "";
    this.pendingTools = [];
    this.separate = false;
    this.frame = 0;
    this.result = {};
  }

  appendThinking(delta) {
    if (!this.thinkingBox) {
      this.thinkingBox = el("details", "thinking");
      const summary = el("summary");
      this.thinkingTitle = el("span", "", "Réflexion en cours…");
      summary.append(this.thinkingTitle);
      this.thinkingBody = el("div", "thinking-text");
      this.thinkingBox.append(summary, this.thinkingBody);
      this.root.insertBefore(this.thinkingBox, this.tools);
    }
    this.thinkingText += delta;
    this.thinkingBody.textContent = this.thinkingText;
  }

  appendText(delta) {
    if (this.separate && this.text) this.text += "\n\n";
    this.separate = false;
    this.text += delta;
    this.typing.hidden = true;
    if (this.thinkingTitle) this.thinkingTitle.textContent = "Réflexion";
    if (!this.frame) {
      this.frame = requestAnimationFrame(() => {
        this.frame = 0;
        renderMarkdown(this.body, this.text);
        scrollToBottom();
      });
    }
  }

  addTool(name, label) {
    this.tools.hidden = false;
    const chip = el("div", "tool");
    chip.append(el("span", "spinner"), el("span", "tool-label", `${TOOL_ICONS[name] || "🛠️"} ${label || name}`));
    this.tools.append(chip);
    this.pendingTools.push(chip);
    this.separate = true;
    this.typing.hidden = false;
  }

  resolveTool(summary, error) {
    const chip = this.pendingTools.shift();
    if (!chip) return;
    chip.querySelector(".spinner")?.remove();
    if (summary) {
      const text = el("span", "tool-summary", `· ${summary}`);
      text.title = summary;
      chip.append(text);
    }
    chip.classList.toggle("error", Boolean(error));
  }

  addNotice(message, isError = false) {
    this.notices.append(el("div", isError ? "notice error" : "notice", `${isError ? "⚠️" : "ℹ️"} ${message}`));
  }

  finish() {
    if (this.frame) cancelAnimationFrame(this.frame);
    this.frame = 0;
    this.typing.remove();
    if (this.text) renderMarkdown(this.body, this.text);
    if (this.thinkingTitle) this.thinkingTitle.textContent = "Réflexion";
    while (this.pendingTools.length) this.resolveTool("", false);
    const { model, stats } = this.result;
    const parts = [];
    if (model) parts.push(model);
    if (stats?.tokens) parts.push(`${stats.tokens} tokens`);
    if (stats?.speed) parts.push(`${String(stats.speed).replace(".", ",")} tokens/s`);
    this.foot.replaceChildren();
    if (this.text) {
      const copy = el("button", "icon-btn");
      copy.type = "button";
      copy.title = "Copier la réponse";
      copy.setAttribute("aria-label", "Copier la réponse");
      copy.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>';
      copy.addEventListener("click", async () => {
        await copyText(this.text);
        copy.title = "Copié !";
      });
      this.foot.append(copy);
    }
    if (parts.length) this.foot.append(el("span", "", parts.join(" · ")));
  }
}

function renderConversationItems(items) {
  for (const item of items) {
    if (item.role === "user") {
      addUserMessage({ text: item.text, images: item.images, documents: item.attachments.slice(item.images.length) });
      continue;
    }
    const view = new AssistantView(state.name);
    if (item.thinking) view.appendThinking(item.thinking);
    for (const tool of item.tools) {
      view.addTool(tool.name, tool.label);
      view.resolveTool(tool.summary, tool.error);
    }
    view.text = item.text;
    for (const notice of item.notices) view.addNotice(notice);
    view.result = { model: item.model, stats: item.stats };
    ui.thread.append(view.root);
    view.finish();
  }
}

// ---------- Envoi d'un message ----------

function setStreaming(streaming) {
  state.streaming = streaming;
  ui.send.classList.toggle("stop", streaming);
  ui.send.setAttribute("aria-label", streaming ? "Arrêter la réponse" : "Envoyer");
}

function stop() {
  state.controller?.abort();
}

function handleEvent(view, event) {
  switch (event.type) {
    case "conversation":
      state.conversationId = event.id;
      saved.set("conversation", event.id);
      loadConversations();
      break;
    case "thinking":
      view.appendThinking(event.text);
      break;
    case "text":
      view.appendText(event.text);
      break;
    case "tool_call":
      view.addTool(event.name, event.label);
      break;
    case "tool_result":
      view.resolveTool(event.summary, event.error);
      break;
    case "notice":
      view.addNotice(event.message);
      break;
    case "error":
      view.addNotice(event.message, true);
      break;
    case "done":
      view.result = { model: event.model, stats: event.stats };
      break;
  }
  scrollToBottom();
}

async function send(forcedText) {
  if (state.streaming) return;
  const text = (forcedText ?? ui.input.value).trim();
  const attachments = state.attachments;
  if (!text && !attachments.length) return;
  if (!ui.modelSelect.value) {
    openModels("Il faut d'abord installer un modèle : choisis-en un ci-dessous.");
    return;
  }

  ui.input.value = "";
  autosize();
  state.attachments = [];
  renderTray();
  showThread();
  const images = attachments.filter((file) => file.isImage);
  const userNode = addUserMessage({
    text,
    images: images.map((file) => file.preview),
    documents: attachments.filter((file) => !file.isImage).map((file) => file.name),
  });
  const view = new AssistantView(state.name);
  ui.thread.append(view.root);
  scrollToBottom(true);

  setStreaming(true);
  const controller = new AbortController();
  state.controller = controller;
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify({
        conversation_id: state.conversationId,
        message: text,
        attachments: [...images, ...attachments.filter((file) => !file.isImage)].map(({ name, type, data }) => ({ name, type, data })),
        model: ui.modelSelect.value,
        thinking: ui.thinking.checked,
      }),
    });
    if (!response.ok) {
      // Rien n'a été enregistré : on rend le message pour pouvoir le corriger.
      const message = await errorMessage(response);
      userNode.remove();
      view.root.remove();
      ui.input.value = text;
      autosize();
      state.attachments = attachments;
      state.trayWarning = `⚠️ ${message}`;
      renderTray();
      if (!ui.thread.children.length && !state.conversationId) ui.welcome.hidden = false;
      return;
    }
    await readEvents(response, (event) => handleEvent(view, event));
  } catch (error) {
    if (error.name !== "AbortError") view.addNotice(networkMessage(error), true);
  } finally {
    view.finish();
    setStreaming(false);
    state.controller = null;
  }
}

// ---------- Fichiers joints ----------

const MAX_FILE_SIZE = 20 * 1024 * 1024;

function readAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1] || "");
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

async function imageToJpeg(file, maxSide = 1536) {
  const url = URL.createObjectURL(file);
  try {
    const image = await new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = url;
    });
    const scale = Math.min(1, maxSide / Math.max(image.naturalWidth, image.naturalHeight));
    const canvas = el("canvas");
    canvas.width = Math.max(1, Math.round(image.naturalWidth * scale));
    canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));
    const context = canvas.getContext("2d");
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    const preview = canvas.toDataURL("image/jpeg", 0.88);
    return { preview, data: preview.split(",")[1] };
  } finally {
    URL.revokeObjectURL(url);
  }
}

async function addFiles(files) {
  for (const file of files) {
    if (file.size > MAX_FILE_SIZE) {
      state.trayWarning = `« ${file.name} » est trop gros (20 Mo maximum).`;
      continue;
    }
    try {
      if (file.type.startsWith("image/")) {
        const { preview, data } = await imageToJpeg(file);
        state.attachments.push({ name: file.name || "image.jpg", type: "image/jpeg", data, preview, isImage: true });
      } else {
        const data = await readAsBase64(file);
        state.attachments.push({ name: file.name, type: file.type || "application/octet-stream", data, isImage: false });
      }
    } catch {
      state.trayWarning = `Impossible de lire « ${file.name} ».`;
    }
  }
  renderTray();
}

function renderTray() {
  ui.tray.replaceChildren();
  state.attachments.forEach((file, index) => {
    const item = el("div", "tray-item");
    if (file.isImage) {
      const image = el("img");
      image.src = file.preview;
      image.alt = "";
      item.append(image);
    } else {
      item.append(el("span", "tray-icon", "📄"));
    }
    const name = el("span", "", file.name);
    name.title = file.name;
    const remove = el("button", "tray-remove", "×");
    remove.type = "button";
    remove.setAttribute("aria-label", `Retirer ${file.name}`);
    remove.addEventListener("click", () => {
      state.attachments.splice(index, 1);
      renderTray();
    });
    item.append(name, remove);
    ui.tray.append(item);
  });
  const capabilities = currentModel()?.capabilities;
  if (state.attachments.some((file) => file.isImage) && capabilities && !capabilities.includes("vision")) {
    ui.tray.append(el("div", "tray-warning", "⚠️ Ce modèle ne sait pas regarder les images : choisis un modèle marqué « images » (par exemple gemma3)."));
  }
  if (state.trayWarning) {
    ui.tray.append(el("div", "tray-warning", state.trayWarning));
    state.trayWarning = null;
  }
  ui.tray.hidden = !ui.tray.children.length;
}

function autosize() {
  ui.input.style.height = "auto";
  ui.input.style.height = `${Math.min(ui.input.scrollHeight, 220)}px`;
}

// ---------- Conversations ----------

async function loadConversations() {
  try {
    state.conversations = await api("/api/conversations");
  } catch {
    return;
  }
  renderConversations();
}

function renderConversations() {
  ui.conversations.replaceChildren();
  if (!state.conversations.length) {
    ui.conversations.append(el("p", "conversations-empty", "Tes conversations apparaîtront ici."));
    return;
  }
  for (const conversation of state.conversations) {
    const item = el("div", conversation.id === state.conversationId ? "conversation active" : "conversation");
    const open = el("button", "conversation-open", conversation.title);
    open.type = "button";
    open.title = conversation.title;
    open.addEventListener("click", () => openConversation(conversation.id));
    const remove = el("button", "conversation-delete", "×");
    remove.type = "button";
    remove.title = "Supprimer";
    remove.setAttribute("aria-label", `Supprimer « ${conversation.title} »`);
    remove.addEventListener("click", () => deleteConversation(conversation));
    item.append(open, remove);
    ui.conversations.append(item);
  }
}

async function openConversation(id) {
  stop();
  let data;
  try {
    data = await api(`/api/conversations/${id}`);
  } catch (error) {
    if (id === saved.get("conversation", null)) saved.set("conversation", null);
    return;
  }
  state.conversationId = id;
  saved.set("conversation", id);
  ui.thread.replaceChildren();
  showThread();
  renderConversationItems(data.messages);
  renderConversations();
  closeSidebar();
  scrollToBottom(true);
}

function newConversation() {
  stop();
  state.conversationId = null;
  saved.set("conversation", null);
  ui.thread.replaceChildren();
  ui.welcome.hidden = false;
  renderConversations();
  closeSidebar();
  ui.input.focus();
}

async function deleteConversation(conversation) {
  if (!confirm(`Supprimer la conversation « ${conversation.title} » ?`)) return;
  try {
    await api(`/api/conversations/${conversation.id}`, { method: "DELETE" });
  } catch (error) {
    alert(networkMessage(error));
    return;
  }
  if (conversation.id === state.conversationId) newConversation();
  loadConversations();
}

function closeSidebar() {
  ui.sidebar.classList.remove("open");
  ui.backdrop.classList.remove("open");
}

// ---------- Modèles ----------

const SUGGESTED_MODELS = [
  { name: "qwen3:4b", size: "2,5 Go", text: "Léger et rapide. Pour un ordinateur modeste (8 Go de mémoire vive)." },
  { name: "qwen3:8b", size: "5,2 Go", text: "Le bon équilibre, recommandé. 16 Go de mémoire vive, ou une carte graphique de 8 Go." },
  { name: "qwen3:14b", size: "9,3 Go", text: "Plus malin. Carte graphique de 12 Go, ou Mac avec 16 Go." },
  { name: "gpt-oss:20b", size: "14 Go", text: "Excellent pour raisonner. Carte graphique de 16 Go, ou Mac avec 24 Go." },
  { name: "qwen3:30b", size: "19 Go", text: "Le plus puissant de la liste, et rapide. Carte graphique de 24 Go, ou Mac avec 32 Go." },
  { name: "gemma3:12b", size: "8,1 Go", text: "Sait regarder les images (photos, captures d'écran), mais n'utilise pas d'outils." },
];

const CAPABILITY_BADGES = { tools: "outils", thinking: "réflexion", vision: "images" };

function currentModel() {
  return state.models.find((model) => model.name === ui.modelSelect.value);
}

function setStatus(kind, text) {
  ui.status.className = `status ${kind}`;
  ui.status.textContent = text;
}

function showBanner(message, retry) {
  ui.banner.replaceChildren(el("p", "", message));
  if (retry) {
    const button = el("button", "btn small", "Réessayer");
    button.type = "button";
    button.addEventListener("click", retry);
    ui.banner.append(button);
  }
  ui.banner.hidden = false;
}

async function loadModels() {
  let data;
  try {
    data = await api("/api/modeles");
  } catch (error) {
    data = { ok: false, error: networkMessage(error), models: [], default: null };
  }
  state.models = data.models;
  state.defaultModel = data.default;
  if (data.ok) {
    setStatus("ok", "Ollama connecté");
    ui.banner.hidden = true;
  } else {
    setStatus("error", "Ollama introuvable");
    showBanner(data.error, loadModels);
  }
  renderModelSelect();
  if (data.ok && !data.models.length) {
    openModels("Aucun modèle n'est installé pour l'instant. Choisis-en un ci-dessous pour donner un cerveau à ton IA (le téléchargement peut prendre quelques minutes).");
  }
}

function renderModelSelect() {
  ui.modelSelect.replaceChildren();
  ui.modelSelect.disabled = !state.models.length;
  if (!state.models.length) {
    const option = el("option", "", "Aucun modèle");
    option.value = "";
    ui.modelSelect.append(option);
  }
  for (const model of state.models) {
    const option = el("option", "", model.parameters ? `${model.name} · ${model.parameters}` : model.name);
    option.value = model.name;
    ui.modelSelect.append(option);
  }
  const preferred = saved.get("model", null);
  if (state.models.some((model) => model.name === preferred)) ui.modelSelect.value = preferred;
  else if (state.defaultModel && state.models.some((model) => model.name === state.defaultModel)) ui.modelSelect.value = state.defaultModel;
  updateCapabilities();
}

function updateCapabilities() {
  const capabilities = currentModel()?.capabilities;
  const canThink = !capabilities || capabilities.includes("thinking");
  ui.thinking.disabled = !canThink;
  ui.thinkingLabel.classList.toggle("disabled", !canThink);
  ui.thinkingText.textContent = canThink ? "Réflexion approfondie" : "Réflexion approfondie (indisponible avec ce modèle)";
  renderTray();
}

function modelCard({ name, description, badges = [], action, current = false }) {
  const card = el("div", current ? "model-card current" : "model-card");
  const info = el("div", "model-info");
  info.append(el("span", "model-name", name));
  if (description) info.append(el("span", "model-desc", description));
  if (badges.length) {
    const box = el("div", "badges");
    for (const badge of badges) box.append(el("span", "badge", badge));
    info.append(box);
  }
  card.append(info);
  if (action) card.append(action);
  return card;
}

function renderModelLists() {
  const installed = $("#installed-models");
  installed.replaceChildren();
  if (!state.models.length) installed.append(el("p", "empty", "Aucun modèle installé pour l'instant."));
  for (const model of state.models) {
    const current = model.name === ui.modelSelect.value;
    const button = el("button", "btn small", current ? "Utilisé" : "Utiliser");
    button.type = "button";
    button.disabled = current;
    button.addEventListener("click", () => {
      ui.modelSelect.value = model.name;
      saved.set("model", model.name);
      updateCapabilities();
      renderModelLists();
    });
    const description = [formatSize(model.size), model.parameters && `${model.parameters} de paramètres`].filter(Boolean).join(" · ");
    const badges = (model.capabilities || []).map((capability) => CAPABILITY_BADGES[capability]).filter(Boolean);
    installed.append(modelCard({ name: model.name, description, badges, action: button, current }));
  }

  const suggested = $("#suggested-models");
  suggested.replaceChildren();
  const installedNames = new Set(state.models.map((model) => model.name));
  for (const model of SUGGESTED_MODELS.filter((item) => !installedNames.has(item.name))) {
    const button = el("button", "btn small primary pull-button", "Télécharger");
    button.type = "button";
    button.disabled = state.pulling;
    button.addEventListener("click", () => pullModel(model.name));
    suggested.append(modelCard({ name: model.name, description: `${model.size} · ${model.text}`, action: button }));
  }
  if (!suggested.children.length) suggested.append(el("p", "empty", "Tu as déjà tous les modèles suggérés !"));
}

function openModels(intro) {
  $("#models-intro").textContent =
    intro ||
    "Le modèle, c'est le « cerveau » de ton IA. Plus il est gros, plus il est intelligent… et plus il demande de mémoire. Tout est gratuit et tourne en local.";
  renderModelLists();
  const dialog = $("#models-dialog");
  if (!dialog.open) dialog.showModal();
}

function translatePullStatus(status) {
  if (status.startsWith("pulling manifest")) return "Préparation…";
  if (status.startsWith("pulling")) return "Téléchargement…";
  if (status.startsWith("verifying")) return "Vérification…";
  if (status.startsWith("writing") || status.startsWith("removing")) return "Finalisation…";
  if (status === "success") return "Terminé !";
  return status;
}

async function pullModel(name) {
  name = name.trim();
  if (!name || state.pulling) return;
  state.pulling = true;
  for (const button of document.querySelectorAll(".pull-button, #pull-custom")) button.disabled = true;
  const progress = $("#pull-progress");
  const status = $("#pull-status");
  const bar = $("#pull-bar");
  progress.hidden = false;
  progress.scrollIntoView({ block: "nearest", behavior: "smooth" });
  bar.style.width = "0";
  status.textContent = `${name} : préparation…`;
  try {
    const response = await fetch("/api/modeles/telecharger", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: name }),
    });
    if (!response.ok) throw new Error(await errorMessage(response));
    let failure = null;
    await readEvents(response, (event) => {
      if (event.type === "progress") {
        const sizes = event.total ? ` ${formatSize(event.completed) || "0 Mo"} / ${formatSize(event.total)}` : "";
        status.textContent = `${name} : ${translatePullStatus(event.status)}${sizes}`;
        if (event.total) bar.style.width = `${Math.round((event.completed / event.total) * 100)}%`;
      } else if (event.type === "error") {
        failure = event.message;
      }
    });
    if (failure) throw new Error(failure);
    saved.set("model", name);
    await loadModels();
    bar.style.width = "100%";
    status.textContent = `✅ ${name} est installé ! Tu peux commencer à discuter.`;
  } catch (error) {
    status.textContent = `❌ ${networkMessage(error)}`;
  } finally {
    state.pulling = false;
    renderModelLists();
    $("#pull-custom").disabled = false;
  }
}

// ---------- Nom, personnalité et mémoire ----------

function applyName(name) {
  state.name = name;
  document.title = name;
  $("#brand-name").textContent = name;
  $("#welcome-name").textContent = name;
}

async function openProfile() {
  try {
    const data = await api("/api/profil");
    $("#profile-name").value = data.name;
    $("#profile-personality").value = data.personality;
  } catch (error) {
    alert(networkMessage(error));
    return;
  }
  $("#profile-error").hidden = true;
  $("#profile-dialog").showModal();
}

async function saveProfile() {
  const error = $("#profile-error");
  try {
    const data = await api("/api/profil", {
      method: "PUT",
      body: JSON.stringify({ name: $("#profile-name").value, personality: $("#profile-personality").value }),
    });
    applyName(data.name);
    $("#profile-dialog").close();
  } catch (failure) {
    error.textContent = networkMessage(failure);
    error.hidden = false;
  }
}

async function openMemory() {
  try {
    const data = await api("/api/memoire");
    $("#memory-text").value = data.text;
  } catch (error) {
    alert(networkMessage(error));
    return;
  }
  $("#memory-dialog").showModal();
}

async function saveMemory() {
  try {
    await api("/api/memoire", { method: "PUT", body: JSON.stringify({ text: $("#memory-text").value }) });
    $("#memory-dialog").close();
  } catch (error) {
    alert(networkMessage(error));
  }
}

// ---------- Branchements ----------

ui.composer.addEventListener("submit", (event) => {
  event.preventDefault();
  if (state.streaming) stop();
  else send();
});

ui.input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    if (!state.streaming) send();
  }
});
ui.input.addEventListener("input", autosize);
ui.input.addEventListener("paste", (event) => {
  const files = Array.from(event.clipboardData?.files || []);
  if (files.length) addFiles(files);
});

$("#attach").addEventListener("click", () => ui.fileInput.click());
ui.fileInput.addEventListener("change", () => {
  addFiles(Array.from(ui.fileInput.files));
  ui.fileInput.value = "";
});

let dragDepth = 0;
const hasFiles = (event) => Array.from(event.dataTransfer?.types || []).includes("Files");
window.addEventListener("dragenter", (event) => {
  if (!hasFiles(event)) return;
  event.preventDefault();
  dragDepth += 1;
  ui.dropZone.hidden = false;
});
window.addEventListener("dragleave", () => {
  dragDepth = Math.max(0, dragDepth - 1);
  if (!dragDepth) ui.dropZone.hidden = true;
});
window.addEventListener("dragover", (event) => {
  if (hasFiles(event)) event.preventDefault();
});
window.addEventListener("drop", (event) => {
  if (!hasFiles(event)) return;
  event.preventDefault();
  dragDepth = 0;
  ui.dropZone.hidden = true;
  addFiles(Array.from(event.dataTransfer.files));
});

for (const suggestion of document.querySelectorAll(".suggestion")) {
  suggestion.addEventListener("click", () => send(suggestion.textContent));
}

ui.modelSelect.addEventListener("change", () => {
  saved.set("model", ui.modelSelect.value);
  updateCapabilities();
});
ui.thinking.addEventListener("change", () => saved.set("thinking", ui.thinking.checked));

$("#new-chat").addEventListener("click", newConversation);
$("#toggle-sidebar").addEventListener("click", () => {
  ui.sidebar.classList.add("open");
  ui.backdrop.classList.add("open");
});
ui.backdrop.addEventListener("click", closeSidebar);
$("#open-profile").addEventListener("click", openProfile);
$("#open-memory").addEventListener("click", openMemory);
$("#open-models").addEventListener("click", () => openModels());
$("#pull-custom").addEventListener("click", () => pullModel($("#pull-name").value));
$("#pull-name").addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    pullModel($("#pull-name").value);
  }
});

$("#profile-save").addEventListener("click", (event) => {
  event.preventDefault();
  saveProfile();
});
$("#memory-save").addEventListener("click", (event) => {
  event.preventDefault();
  saveMemory();
});

async function init() {
  try {
    const infos = await api("/api/infos");
    applyName(infos.name);
    ui.thinking.checked = saved.get("thinking", infos.thinking);
  } catch (error) {
    setStatus("error", "Serveur injoignable");
    showBanner(networkMessage(error), () => location.reload());
    return;
  }
  await Promise.all([loadModels(), loadConversations()]);
  const last = saved.get("conversation", null);
  if (last && state.conversations.some((conversation) => conversation.id === last)) await openConversation(last);
  ui.input.focus();
}

init();
