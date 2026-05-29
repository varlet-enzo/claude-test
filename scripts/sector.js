/* ============================================================
   MAISON BONBON — Page secteur (?dept=slug) + profils
   ============================================================ */
(() => {
  "use strict";
  const root = document.getElementById("sectorRoot");
  if (!root || !window.DEPARTMENTS) return;

  const params = new URLSearchParams(location.search);
  const slug = params.get("dept") || window.DEPARTMENT_ORDER[0];
  const dept = window.DEPARTMENTS[slug] || window.DEPARTMENTS[window.DEPARTMENT_ORDER[0]];

  document.title = `${dept.name} — Maison Bonbon`;

  const others = window.DEPARTMENT_ORDER.filter((s) => s !== dept.slug).map((s) => window.DEPARTMENTS[s]);

  root.innerHTML = `
    <section class="sector-hero" style="--hue:${dept.hue}">
      <div class="sector-hero__glow"></div>
      <a href="teams.html" class="gd-back reveal" data-cursor>← Tous nos ateliers</a>
      <span class="sector-hero__icon reveal" style="--d:.05s">${dept.icon}</span>
      <h1 class="sector-hero__title reveal" style="--d:.1s">${dept.name}</h1>
      <p class="sector-hero__tagline reveal" style="--d:.2s">${dept.tagline}</p>
    </section>

    <section class="sector-mission">
      <div class="sector-mission__grid">
        <div class="reveal">
          <h2 class="gd-h2">Notre mission</h2>
          <p class="sector-mission__text">${dept.mission}</p>
        </div>
        <div class="reveal" style="--d:.1s">
          <h3 class="sector-focus__title">Domaines</h3>
          <ul class="sector-focus">
            ${dept.focus.map((f) => `<li>${f}</li>`).join("")}
          </ul>
        </div>
      </div>
      <div class="sector-stack reveal">
        <h3 class="sector-focus__title">Savoir-faire & matériel</h3>
        <div class="sector-stack__chips">
          ${dept.stack.map((t) => `<span class="chip chip--sm">${t}</span>`).join("")}
        </div>
      </div>
    </section>

    <section class="sector-team">
      <div class="section-head">
        <p class="section-head__tag reveal">L'équipe</p>
        <h2 class="section-head__title reveal" style="--d:.1s">Les artisans de l'atelier</h2>
      </div>
      <div class="profiles">
        ${dept.profiles
          .map(
            (p, i) => `
          <article class="profile reveal" style="--d:${i * 0.07}s" data-cursor data-tilt>
            <div class="profile__avatar" style="--hue:${avatarHue(p.name)}">${initials(p.name)}</div>
            <h3 class="profile__name">${p.name}</h3>
            <p class="profile__role">${p.role}</p>
            <p class="profile__years">${p.years} ans de métier</p>
            <p class="profile__bio">${p.bio}</p>
            <div class="profile__skills">${p.skills.map((s) => `<span>${s}</span>`).join("")}</div>
          </article>`
          )
          .join("")}
      </div>
    </section>

    <section class="sector-others">
      <h2 class="section-head__title reveal">Explorer les autres ateliers</h2>
      <div class="sector-others__grid">
        ${others
          .map(
            (d) => `
          <a class="sector-link reveal" href="secteur.html?dept=${d.slug}" data-cursor data-tilt style="--hue:${d.hue}">
            <span class="sector-link__icon">${d.icon}</span>
            <span class="sector-link__name">${d.name}</span>
            <span class="sector-link__arrow">→</span>
          </a>`
          )
          .join("")}
      </div>
    </section>
  `;

  function initials(name) {
    return name.trim().split(/\s+/).slice(0, 2).map((w) => w[0] || "").join("").toUpperCase();
  }
  function avatarHue(name) {
    let h = 0; for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) % 360;
    return h;
  }

  window.AETHER && window.AETHER.refresh(root);
})();
