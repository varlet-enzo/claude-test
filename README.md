# AETHERION — Site vitrine de jeu vidéo

Site web vitrine **niveau professionnel / award-worthy** pour un RPG d'action open-world
next-gen fictif nommé **AETHERION**. Conçu pour avoir un rendu digne d'un studio AAA et
pouvoir concourir à des prix de design web.

![Thème](https://img.shields.io/badge/th%C3%A8me-jeux%20vid%C3%A9o-a855f7)
![Stack](https://img.shields.io/badge/stack-HTML%20%2F%20CSS%20%2F%20JS%20vanilla-38bdf8)

## ✨ Fonctionnalités

- **Écran de chargement** animé avec barre de progression
- **Curseur personnalisé** avec effet de fluidité et blend mode
- **Fond de particules** interactif sur `<canvas>` (réagit à la souris, connexions dynamiques)
- **Boutons magnétiques** et **cartes 3D tilt** au survol
- **Animations au scroll** (reveal en cascade via IntersectionObserver)
- **Compteurs animés** pour les statistiques
- **Effet glitch** sur le titre hero
- **Barre de progression** de défilement
- **Menu burger** responsive
- **Texte en dégradé**, glow néon, marquee défilant
- Entièrement **responsive** (desktop / tablette / mobile)
- Respect de `prefers-reduced-motion` ♿

## 🎨 Stack technique

Aucune dépendance, aucun build. Tout en **HTML / CSS / JavaScript vanilla** :

```
.
├── index.html        # Structure de la page
├── styles/main.css   # Design system + animations
├── scripts/main.js   # Interactions (curseur, particules, reveal, compteurs…)
└── README.md
```

Polices : [Orbitron](https://fonts.google.com/specimen/Orbitron) (display) &
[Sora](https://fonts.google.com/specimen/Sora) (texte) via Google Fonts.

## 🚀 Lancer le site

Aucune installation requise. Ouvrez simplement `index.html` dans un navigateur,
ou servez le dossier localement :

```bash
# Python
python3 -m http.server 8000

# ou Node
npx serve .
```

Puis ouvrez http://localhost:8000.

## 🏆 Pourquoi un rendu « pro »

- Direction artistique cohérente (palette violet/cyan/rose, typographie spatiale)
- Micro-interactions soignées sur chaque élément
- Hiérarchie visuelle claire et copywriting immersif
- Performances : animations en `requestAnimationFrame`, observers, `will-change` implicite
- Accessibilité : navigation clavier, contrastes, reduced-motion, attributs ARIA

---

*Projet de démonstration — AETHERION est un jeu fictif.*
