/* ============================================================
   MAISON BONBON — Système de commentaires
   ------------------------------------------------------------
   Stockage actuel : localStorage (démo, sans serveur).
   La couche "CommentStore" est volontairement ASYNCHRONE :
   pour brancher un vrai backend plus tard, il suffit de
   remplacer le corps de list/add/like/remove par des appels
   fetch() vers votre API — l'UI n'a pas besoin de changer.
   ============================================================ */
(() => {
  "use strict";

  const STORAGE_KEY = "aether_comments_v1";
  const OWNED_KEY = "aether_comments_owned_v1";
  const LIKED_KEY = "aether_comments_liked_v1";

  /* ---------- Helpers stockage ---------- */
  const readAll = () => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; }
    catch { return {}; }
  };
  const writeAll = (data) => localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  const readSet = (key) => {
    try { return new Set(JSON.parse(localStorage.getItem(key)) || []); }
    catch { return new Set(); }
  };
  const writeSet = (key, set) => localStorage.setItem(key, JSON.stringify([...set]));

  /* ============================================================
     CommentStore — couche d'accès aux données (REMPLAÇABLE)
     ============================================================
     👉 Pour un backend réel, remplacez chaque méthode par, ex. :
        list:   () => fetch(`/api/threads/${threadId}/comments`).then(r=>r.json())
        add:    (t,c) => fetch(`/api/threads/${t}/comments`, {method:'POST', body:...})
        like:   (t,id) => fetch(`/api/comments/${id}/like`, {method:'POST'})
        remove: (t,id) => fetch(`/api/comments/${id}`, {method:'DELETE'})
  */
  const CommentStore = {
    async list(threadId) {
      const all = readAll();
      return (all[threadId] || []).slice().sort((a, b) => b.ts - a.ts);
    },
    async add(threadId, { name, text }) {
      const all = readAll();
      const comment = {
        id: "c_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
        name: name.slice(0, 40),
        text: text.slice(0, 1000),
        ts: Date.now(),
        likes: 0,
      };
      (all[threadId] = all[threadId] || []).push(comment);
      writeAll(all);
      const owned = readSet(OWNED_KEY); owned.add(comment.id); writeSet(OWNED_KEY, owned);
      return comment;
    },
    async like(threadId, id) {
      const all = readAll();
      const list = all[threadId] || [];
      const c = list.find((x) => x.id === id);
      if (!c) return;
      const liked = readSet(LIKED_KEY);
      if (liked.has(id)) { c.likes = Math.max(0, c.likes - 1); liked.delete(id); }
      else { c.likes++; liked.add(id); }
      writeAll(all); writeSet(LIKED_KEY, liked);
      return c;
    },
    async remove(threadId, id) {
      const all = readAll();
      all[threadId] = (all[threadId] || []).filter((x) => x.id !== id);
      writeAll(all);
      const owned = readSet(OWNED_KEY); owned.delete(id); writeSet(OWNED_KEY, owned);
    },
    isOwn: (id) => readSet(OWNED_KEY).has(id),
    isLiked: (id) => readSet(LIKED_KEY).has(id),
  };

  /* ---------- Utilitaires UI ---------- */
  const escape = (s) =>
    String(s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  const relTime = (ts) => {
    const diff = (Date.now() - ts) / 1000;
    if (diff < 60) return "à l'instant";
    if (diff < 3600) return `il y a ${Math.floor(diff / 60)} min`;
    if (diff < 86400) return `il y a ${Math.floor(diff / 3600)} h`;
    if (diff < 604800) return `il y a ${Math.floor(diff / 86400)} j`;
    return new Date(ts).toLocaleDateString("fr-FR");
  };

  const initials = (name) =>
    name.trim().split(/\s+/).slice(0, 2).map((w) => w[0] || "").join("").toUpperCase() || "?";

  const avatarHue = (name) => {
    let h = 0; for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) % 360;
    return h;
  };

  /* ---------- Composant ---------- */
  async function mount(container, threadId) {
    if (!container) return;
    container.classList.add("comments");
    container.innerHTML = `
      <div class="comments__head">
        <h3 class="comments__title">Avis gourmands <span class="comments__count" id="cmtCount">0</span></h3>
        <p class="comments__note">🍓 Démo locale : vos avis sont enregistrés dans ce navigateur. Régalez-vous et restez bienveillant !</p>
      </div>
      <form class="comments__form" id="cmtForm">
        <div class="comments__row">
          <input type="text" id="cmtName" maxlength="40" placeholder="Votre prénom" aria-label="Prénom" required />
        </div>
        <textarea id="cmtText" maxlength="1000" rows="3" placeholder="Partagez votre avis sur cette pâtisserie…" aria-label="Avis" required></textarea>
        <div class="comments__actions">
          <span class="comments__hint" id="cmtHint">0 / 1000</span>
          <button type="submit" class="btn btn--primary" data-cursor data-magnetic><span>Publier</span></button>
        </div>
      </form>
      <div class="comments__list" id="cmtList" aria-live="polite"></div>
    `;

    const listEl = container.querySelector("#cmtList");
    const countEl = container.querySelector("#cmtCount");
    const form = container.querySelector("#cmtForm");
    const nameI = container.querySelector("#cmtName");
    const textI = container.querySelector("#cmtText");
    const hint = container.querySelector("#cmtHint");

    // pseudo mémorisé
    const savedName = localStorage.getItem("aether_cmt_name");
    if (savedName) nameI.value = savedName;

    textI.addEventListener("input", () => { hint.textContent = `${textI.value.length} / 1000`; });

    async function render() {
      const items = await CommentStore.list(threadId);
      countEl.textContent = items.length;
      if (!items.length) {
        listEl.innerHTML = `<p class="comments__empty">Aucun avis pour l'instant. Soyez le premier à vous régaler ! 🧁</p>`;
        return;
      }
      listEl.innerHTML = items
        .map((c) => {
          const own = CommentStore.isOwn(c.id);
          const liked = CommentStore.isLiked(c.id);
          return `
          <article class="comment" data-id="${c.id}">
            <div class="comment__avatar" style="--hue:${avatarHue(c.name)}">${escape(initials(c.name))}</div>
            <div class="comment__body">
              <header class="comment__meta">
                <strong>${escape(c.name)}</strong>
                <span>${relTime(c.ts)}</span>
                ${own ? '<span class="comment__tag">vous</span>' : ""}
              </header>
              <p class="comment__text">${escape(c.text)}</p>
              <footer class="comment__foot">
                <button class="comment__like${liked ? " is-liked" : ""}" data-act="like" data-cursor>
                  ♥ <span>${c.likes}</span>
                </button>
                ${own ? '<button class="comment__del" data-act="del" data-cursor>Supprimer</button>' : ""}
              </footer>
            </div>
          </article>`;
        })
        .join("");
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = nameI.value.trim();
      const text = textI.value.trim();
      if (!name || !text) return;
      localStorage.setItem("aether_cmt_name", name);
      await CommentStore.add(threadId, { name, text });
      textI.value = ""; hint.textContent = "0 / 1000";
      await render();
      window.AETHER && window.AETHER.flash("🧁 Merci pour votre avis !");
    });

    listEl.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-act]");
      if (!btn) return;
      const art = btn.closest(".comment");
      const id = art.getAttribute("data-id");
      if (btn.dataset.act === "like") { await CommentStore.like(threadId, id); await render(); }
      if (btn.dataset.act === "del") {
        if (confirm("Supprimer ce commentaire ?")) { await CommentStore.remove(threadId, id); await render(); }
      }
    });

    await render();
  }

  window.CommentSystem = { mount, store: CommentStore };
})();
