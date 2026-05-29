/* ============================================================
   AETHERION STUDIOS — Chrome partagé (header, footer, globaux)
   Injecté sur toutes les pages pour une nav cohérente (DRY).
   Doit être chargé AVANT main.js et APRÈS data/team.js.
   ============================================================ */
(() => {
  "use strict";

  const page = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  const isHome = page === "" || page === "index.html";

  const depts =
    window.DEPARTMENT_ORDER && window.DEPARTMENTS
      ? window.DEPARTMENT_ORDER.map((s) => window.DEPARTMENTS[s])
      : [];

  const deptMenu = depts.length
    ? `<div class="nav__dropdown">
         ${depts
           .map(
             (d) =>
               `<a href="secteur.html?dept=${d.slug}" data-cursor><span>${d.icon}</span>${d.name}</a>`
           )
           .join("")}
       </div>`
    : "";

  const links = [
    { href: "studio.html", label: "Studio" },
    { href: "games.html", label: "Jeux" },
    { href: "teams.html", label: "Équipes", dropdown: deptMenu },
    { href: "careers.html", label: "Carrières" },
    { href: "news.html", label: "Actus" },
    { href: "contact.html", label: "Contact" },
  ];

  const isActive = (href) => href.toLowerCase() === page || (href === "teams.html" && page === "secteur.html");

  const navLinks = links
    .map((l) => {
      const active = isActive(l.href) ? " is-active" : "";
      if (l.dropdown) {
        return `<div class="nav__item nav__item--has-menu">
            <a href="${l.href}" class="${active.trim()}" data-cursor>${l.label}</a>
            ${l.dropdown}
          </div>`;
      }
      return `<a href="${l.href}" class="${active.trim()}" data-cursor>${l.label}</a>`;
    })
    .join("");

  const header = `
    <a href="index.html" class="nav__brand" data-cursor>
      <span class="nav__mark"></span>AETHERION<span class="nav__brand-sub">STUDIOS</span>
    </a>
    <nav class="nav__links" aria-label="Navigation principale">${navLinks}</nav>
    <a href="careers.html" class="btn btn--ghost nav__cta" data-cursor>
      Nous rejoindre
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
    </a>
    <button class="nav__burger" id="burger" aria-label="Menu"><span></span><span></span><span></span></button>
  `;

  const footer = `
    <div class="footer__top">
      <div class="footer__brand">
        <span class="nav__mark"></span> AETHERION <em>STUDIOS</em>
        <p>Nous créons des mondes dont on se souvient.</p>
      </div>
      <div class="footer__cols">
        <div>
          <h4>Studio</h4>
          <a href="studio.html" data-cursor>À propos</a>
          <a href="teams.html" data-cursor>Nos équipes</a>
          <a href="careers.html" data-cursor>Carrières</a>
          <a href="news.html" data-cursor>Actualités</a>
        </div>
        <div>
          <h4>Jeux</h4>
          <a href="games.html" data-cursor>Catalogue</a>
          <a href="game.html?id=aetherion" data-cursor>Aetherion</a>
          <a href="game.html?id=mythwright" data-cursor>Mythwright</a>
          <a href="game.html?id=neon-requiem" data-cursor>Neon Requiem</a>
        </div>
        <div>
          <h4>Communauté</h4>
          <a href="#" data-cursor>Discord</a>
          <a href="#" data-cursor>X / Twitter</a>
          <a href="#" data-cursor>YouTube</a>
          <a href="contact.html" data-cursor>Contact</a>
        </div>
      </div>
    </div>
    <div class="footer__bottom">
      <p>© ${new Date().getFullYear()} Aetherion Studios. Univers et jeux fictifs — projet de démonstration.</p>
      <p>Conçu avec passion pour les joueurs.</p>
    </div>
  `;

  // --- Chrome global (loader, curseur, canvas, progress) ---
  const chrome = document.createElement("div");
  chrome.innerHTML = `
    <div class="loader" id="loader" aria-hidden="true">
      <div class="loader__logo">AETHERION</div>
      <div class="loader__bar"><span id="loaderBar"></span></div>
      <div class="loader__pct" id="loaderPct">0%</div>
    </div>
    <div class="cursor" id="cursor" aria-hidden="true"></div>
    <div class="cursor-dot" id="cursorDot" aria-hidden="true"></div>
    <canvas class="bg-canvas" id="bgCanvas" aria-hidden="true"></canvas>
    <div class="scroll-progress" id="scrollProgress" aria-hidden="true"></div>
  `;
  while (chrome.firstChild) document.body.insertBefore(chrome.firstChild, document.body.firstChild);

  // --- Header ---
  const headerEl = document.createElement("header");
  headerEl.className = "nav";
  headerEl.id = "nav";
  headerEl.innerHTML = header;
  // insert after the chrome elements but before main content
  const main = document.querySelector("main");
  document.body.insertBefore(headerEl, main || null);

  // --- Footer ---
  const footerEl = document.createElement("footer");
  footerEl.className = "footer";
  footerEl.innerHTML = footer;
  document.body.appendChild(footerEl);
})();
