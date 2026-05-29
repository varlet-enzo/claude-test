/* ============================================================
   MAISON BONBON — Chrome partagé (header, footer, globaux)
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
    { href: "studio.html", label: "La Maison" },
    { href: "games.html", label: "La Carte" },
    { href: "teams.html", label: "Nos Ateliers", dropdown: deptMenu },
    { href: "careers.html", label: "Recrutement" },
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
      <span class="nav__mark"></span>Bonbon<span class="nav__brand-sub">PÂTISSERIE</span>
    </a>
    <nav class="nav__links" aria-label="Navigation principale">${navLinks}</nav>
    <a href="contact.html" class="btn btn--ghost nav__cta" data-cursor>
      Commander
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
    </a>
    <button class="nav__burger" id="burger" aria-label="Menu"><span></span><span></span><span></span></button>
  `;

  const footer = `
    <div class="footer__top">
      <div class="footer__brand">
        <span class="nav__mark"></span> Bonbon <em>PÂTISSERIE</em>
        <p>Des douceurs faites maison, chaque jour, avec amour.</p>
      </div>
      <div class="footer__cols">
        <div>
          <h4>La Maison</h4>
          <a href="studio.html" data-cursor>Notre histoire</a>
          <a href="teams.html" data-cursor>Nos ateliers</a>
          <a href="careers.html" data-cursor>Recrutement</a>
          <a href="news.html" data-cursor>Actualités</a>
        </div>
        <div>
          <h4>La Carte</h4>
          <a href="games.html" data-cursor>Toutes nos pâtisseries</a>
          <a href="game.html?id=macaron-framboise" data-cursor>Macaron Framboise</a>
          <a href="game.html?id=paris-brest" data-cursor>Paris-Brest</a>
          <a href="game.html?id=tarte-citron" data-cursor>Tarte au Citron</a>
        </div>
        <div>
          <h4>Nous suivre</h4>
          <a href="#" data-cursor>Instagram</a>
          <a href="#" data-cursor>Facebook</a>
          <a href="#" data-cursor>Pinterest</a>
          <a href="contact.html" data-cursor>Contact</a>
        </div>
      </div>
    </div>
    <div class="footer__bottom">
      <p>© ${new Date().getFullYear()} Maison Bonbon. Maison et produits fictifs — projet de démonstration.</p>
      <p>Fait maison, avec gourmandise. 🍓</p>
    </div>
  `;

  // --- Chrome global (loader, curseur, canvas, progress) ---
  const chrome = document.createElement("div");
  chrome.innerHTML = `
    <div class="loader" id="loader" aria-hidden="true">
      <div class="loader__logo">Bonbon</div>
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
