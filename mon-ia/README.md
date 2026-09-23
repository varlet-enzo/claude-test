# Mon IA : ton IA personnelle, gratuite et 100 % locale

Mon IA est un assistant qui tourne **entièrement sur ton ordinateur**, grâce à [Ollama](https://ollama.com) et aux modèles d'IA open source (Qwen, Gemma, gpt-oss, Mistral, Llama…).

- 💸 **Gratuite** : pas d'abonnement, pas de clé d'API, aucun token facturé. Le seul coût, c'est l'électricité de ton ordinateur.
- 🔒 **Privée** : tes conversations, ta mémoire et tes fichiers restent sur ta machine.
- ✈️ **Hors ligne** : une fois le modèle téléchargé, tout marche sans internet (sauf la recherche web, que tu peux désactiver).
- 🧠 **Elle se souvient de toi** d'une conversation à l'autre, et tu peux voir et modifier ce qu'elle sait.
- 🛠️ **Elle a des outils** : recherche web gratuite, lecture de pages web, calculatrice exacte, date et heure.
- 📎 **Elle lit tes fichiers** : PDF, documents Word, textes, code… et les images avec un modèle « vision ».
- 🎭 **Elle est à toi** : tu choisis son nom, sa personnalité et son « cerveau » (le modèle).

> **Soyons honnêtes sur la puissance.** Un modèle qui tourne sur un ordinateur personnel n'égale pas les plus gros modèles des entreprises d'IA (comme Claude), qui tournent sur des fermes de serveurs. Mais les modèles open source sont devenus très bons : pour discuter, écrire, expliquer, résumer, traduire ou coder, un modèle de 8 à 30 milliards de paramètres fait déjà du très bon travail. Et plus ta machine est puissante, plus ton IA le sera : il suffit de changer de modèle, en un clic.

## Installation (une dizaine de minutes)

1. **Installe Ollama** depuis [ollama.com/download](https://ollama.com/download) (Windows, Mac ou Linux), puis lance-le. C'est le moteur qui fait tourner les modèles.
2. **Installe Python 3.10 ou plus récent** depuis [python.org/downloads](https://www.python.org/downloads/). Sous Windows, coche bien la case « Add python.exe to PATH » pendant l'installation.
3. **Récupère ce dossier** : bouton « Code → Download ZIP » sur GitHub (puis dézippe), ou `git clone`.
4. **Lance ton IA** :
   - **Windows** : double-clique sur `lancer.bat` dans le dossier `mon-ia`.
   - **Mac / Linux** : ouvre un terminal dans le dossier `mon-ia` et tape `./lancer.sh`.

Au premier lancement, le script installe ce qu'il faut (une ou deux minutes), puis ton navigateur s'ouvre sur <http://127.0.0.1:8000>. Si aucun modèle n'est encore installé, l'interface te propose d'en télécharger un en un clic.

<details>
<summary>Installation « à la main » (sans les scripts)</summary>

```bash
cd mon-ia
python -m venv .venv
source .venv/bin/activate      # Windows : .venv\Scripts\activate
pip install -r requirements.txt
ollama pull qwen3:8b           # ou un autre modèle, voir plus bas
python -m mon_ia               # interface dans le navigateur
python -m mon_ia chat          # ou discussion dans le terminal
```
</details>

## Quel modèle choisir ?

Pour être rapide, le modèle doit tenir dans la mémoire de ta carte graphique (VRAM). Sinon il tourne sur le processeur et la mémoire vive : ça marche, mais c'est plus lent.

| Ton ordinateur | Modèle conseillé | Taille |
|---|---|---|
| Ordinateur modeste, 8 Go de mémoire vive, sans carte graphique | `qwen3:4b` | 2,5 Go |
| 16 Go de mémoire vive, ou carte graphique de 8 Go | `qwen3:8b` ⭐ | 5,2 Go |
| Carte graphique de 12 Go, ou Mac (puce M) avec 16 Go | `qwen3:14b` | 9,3 Go |
| Carte graphique de 16 Go, ou Mac avec 24 Go | `gpt-oss:20b` | 14 Go |
| Carte graphique de 24 Go, ou Mac avec 32 Go ou plus | `qwen3:30b` | 19 Go |
| Pour qu'elle regarde des images | `gemma3:12b` (ou `gemma3:4b`) | 8,1 Go |

Les modèles `qwen3` et `gpt-oss` savent utiliser les outils (mémoire, recherche web, calculatrice) et réfléchir avant de répondre. `gemma3` sait regarder les images, mais n'utilise pas d'outils.

Pour aller encore plus loin sur une très grosse machine (64 Go de mémoire ou plus) : `gpt-oss:120b`, `qwen3:235b`… Le catalogue complet est sur [ollama.com/library](https://ollama.com/library) et de nouveaux modèles sortent régulièrement : pour en essayer un, tape son nom dans le menu **📦 Modèles** (ou `ollama pull nom-du-modele` dans un terminal).

## Utilisation

**Dans le navigateur** (`lancer.bat`, `./lancer.sh` ou `python -m mon_ia`) :

- choisis le modèle en haut, écris ton message, puis Entrée pour l'envoyer ;
- 📎 pour joindre des fichiers (tu peux aussi les glisser-déposer ou coller une image) ;
- **Réflexion approfondie** : le modèle réfléchit avant de répondre, ce qui est plus intelligent sur les questions difficiles mais plus lent ;
- ■ pour arrêter une réponse en cours ;
- dans la barre de gauche : tes conversations, **🎭 Nom et personnalité**, **🧠 Mémoire** et **📦 Modèles**.

**Dans le terminal** (`./lancer.sh chat`, `lancer.bat chat` ou `python -m mon_ia chat`) :

| Commande | Effet |
|---|---|
| `/nouveau` | nouvelle conversation |
| `/modele qwen3:14b` | changer de modèle |
| `/modeles` | lister les modèles installés |
| `/reflexion` | activer ou désactiver la réflexion approfondie |
| `/memoire` | voir ce que ton IA sait sur toi |
| `/quitter` | quitter |

Options : `--modele qwen3:14b`, `--reflexion`, `--voir-reflexion`.

## La rendre vraiment à toi

- **Son nom et sa personnalité** : menu 🎭 (ou le fichier `data/personnalite.md`). C'est un texte libre : décris-lui qui elle est, comment elle parle, ce qu'elle doit savoir faire. Exemples : « Tu es {nom}, un coach sportif motivant qui parle de façon énergique », « Tu es {nom}, un professeur de maths patient qui ne donne jamais la réponse directement ».
- **Sa mémoire** : menu 🧠 (ou le fichier `data/memoire.md`). Elle s'enrichit toute seule quand tu parles de toi, et tu peux la corriger à tout moment. Dis-lui aussi « oublie que… » pour effacer un souvenir.
- **Les réglages** : copie `.env.exemple` en `.env` pour changer le modèle par défaut, la taille de la mémoire de travail, désactiver la recherche web, etc.

## Partager avec tes potes

Ton IA tourne sur ton PC : pour que tes potes l'utilisent, ton PC sert de serveur, et un **tunnel Cloudflare** (gratuit) leur donne un lien du type `https://xxx.trycloudflare.com`. Chacun a son compte et son espace privé (ses conversations et sa mémoire). Toi seul peux changer le nom, la personnalité et les modèles.

> Pourquoi pas Vercel ou un hébergeur « classique » ? Ils n'ont pas de carte graphique et ne peuvent pas garder un modèle de plusieurs Go en mémoire. Les serveurs qui en sont capables sont payants.

**1. Crée les comptes.** Copie `.env.exemple` en `.env`, puis remplis ces deux lignes (sans le `#` devant) :

```
IA_MOT_DE_PASSE=un-mot-de-passe-solide-pour-toi
IA_AMIS=leo:soleil42, sam:banane77
```

- `IA_MOT_DE_PASSE` : ton mot de passe (8 caractères minimum). Tu te connectes avec le pseudo `admin`.
- `IA_AMIS` : un `pseudo:motdepasse` par pote, séparés par des virgules. Pseudo sans accent ni espace, mot de passe de 6 caractères minimum.

**2. Installe cloudflared** (une seule fois). Sous Windows, ouvre l'invite de commandes et tape :

```
winget install --id Cloudflare.cloudflared
```

Sur Mac : `brew install cloudflared`. Ferme puis rouvre la fenêtre après l'installation.

**3. Lance ton IA** avec `lancer.bat` (ou `./lancer.sh`), comme d'habitude. Elle te demande maintenant de te connecter : pseudo `admin` et ton mot de passe.

**4. Crée le lien** : double-clique sur `partager.bat` (ou lance `./partager.sh`). Au bout de quelques secondes, une adresse en `https://…trycloudflare.com` s'affiche dans un cadre. Envoie-la à tes potes, avec leur pseudo et leur mot de passe.

À savoir :

- **Ton PC doit rester allumé**, avec les fenêtres de `lancer.bat` et de `partager.bat` ouvertes. Les fermer coupe le partage.
- **Le lien change à chaque lancement** de `partager.bat` : renvoie le nouveau à tes potes. (Pour une adresse fixe, il faut un compte Cloudflare et un nom de domaine.)
- **Ton IA répond à une personne à la fois** : si plusieurs potes écrivent en même temps, ils attendent leur tour.
- **Sois honnête avec tes potes** : leurs conversations sont séparées des tiennes dans l'interface, mais elles sont enregistrées sur ton PC (dans `data/invites/`), donc tu pourrais les lire.
- **Pour retirer l'accès à quelqu'un**, enlève son compte de `IA_AMIS` et relance `lancer.bat` : il est aussitôt déconnecté.
- **Après 8 mauvais mots de passe**, la connexion est bloquée pendant un quart d'heure, pour empêcher quelqu'un de deviner les mots de passe.

## Tes données

Tout est rangé dans le dossier `data/` : les conversations (`conversations/`), la mémoire (`memoire.md`), la personnalité (`personnalite.md`), le nom (`reglages.json`) et, si tu partages ton IA, les espaces de tes potes (`invites/`). Pour faire une sauvegarde, copie ce dossier. Pour tout effacer, supprime-le.

Ce qui sort de ton ordinateur :
- les recherches web et les pages lues, quand ton IA utilise ces outils (tu vois toujours quand elle le fait). Pour une IA totalement hors ligne, mets `IA_RECHERCHE_WEB=non` dans le fichier `.env` ;
- le téléchargement des modèles, depuis ollama.com.

## Problèmes fréquents

- **« Impossible de joindre Ollama »** : lance l'application Ollama (l'icône du lama près de l'horloge), ou tape `ollama serve` dans un terminal.
- **Les réponses sont très lentes** : le modèle est trop gros pour ton ordinateur. Prends-en un plus petit, désactive la réflexion approfondie et ferme les applications gourmandes.
- **« Pas assez de mémoire »** : même remède, ou baisse `IA_CONTEXTE` dans le fichier `.env`.
- **Elle oublie le début d'une très longue conversation** : c'est normal, sa mémoire de travail est limitée. Augmente `IA_CONTEXTE` si ton ordinateur a assez de mémoire, ou commence une nouvelle conversation (sa mémoire à long terme, elle, est conservée).
- **La recherche web échoue** : les moteurs de recherche limitent parfois le nombre de requêtes. Réessaie un peu plus tard.
- **Le port 8000 est déjà utilisé** : ajoute `IA_PORT=8001` dans le fichier `.env`.
- **L'utiliser depuis ton téléphone** (sur le même Wi-Fi) : mets `IA_HOTE=0.0.0.0` dans `.env`, puis ouvre `http://adresse-ip-de-ton-pc:8000` sur le téléphone. Pense à définir aussi `IA_MOT_DE_PASSE`, sinon toute personne connectée au même réseau pourra l'utiliser.
- **Tes potes voient « Pseudo ou mot de passe incorrect »** : vérifie l'orthographe dans `IA_AMIS` (le pseudo s'écrit sans majuscule obligatoire, mais le mot de passe doit être exact) et que tu as bien relancé `lancer.bat` après avoir modifié `.env`.

## Pour les curieux

```
mon-ia/
├── lancer.bat / lancer.sh   lancement en un clic
├── partager.bat / .sh       lien de partage pour tes potes (Cloudflare Tunnel)
├── mon_ia/
│   ├── assistant.py         le moteur : discute avec le modèle via Ollama, gère le contexte et les outils
│   ├── tools.py             les outils : mémoire, recherche web, lecture de pages, calcul, date
│   ├── memory.py            la mémoire à long terme
│   ├── profile.py           le nom et la personnalité
│   ├── storage.py           la sauvegarde des conversations
│   ├── files.py             la lecture des fichiers joints
│   ├── web.py               le serveur de l'interface web
│   ├── auth.py              les comptes et la connexion (mode partage)
│   ├── cli.py               la discussion dans le terminal
│   └── static/              l'interface (HTML, CSS, JavaScript)
└── tests/                   les tests automatiques, avec un faux Ollama
```

Pour lancer les tests : `pip install -r requirements-dev.txt` puis `pytest`.

Des idées pour aller plus loin : ajouter tes propres outils dans `tools.py` (météo, agenda, domotique…), lui faire lire tout un dossier de documents, ou lui donner une voix.
