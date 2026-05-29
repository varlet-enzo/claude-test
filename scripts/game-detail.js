/* ============================================================
   MAISON BONBON — Fiche de jeu détaillée + commentaires
   ============================================================ */
(() => {
  "use strict";
  const root = document.getElementById("gameDetail");
  if (!root || !window.GAMES) return;

  const params = new URLSearchParams(location.search);
  const id = params.get("id") || "macaron-framboise";
  const game = window.GAMES.find((g) => g.id === id) || window.GAMES[0];

  document.title = `${game.title} — Maison Bonbon`;

  const related = window.GAMES
    .filter((g) => g.id !== game.id && g.genres.some((x) => game.genres.includes(x)))
    .slice(0, 3);

  const ratingBlock =
    game.rating > 0
      ? `<div class="gd-stat"><strong>★ ${game.rating.toFixed(1)}</strong><span>Note gourmande</span></div>`
      : `<div class="gd-stat"><strong>—</strong><span>À déguster</span></div>`;

  root.innerHTML = `
    <div class="gd-hero" style="--hue:${game.hue}">
      <div class="gd-hero__art"></div>
      <div class="gd-hero__overlay"></div>
      <div class="gd-hero__content">
        <a href="games.html" class="gd-back" data-cursor>← Toute la carte</a>
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
          <h2 class="gd-h2">La gourmandise</h2>
          <p class="gd-syn">${game.synopsis}</p>
        </section>
        <section class="gd-section reveal">
          <h2 class="gd-h2">En détail</h2>
          <ul class="gd-features">
            <li><span>Catégorie</span><strong>${game.genres.join(", ")}</strong></li>
            <li><span>Saveurs</span><strong>${game.platforms.join(", ")}</strong></li>
            <li><span>Prix</span><strong>${game.price}</strong></li>
            <li><span>Disponibilité</span><strong>${game.status}</strong></li>
            <li><span>Maison</span><strong>Maison Bonbon</strong></li>
          </ul>
        </section>
        <div class="gd-cta reveal">
          <a href="#comments" class="btn btn--ghost" data-cursor data-magnetic><span>Lire les avis</span></a>
          <button class="btn btn--play" data-cursor data-magnetic><span class="btn__play-icon">▶</span> Voir la recette en vidéo</button>
        </div>
      </div>

      <aside class="gd-aside">
        <div class="gd-card reveal">
          ${ratingBlock}
          <div class="gd-stat"><strong>${game.price}</strong><span>La pièce</span></div>
          <div class="gd-stat"><strong>${game.platforms.length}</strong><span>Saveurs</span></div>
        </div>
        <div class="gd-buy reveal" style="--d:.1s">
          <p class="gd-buy__label">${game.status === "Sur commande" ? "Sur mesure" : "À la pièce"}</p>
          <p class="gd-buy__price">${game.price}</p>
          <button class="btn btn--primary" data-cursor data-magnetic><span>${game.status === "Sur commande" ? "Demander un devis" : "Commander"}</span></button>
          <p class="gd-buy__note">Produit fictif — démonstration.</p>
        </div>
      </aside>
    </div>

    ${
      related.length
        ? `<section class="gd-related">
            <h2 class="section-head__title reveal">À déguster aussi</h2>
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
