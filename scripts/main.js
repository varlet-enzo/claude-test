/* ============================================
   AETHERION — interactions & animations
   ============================================ */
(() => {
  "use strict";
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isTouch = window.matchMedia("(hover: none)").matches;

  /* ---------- LOADER ---------- */
  const loader = document.getElementById("loader");
  const loaderBar = document.getElementById("loaderBar");
  const loaderPct = document.getElementById("loaderPct");
  let progress = 0;
  const fakeLoad = setInterval(() => {
    progress += Math.random() * 18;
    if (progress >= 100) { progress = 100; clearInterval(fakeLoad); finishLoad(); }
    if (loaderBar) loaderBar.style.width = progress + "%";
    if (loaderPct) loaderPct.textContent = Math.floor(progress) + "%";
  }, 140);
  function finishLoad() {
    setTimeout(() => {
      loader && loader.classList.add("is-done");
      document.body.style.overflow = "";
      startReveals();
    }, 400);
  }
  document.body.style.overflow = "hidden";

  /* ---------- CUSTOM CURSOR ---------- */
  if (!isTouch) {
    const cursor = document.getElementById("cursor");
    const dot = document.getElementById("cursorDot");
    let mx = 0, my = 0, cx = 0, cy = 0;
    window.addEventListener("mousemove", (e) => {
      mx = e.clientX; my = e.clientY;
      if (dot) { dot.style.left = mx + "px"; dot.style.top = my + "px"; }
    });
    const tick = () => {
      cx += (mx - cx) * 0.18; cy += (my - cy) * 0.18;
      if (cursor) { cursor.style.left = cx + "px"; cursor.style.top = cy + "px"; }
      requestAnimationFrame(tick);
    };
    tick();
    document.querySelectorAll("[data-cursor], a, button, input").forEach((el) => {
      el.addEventListener("mouseenter", () => cursor && cursor.classList.add("is-hover"));
      el.addEventListener("mouseleave", () => cursor && cursor.classList.remove("is-hover"));
    });
  }

  /* ---------- MAGNETIC BUTTONS ---------- */
  if (!isTouch && !reduceMotion) {
    document.querySelectorAll("[data-magnetic]").forEach((el) => {
      el.addEventListener("mousemove", (e) => {
        const r = el.getBoundingClientRect();
        const x = e.clientX - r.left - r.width / 2;
        const y = e.clientY - r.top - r.height / 2;
        el.style.transform = `translate(${x * 0.25}px, ${y * 0.35}px)`;
      });
      el.addEventListener("mouseleave", () => { el.style.transform = ""; });
    });
  }

  /* ---------- 3D TILT ---------- */
  if (!isTouch && !reduceMotion) {
    document.querySelectorAll("[data-tilt]").forEach((el) => {
      el.addEventListener("mousemove", (e) => {
        const r = el.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width - 0.5;
        const py = (e.clientY - r.top) / r.height - 0.5;
        el.style.transform = `perspective(800px) rotateY(${px * 8}deg) rotateX(${-py * 8}deg) translateY(-4px)`;
      });
      el.addEventListener("mouseleave", () => { el.style.transform = ""; });
    });
  }

  /* ---------- NAV ---------- */
  const nav = document.getElementById("nav");
  const burger = document.getElementById("burger");
  window.addEventListener("scroll", () => {
    nav && nav.classList.toggle("is-scrolled", window.scrollY > 40);
    const sp = document.getElementById("scrollProgress");
    if (sp) {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      sp.style.width = (window.scrollY / h) * 100 + "%";
    }
  }, { passive: true });
  burger && burger.addEventListener("click", () => nav.classList.toggle("is-open"));
  document.querySelectorAll(".nav__links a").forEach((a) =>
    a.addEventListener("click", () => nav.classList.remove("is-open"))
  );

  /* ---------- REVEAL ON SCROLL ---------- */
  let revealObserver;
  function startReveals() {
    revealObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-in");
          revealObserver.unobserve(entry.target);
          if (entry.target.hasAttribute("data-count")) animateCount(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: "0px 0px -8% 0px" });
    document.querySelectorAll(".reveal").forEach((el) => revealObserver.observe(el));
    document.querySelectorAll("[data-count]").forEach((el) => {
      new IntersectionObserver((es, ob) => {
        es.forEach((e) => { if (e.isIntersecting) { animateCount(e.target); ob.unobserve(e.target); } });
      }, { threshold: 0.4 }).observe(el);
    });
  }

  /* ---------- COUNTERS ---------- */
  function animateCount(el) {
    const target = parseInt(el.getAttribute("data-count"), 10);
    const suffix = el.getAttribute("data-suffix") || "";
    if (reduceMotion) { el.textContent = format(target) + suffix; return; }
    const dur = 1800; const start = performance.now();
    const step = (now) => {
      const p = Math.min((now - start) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = format(Math.floor(target * eased)) + suffix;
      if (p < 1) requestAnimationFrame(step);
      else el.textContent = format(target) + suffix;
    };
    requestAnimationFrame(step);
  }
  function format(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1).replace(".0", "") + "M";
    if (n >= 1000) return (n / 1000).toFixed(0) + "K";
    return n.toString();
  }

  /* ---------- GLITCH ---------- */
  if (!reduceMotion) {
    document.querySelectorAll("[data-glitch]").forEach((el) => {
      setInterval(() => {
        el.classList.add("glitching");
        setTimeout(() => el.classList.remove("glitching"), 220);
      }, 3200 + Math.random() * 2000);
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
      const count = Math.min(90, Math.floor((w * h) / 16000));
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.35, vy: (Math.random() - 0.5) * 0.35,
        r: Math.random() * 1.8 + 0.6, c: COLORS[(Math.random() * COLORS.length) | 0],
      }));
    }
    window.addEventListener("resize", resize);
    window.addEventListener("mousemove", (e) => { mouse.x = e.clientX; mouse.y = e.clientY; });
    resize();
    function draw() {
      ctx.clearRect(0, 0, w, h);
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
        // mouse repel
        const dx = p.x - mouse.x, dy = p.y - mouse.y;
        const d2 = dx * dx + dy * dy;
        if (d2 < 14000) { const f = (14000 - d2) / 14000; p.x += (dx / Math.sqrt(d2)) * f * 1.6; p.y += (dy / Math.sqrt(d2)) * f * 1.6; }
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${p.c},0.9)`;
        ctx.fill();
        // connections
        for (let j = i + 1; j < particles.length; j++) {
          const q = particles[j];
          const ddx = p.x - q.x, ddy = p.y - q.y;
          const dist = ddx * ddx + ddy * ddy;
          if (dist < 12000) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y);
            ctx.strokeStyle = `rgba(${p.c},${0.12 * (1 - dist / 12000)})`;
            ctx.lineWidth = 0.6;
            ctx.stroke();
          }
        }
      }
      requestAnimationFrame(draw);
    }
    draw();
  }

  /* ---------- TRAILER / PLAY feedback ---------- */
  document.querySelectorAll(".trailer__play, .btn--play").forEach((b) =>
    b.addEventListener("click", (e) => {
      e.preventDefault();
      flash("🎬 La bande-annonce sera dévoilée le jour de la sortie !");
    })
  );

  /* ---------- CTA FORM ---------- */
  const form = document.getElementById("ctaForm");
  const note = document.getElementById("ctaNote");
  form && form.addEventListener("submit", (e) => {
    e.preventDefault();
    const email = form.querySelector("input").value.trim();
    if (note) note.textContent = `✦ Bienvenue dans la légende, ${email.split("@")[0]} ! Vérifiez votre boîte mail.`;
    form.reset();
  });

  /* ---------- toast ---------- */
  let toastEl;
  function flash(msg) {
    if (!toastEl) {
      toastEl = document.createElement("div");
      Object.assign(toastEl.style, {
        position: "fixed", bottom: "2rem", left: "50%", transform: "translateX(-50%) translateY(120%)",
        background: "rgba(13,4,32,.92)", backdropFilter: "blur(14px)", color: "#f3eefb",
        padding: "1rem 1.6rem", borderRadius: "99px", border: "1px solid rgba(168,85,247,.5)",
        zIndex: "10000", fontSize: ".95rem", boxShadow: "0 0 40px rgba(168,85,247,.4)",
        transition: "transform .5s cubic-bezier(.16,1,.3,1)", maxWidth: "90vw", textAlign: "center",
      });
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    requestAnimationFrame(() => { toastEl.style.transform = "translateX(-50%) translateY(0)"; });
    clearTimeout(toastEl._t);
    toastEl._t = setTimeout(() => { toastEl.style.transform = "translateX(-50%) translateY(120%)"; }, 3500);
  }

  /* fallback: si reduce-motion, on révèle direct */
  if (reduceMotion) {
    document.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-in"));
  }
})();
