# AETHERION STUDIOS — Site vitrine d'un studio de jeux vidéo

Site web **complet et professionnel** d'un studio de jeux vidéo fictif, **AETHERION STUDIOS**.
Architecture multi-pages, catalogue de **35 jeux**, présentation des **6 secteurs** avec profils,
et un **système de commentaires** prêt à l'emploi.

![Thème](https://img.shields.io/badge/th%C3%A8me-jeux%20vid%C3%A9o-a855f7)
![Stack](https://img.shields.io/badge/stack-HTML%20%2F%20CSS%20%2F%20JS%20vanilla-38bdf8)
![Pages](https://img.shields.io/badge/pages-10%2B-f472b6)

## 🗺️ Architecture des pages

| Page | Fichier | Description |
|------|---------|-------------|
| Accueil | `index.html` | Hero, stats, jeux phares, secteurs, newsletter |
| Le studio | `studio.html` | Histoire, mission, valeurs, frise chronologique |
| Catalogue | `games.html` | Les **35 jeux**, recherche + filtres par genre |
| Fiche de jeu | `game.html?id=…` | Synopsis, caractéristiques, jeux liés + **commentaires** |
| Nos équipes | `teams.html` | Vue d'ensemble des 6 secteurs |
| Secteur | `secteur.html?dept=…` | Mission, technos et **profils** (prog, art, design, prod, audio, QA) |
| Carrières | `careers.html` | Avantages + offres d'emploi |
| Actualités | `news.html` | Fil d'actualités du studio |
| Contact | `contact.html` | Formulaire + coordonnées |

> Les secteurs et les jeux sont **pilotés par les données** (`data/`) : une seule page
> modèle affiche les 35 jeux et les 6 départements.

## 📁 Structure du projet

```
.
├── index.html  studio.html  games.html  game.html
├── teams.html  secteur.html  careers.html  news.html  contact.html
├── data/
│   ├── games.js        # 35 jeux (titre, synopsis, genres, plateformes…)
│   └── team.js         # 6 secteurs + 25 profils
├── scripts/
│   ├── components.js   # header/footer partagés (DRY) injectés sur chaque page
│   ├── main.js         # interactions globales (curseur, particules, reveal…)
│   ├── home.js         # rendu accueil (jeux phares + secteurs)
│   ├── catalog.js      # catalogue : recherche + filtres
│   ├── game-detail.js  # fiche de jeu
│   ├── sector.js       # page secteur + profils
│   └── comments.js     # système de commentaires
├── styles/
│   ├── main.css        # design system + animations de base
│   └── pages.css       # composants & pages internes
└── README.md
```

## 💬 Système de commentaires

Disponible sur chaque **fiche de jeu** (`game.html`). Fonctionnalités :

- Publication avec pseudo (mémorisé), validation et anti-injection (échappement HTML)
- Likes, suppression de ses propres commentaires, horodatage relatif, avatars colorés
- Compteur, tri du plus récent au plus ancien

**Stockage actuel : `localStorage`** (démo sans serveur). Le code est volontairement
structuré autour d'une couche `CommentStore` **asynchrone** : pour brancher un vrai
backend plus tard, il suffit de remplacer le corps de `list/add/like/remove` par des
appels `fetch()` — l'interface ne change pas. Voir les commentaires dans
`scripts/comments.js`.

## ✨ Fonctionnalités UI

- Écran de chargement, curseur personnalisé, **fond de particules interactif** (canvas)
- Animations au scroll, compteurs animés, effet glitch, boutons magnétiques, cartes 3D (tilt)
- Menu déroulant des secteurs, barre de progression de défilement
- **100 % responsive** + respect de `prefers-reduced-motion` ♿
- HTML / CSS / JavaScript **vanilla**, sans dépendance ni build

## 🚀 Lancer le site

```bash
python3 -m http.server 8000   # puis http://localhost:8000
# ou : npx serve .
```

> ⚠️ Ouvrez via un serveur local (et non `file://`) pour que le chargement des
> scripts de données fonctionne correctement.

---

*Projet de démonstration — Aetherion Studios, ses 35 jeux et ses équipes sont fictifs.*
