/* ============================================================
   AETHERION STUDIOS — Fiche de jeu détaillée + commentaires
   ============================================================ */
(() => {
  "use strict";
  const root = document.getElementById("gameDetail");
  if (!root || !window.GAMES) return;

  const params = new URLSearchParams(location.search);
  const id = params.get("id") || "aetherion";
  const game = window.GAMES.find((g) => g.id === id) || window.GAMES[0];

  document.title = `${game.title} — Aetherion Studios`;

  const related = window.GAMES
    .filter((g) => g.id !== game.id && g.genres.some((x) => game.genres.includes(x)))
    .slice(0, 3);

  const ratingBlock =
    game.rating > 0
      ? `<div class="gd-stat"><strong>★ ${game.rating.toFixed(1)}</strong><span>Note critique</span></div>`
      : `<div class="gd-stat"><strong>—</strong><span>Bientôt noté</span></div>`;

  root.innerHTML = `
    <div class="gd-hero" style="--hue:${game.hue}">
      <div class="gd-hero__art"></div>
      <div class="gd-hero__overlay"></div>
      <div class="gd-hero__content">
        <a href="games.html" class="gd-back" data-cursor>← Tous les jeux</a>
        <div class="gd-genres">${game.genres.map((x) => `<span class="chip chip--sm">${x}</span>`).join("")}</div>
        <h1 class="gd-title reveal">${game.title}</h1>
        <p class="gd-tagline reveal" style="--d:.1s">${game.tagline}</p>
        <div class="gd-meta reveal" style="--d:.2s">
          <span class="gd-badge gd-badge--${statusSlug(game.status)}">${game.status}</span>
          <span>${game.year}</span>
          <span>${game.platforms.join(" · ")}</span>
        </div>
      </div>
    </div>

    <div class="gd-body">
      <div class="gd-main">
        <section class="gd-section reveal">
          <h2 class="gd-h2">Synopsis</h2>
          <p class="gd-syn">${game.synopsis}</p>
        </section>
        <section class="gd-section reveal">
          <h2 class="gd-h2">Caractéristiques</h2>
          <ul class="gd-features">
            <li><span>Genre</span><strong>${game.genres.join(", ")}</strong></li>
            <li><span>Sortie</span><strong>${game.year}</strong></li>
            <li><span>Plateformes</span><strong>${game.platforms.join(", ")}</strong></li>
            <li><span>Statut</span><strong>${game.status}</strong></li>
            <li><span>Studio</span><strong>Aetherion Studios</strong></li>
          </ul>
        </section>
        <div class="gd-cta reveal">
          <a href="#comments" class="btn btn--ghost" data-cursor data-magnetic><span>Lire les avis</span></a>
          <button class="btn btn--play" data-cursor data-magnetic><span class="btn__play-icon">▶</span> Voir le trailer</button>
        </div>
      </div>

      <aside class="gd-aside">
        <div class="gd-card reveal">
          ${ratingBlock}
          <div class="gd-stat"><strong>${game.year}</strong><span>Année</span></div>
          <div class="gd-stat"><strong>${game.platforms.length}</strong><span>Plateformes</span></div>
        </div>
        <div class="gd-buy reveal" style="--d:.1s">
          <p class="gd-buy__label">Édition standard</p>
          <p class="gd-buy__price">${game.status === "À venir" ? "59,99 € — Précommande" : game.status === "Bêta" ? "Accès bêta gratuit" : "39,99 €"}</p>
          <button class="btn btn--primary" data-cursor data-magnetic><span>${game.status === "À venir" ? "Précommander" : game.status === "Bêta" ? "Rejoindre la bêta" : "Acheter"}</span></button>
          <p class="gd-buy__note">Jeu fictif — démonstration.</p>
        </div>
      </aside>
    </div>

    ${
      related.length
        ? `<section class="gd-related">
            <h2 class="section-head__title reveal">Dans le même genre</h2>
            <div class="gd-related__grid">
              ${related
                .map(
                  (g) => `
                <a class="game-card reveal" href="game.html?id=${g.id}" data-cursor data-tilt style="--hue:${g.hue}">
                  <div class="game-card__media"></div>
                  <div class="game-card__body">
                    <div class="game-card__top"><h3>${g.title}</h3>${g.rating > 0 ? `<span class="game-card__rating">★ ${g.rating.toFixed(1)}</span>` : ""}</div>
                    <div class="game-card__genres">${g.genres.map((x) => `<span>${x}</span>`).join("")}</div>
                    <p class="game-card__syn">${g.tagline}</p>
                  </div>
                </a>`
                )
                .join("")}
            </div>
          </section>`
        : ""
    }

    <section class="gd-comments" id="comments">
      <div id="commentRoot"></div>
    </section>
  `;

  function statusSlug(s) {
    return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z]/g, "");
  }

  // commentaires (un fil par jeu)
  if (window.CommentSystem) {
    window.CommentSystem.mount(document.getElementById("commentRoot"), "game:" + game.id);
  }

  window.AETHER && window.AETHER.refresh(root);
})();
