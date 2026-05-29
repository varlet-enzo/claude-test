/* ============================================================
   AETHERION STUDIOS — Accueil : jeux phares + secteurs
   ============================================================ */
(() => {
  "use strict";

  /* Jeux mis en avant */
  const grid = document.getElementById("homeGames");
  if (grid && window.GAMES) {
    const featured = [
      window.GAMES.find((g) => g.flagship),
      ...window.GAMES.filter((g) => !g.flagship && g.rating >= 9).slice(0, 5),
    ].filter(Boolean).slice(0, 6);

    grid.innerHTML = featured
      .map(
        (g) => `
      <a class="game-card reveal" href="game.html?id=${g.id}" data-cursor data-tilt style="--hue:${g.hue}">
        <div class="game-card__media">
          ${g.flagship ? '<span class="game-card__flag">Phare</span>' : ""}
          ${g.rating > 0 ? `<span class="game-card__status game-card__status--sorti">★ ${g.rating.toFixed(1)}</span>` : ""}
        </div>
        <div class="game-card__body">
          <div class="game-card__top"><h3>${g.title}</h3></div>
          <div class="game-card__genres">${g.genres.map((x) => `<span>${x}</span>`).join("")}</div>
          <p class="game-card__syn">${g.tagline}</p>
        </div>
      </a>`
      )
      .join("");
  }

  /* Secteurs */
  const sec = document.getElementById("homeSectors");
  if (sec && window.DEPARTMENTS) {
    sec.innerHTML = window.DEPARTMENT_ORDER.map((slug) => {
      const d = window.DEPARTMENTS[slug];
      return `
      <a class="team-card reveal" href="secteur.html?dept=${d.slug}" data-cursor data-tilt style="--hue:${d.hue}">
        <div class="team-card__icon">${d.icon}</div>
        <h3>${d.name}</h3>
        <p>${d.tagline}</p>
        <span class="team-card__count">${d.profiles.length} membres</span>
      </a>`;
    }).join("");
  }

  window.AETHER && window.AETHER.refresh(document);
})();
