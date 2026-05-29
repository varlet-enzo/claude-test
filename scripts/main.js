/* ============================================================
   AETHERION STUDIOS — interactions globales (multi-pages)
   Expose window.AETHER.refresh() pour le contenu dynamique.
   ============================================================ */
(() => {
  "use strict";
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isTouch = window.matchMedia("(hover: none)").matches;

  /* ---------- LOADER ---------- */
  const loader = document.getElementById("loader");
  const loaderBar = document.getElementById("loaderBar");
  const loaderPct = document.getElementById("loaderPct");
  let progress = 0;
  document.body.style.overflow = "hidden";
  const fakeLoad = setInterval(() => {
    progress += Math.random() * 22;
    if (progress >= 100) { progress = 100; clearInterval(fakeLoad); finishLoad(); }
    if (loaderBar) loaderBar.style.width = progress + "%";
    if (loaderPct) loaderPct.textContent = Math.floor(progress) + "%";
  }, 120);
  function finishLoad() {
    setTimeout(() => {
      loader && loader.classList.add("is-done");
      document.body.style.overflow = "";
    }, 350);
  }

  /* ---------- CUSTOM CURSOR (délégation) ---------- */
  const INTERACTIVE = 'a, button, input, textarea, [data-cursor], [data-tilt], .trailer__play';
  if (!isTouch) {
    const cursor = document.getElementById("cursor");
    const dot = document.getElementById("cursorDot");
    let mx = 0, my = 0, cx = 0, cy = 0;
    window.addEventListener("mousemove", (e) => {
      mx = e.clientX; my = e.clientY;
      if (dot) { dot.style.left = mx + "px"; dot.style.top = my + "px"; }
    });
    (function tick() {
      cx += (mx - cx) * 0.18; cy += (my - cy) * 0.18;
      if (cursor) { cursor.style.left = cx + "px"; cursor.style.top = cy + "px"; }
      requestAnimationFrame(tick);
    })();
    document.addEventListener("mouseover", (e) => {
      if (cursor && e.target.closest && e.target.closest(INTERACTIVE)) cursor.classList.add("is-hover");
    });
    document.addEventListener("mouseout", (e) => {
      if (cursor && e.target.closest && e.target.closest(INTERACTIVE)) cursor.classList.remove("is-hover");
    });
  }

  /* ---------- MAGNETIC + TILT (rebindable) ---------- */
  function bindMagnetic(scope) {
    if (isTouch || reduceMotion) return;
    (scope || document).querySelectorAll("[data-magnetic]:not([data-bound])").forEach((el) => {
      el.setAttribute("data-bound", "1");
      el.addEventListener("mousemove", (e) => {
        const r = el.getBoundingClientRect();
        const x = e.clientX - r.left - r.width / 2;
        const y = e.clientY - r.top - r.height / 2;
        el.style.transform = `translate(${x * 0.25}px, ${y * 0.35}px)`;
      });
      el.addEventListener("mouseleave", () => { el.style.transform = ""; });
    });
  }
  function bindTilt(scope) {
    if (isTouch || reduceMotion) return;
    (scope || document).querySelectorAll("[data-tilt]:not([data-bound])").forEach((el) => {
      el.setAttribute("data-bound", "1");
      el.addEventListener("mousemove", (e) => {
        const r = el.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width - 0.5;
        const py = (e.clientY - r.top) / r.height - 0.5;
        el.style.transform = `perspective(800px) rotateY(${px * 7}deg) rotateX(${-py * 7}deg) translateY(-4px)`;
      });
      el.addEventListener("mouseleave", () => { el.style.transform = ""; });
    });
  }

  /* ---------- NAV ---------- */
  const nav = document.getElementById("nav");
  const sp = document.getElementById("scrollProgress");
  window.addEventListener("scroll", () => {
    nav && nav.classList.toggle("is-scrolled", window.scrollY > 40);
    if (sp) {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      sp.style.width = (h > 0 ? (window.scrollY / h) * 100 : 0) + "%";
    }
  }, { passive: true });
  const burger = document.getElementById("burger");
  burger && burger.addEventListener("click", () => nav.classList.toggle("is-open"));
  document.addEventListener("click", (e) => {
    if (e.target.closest(".nav__links a")) nav && nav.classList.remove("is-open");
  });

  /* ---------- REVEAL ON SCROLL (rebindable) ---------- */
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-in");
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });

  const countObserver = new IntersectionObserver((entries, ob) => {
    entries.forEach((e) => { if (e.isIntersecting) { animateCount(e.target); ob.unobserve(e.target); } });
  }, { threshold: 0.4 });

  function observeReveals(scope) {
    (scope || document).querySelectorAll(".reveal:not([data-seen])").forEach((el) => {
      el.setAttribute("data-seen", "1"); revealObserver.observe(el);
    });
    (scope || document).querySelectorAll("[data-count]:not([data-seen-c])").forEach((el) => {
      el.setAttribute("data-seen-c", "1"); countObserver.observe(el);
    });
  }

  /* ---------- COUNTERS ---------- */
  function animateCount(el) {
    const target = parseFloat(el.getAttribute("data-count"));
    const suffix = el.getAttribute("data-suffix") || "";
    if (reduceMotion) { el.textContent = fmt(target) + suffix; return; }
    const dur = 1700, start = performance.now();
    (function step(now) {
      const p = Math.min((now - start) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = fmt(target * eased) + suffix;
      if (p < 1) requestAnimationFrame(step); else el.textContent = fmt(target) + suffix;
    })(start);
  }
  function fmt(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1).replace(".0", "") + "M";
    if (n >= 1000) return Math.round(n / 1000) + "K";
    return Math.round(n).toString();
  }

  /* ---------- GLITCH ---------- */
  function bindGlitch(scope) {
    if (reduceMotion) return;
    (scope || document).querySelectorAll("[data-glitch]:not([data-g])").forEach((el) => {
      el.setAttribute("data-g", "1");
      setInterval(() => {
        el.classList.add("glitching");
        setTimeout(() => el.classList.remove("glitching"), 220);
      }, 3200 + Math.random() * 2200);
    });
  }

  /* ---------- PARTICLE BACKGROUND ---------- */
  const canvas = document.getElementById("bgCanvas");
  if (canvas && !reduceMotion) {
    const ctx = canvas.getContext("2d");
    let w, h, particles, mouse = { x: -999, y: -999 };
    const COLORS = ["168,85,247", "56,189,248", "244,114,182"];
    function resize() {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
      const count = Math.min(80, Math.floor((w * h) / 18000));
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.32, vy: (Math.random() - 0.5) * 0.32,
        r: Math.random() * 1.7 + 0.6, c: COLORS[(Math.random() * COLORS.length) | 0],
      }));
    }
    window.addEventListener("resize", resize);
    window.addEventListener("mousemove", (e) => { mouse.x = e.clientX; mouse.y = e.clientY; });
    resize();
    (function draw() {
      ctx.clearRect(0, 0, w, h);
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
        const dx = p.x - mouse.x, dy = p.y - mouse.y, d2 = dx * dx + dy * dy;
        if (d2 < 13000) { const f = (13000 - d2) / 13000, dd = Math.sqrt(d2) || 1; p.x += (dx / dd) * f * 1.5; p.y += (dy / dd) * f * 1.5; }
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${p.c},0.9)`; ctx.fill();
        for (let j = i + 1; j < particles.length; j++) {
          const q = particles[j], ax = p.x - q.x, ay = p.y - q.y, dist = ax * ax + ay * ay;
          if (dist < 12000) {
            ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y);
            ctx.strokeStyle = `rgba(${p.c},${0.1 * (1 - dist / 12000)})`; ctx.lineWidth = 0.6; ctx.stroke();
          }
        }
      }
      requestAnimationFrame(draw);
    })();
  }

  /* ---------- TOAST (global) ---------- */
  let toastEl;
  function flash(msg) {
    if (!toastEl) {
      toastEl = document.createElement("div");
      toastEl.className = "toast";
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    toastEl.classList.add("is-show");
    clearTimeout(toastEl._t);
    toastEl._t = setTimeout(() => toastEl.classList.remove("is-show"), 3500);
  }

  /* ---------- Home page extras (si présents) ---------- */
  document.addEventListener("click", (e) => {
    if (e.target.closest(".trailer__play, .btn--play")) {
      e.preventDefault();
      flash("🎬 La bande-annonce sera dévoilée le jour de la sortie !");
    }
  });
  const form = document.getElementById("ctaForm");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const email = form.querySelector("input").value.trim();
      flash(`✦ Bienvenue dans la légende, ${email.split("@")[0] || "héros"} !`);
      form.reset();
    });
  }

  /* ---------- API publique pour le contenu dynamique ---------- */
  function refresh(scope) {
    observeReveals(scope);
    bindMagnetic(scope);
    bindTilt(scope);
    bindGlitch(scope);
  }
  window.AETHER = { refresh, flash };

  // premier scan
  refresh(document);
})();
