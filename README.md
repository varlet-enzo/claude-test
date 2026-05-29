# MAISON BONBON — Site vitrine d'une pâtisserie 🍰

Site web **complet et professionnel** d'une pâtisserie artisanale fictive, **MAISON BONBON**,
avec une direction artistique **rose bonbon** et gourmande. Architecture multi-pages,
carte de **35 pâtisseries**, présentation des **6 ateliers** avec artisans, et un
**système d'avis** prêt à l'emploi.

![Thème](https://img.shields.io/badge/th%C3%A8me-p%C3%A2tisserie-ff4f9a)
![DA](https://img.shields.io/badge/DA-rose%20bonbon-ff86bd)
![Stack](https://img.shields.io/badge/stack-HTML%20%2F%20CSS%20%2F%20JS%20vanilla-c98be0)

## 🗺️ Architecture des pages

| Page | Fichier | Description |
|------|---------|-------------|
| Accueil | `index.html` | Hero, chiffres, douceurs phares, ateliers, newsletter |
| La Maison | `studio.html` | Histoire, mission, valeurs, frise chronologique |
| La Carte | `games.html` | Les **35 pâtisseries**, recherche + filtres par catégorie |
| Fiche pâtisserie | `game.html?id=…` | Saveurs, prix, suggestions + **avis gourmands** |
| Nos Ateliers | `teams.html` | Vue d'ensemble des 6 ateliers |
| Atelier | `secteur.html?dept=…` | Mission, savoir-faire et **artisans** (pâtisserie, boulangerie, chocolaterie, cake design, production, boutique) |
| Recrutement | `careers.html` | Avantages + offres d'emploi |
| Actualités | `news.html` | Nouveautés de saison & coulisses |
| Contact | `contact.html` | Formulaire + coordonnées |

> Les ateliers et les pâtisseries sont **pilotés par les données** (`data/`) : une seule
> page modèle affiche les 35 douceurs et les 6 ateliers.

## 🎨 Direction artistique

- Palette **rose bonbon** sur fond crème (clair, doux, gourmand)
- Typographies : **Fraunces** (titres, élégance pâtissière) + **Quicksand** (texte, rondeur)
- Cartes blanches à coins arrondis, ombres roses, tuiles pastel façon macarons
- Fond de particules en tons rosés, curseur et accents rose vif

## 📁 Structure du projet

```
.
├── index.html  studio.html  games.html  game.html
├── teams.html  secteur.html  careers.html  news.html  contact.html
├── data/
│   ├── games.js        # 35 pâtisseries (nom, saveurs, catégories, prix…)
│   └── team.js         # 6 ateliers + artisans
├── scripts/
│   ├── components.js   # header/footer partagés (DRY) injectés sur chaque page
│   ├── main.js         # interactions globales (curseur, particules, reveal…)
│   ├── home.js         # rendu accueil (douceurs phares + ateliers)
│   ├── catalog.js      # carte : recherche + filtres
│   ├── game-detail.js  # fiche pâtisserie
│   ├── sector.js       # page atelier + artisans
│   └── comments.js     # système d'avis
├── styles/
│   ├── main.css        # design system rose bonbon + animations
│   └── pages.css       # composants & pages internes
└── README.md
```

## 💬 Système d'avis

Disponible sur chaque **fiche pâtisserie** (`game.html`). Fonctionnalités :

- Publication avec prénom (mémorisé), validation et anti-injection (échappement HTML)
- J'aime, suppression de ses propres avis, horodatage relatif, avatars colorés
- Compteur, tri du plus récent au plus ancien

**Stockage actuel : `localStorage`** (démo sans serveur). Le code est structuré autour
d'une couche `CommentStore` **asynchrone** : pour brancher un vrai backend plus tard,
il suffit de remplacer le corps de `list/add/like/remove` par des appels `fetch()` —
l'interface ne change pas. Voir `scripts/comments.js`.

## ✨ Fonctionnalités UI

- Écran de chargement, curseur personnalisé, **fond de particules interactif** (canvas)
- Animations au scroll, compteurs animés, boutons magnétiques, cartes 3D (tilt)
- Menu déroulant des ateliers, barre de progression de défilement
- **100 % responsive** + respect de `prefers-reduced-motion` ♿
- HTML / CSS / JavaScript **vanilla**, sans dépendance ni build

## 🚀 Lancer le site

```bash
python3 -m http.server 8000   # puis http://localhost:8000
# ou : npx serve .
```

> ⚠️ Ouvrez via un serveur local (et non `file://`) pour que le chargement des
> données fonctionne correctement.

---

*Projet de démonstration — Maison Bonbon, ses 35 pâtisseries et ses artisans sont fictifs.*
