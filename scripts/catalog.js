/* ============================================================
   MAISON BONBON — Carte des pâtisseries (filtres + recherche)
   ============================================================ */
(() => {
  "use strict";
  const grid = document.getElementById("gamesGrid");
  if (!grid || !window.GAMES) return;

  const games = window.GAMES;
  const genres = [...new Set(games.flatMap((g) => g.genres))].sort();
  const filterBar = document.getElementById("gameFilters");
  const searchInput = document.getElementById("gameSearch");
  const countEl = document.getElementById("gameCount");

  let activeGenre = "Tous";
  let query = "";

  /* chips de genre */
  if (filterBar) {
    filterBar.innerHTML =
      ["Tous", ...genres]
        .map(
          (g) =>
            `<button class="chip${g === "Tous" ? " is-active" : ""}" data-genre="${g}" data-cursor>${g}</button>`
        )
        .join("");
    filterBar.addEventListener("click", (e) => {
      const chip = e.target.closest(".chip");
      if (!chip) return;
      activeGenre = chip.dataset.genre;
      filterBar.querySelectorAll(".chip").forEach((c) => c.classList.toggle("is-active", c === chip));
      render();
    });
  }

  if (searchInput) {
    searchInput.addEventListener("input", () => { query = searchInput.value.toLowerCase().trim(); render(); });
  }

  function card(g) {
    const note = g.rating > 0 ? `<span class="game-card__rating">★ ${g.rating.toFixed(1)}</span>` : "";
    return `
      <a class="game-card reveal" href="game.html?id=${g.id}" data-cursor data-tilt style="--hue:${g.hue}">
        <div class="game-card__media">
          ${g.flagship ? '<span class="game-card__flag">Signature</span>' : ""}
          <span class="game-card__status game-card__status--${slug(g.status)}">${g.status}</span>
        </div>
        <div class="game-card__body">
          <div class="game-card__top">
            <h3>${g.title}</h3>
            ${note}
          </div>
          <div class="game-card__genres">${g.genres.map((x) => `<span>${x}</span>`).join("")}</div>
          <p class="game-card__syn">${g.tagline}</p>
          <span class="game-card__year">${g.price} · ${g.platforms.slice(0, 2).join(", ")}</span>
        </div>
      </a>`;
  }

  function slug(s) {
    return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z]/g, "");
  }

  function render() {
    const filtered = games.filter((g) => {
      const okGenre = activeGenre === "Tous" || g.genres.includes(activeGenre);
      const okQuery =
        !query ||
        g.title.toLowerCase().includes(query) ||
        g.genres.join(" ").toLowerCase().includes(query) ||
        g.tagline.toLowerCase().includes(query);
      return okGenre && okQuery;
    });
    if (countEl) countEl.textContent = filtered.length;
    grid.innerHTML = filtered.length
      ? filtered.map(card).join("")
      : `<p class="games-empty">Aucune pâtisserie ne correspond à votre recherche. 🔍</p>`;
    window.AETHER && window.AETHER.refresh(grid);
  }

  render();
})();
