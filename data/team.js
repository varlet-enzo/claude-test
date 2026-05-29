/* ============================================================
   AETHERION STUDIOS — Secteurs & profils (hypothétiques)
   Donnée globale: window.DEPARTMENTS (objet indexé par slug)
   ============================================================ */
window.DEPARTMENTS = {
  programmation: {
    slug: "programmation",
    name: "Programmation",
    icon: "⌨️",
    hue: 210,
    tagline: "Le code qui donne vie aux mondes.",
    mission:
      "L'équipe Programmation transforme la vision créative en systèmes jouables. Du moteur maison « Aether » au gameplay, en passant par les outils et le réseau, nous construisons les fondations techniques de chaque jeu.",
    focus: [
      "Moteur & rendu (Aether Engine, ray tracing, pipeline graphique)",
      "Gameplay & systèmes (combat, IA, physique)",
      "Outils internes & éditeurs",
      "Réseau, backend & multijoueur",
    ],
    stack: ["C++", "Rust", "C#", "Lua", "Vulkan", "DirectX 12", "Python", "Go"],
    profiles: [
      {
        name: "Léa Moreau",
        role: "Directrice technique",
        years: 14,
        bio: "Architecte du moteur Aether. Léa veille à la cohérence technique de tous les projets et encadre les choix d'architecture.",
        skills: ["Architecture moteur", "Optimisation", "Leadership technique"],
      },
      {
        name: "Hugo Tanaka",
        role: "Ingénieur gameplay senior",
        years: 9,
        bio: "Spécialiste du game feel. Hugo a conçu le système de combat à la frame près d'Aetherion.",
        skills: ["Combat systems", "C++", "Game feel"],
      },
      {
        name: "Amina Diallo",
        role: "Ingénieure rendu",
        years: 7,
        bio: "Passionnée de lumière. Amina pilote le pipeline de ray tracing temps réel et l'éclairage volumétrique.",
        skills: ["Vulkan", "Shaders", "Ray tracing"],
      },
      {
        name: "Marco Bianchi",
        role: "Ingénieur réseau",
        years: 10,
        bio: "Garant de la fluidité en ligne. Marco bâtit l'infrastructure multijoueur de Celestia et Eclipse Protocol.",
        skills: ["Netcode", "Go", "Scalabilité"],
      },
      {
        name: "Sofia Reyes",
        role: "Développeuse outils",
        years: 6,
        bio: "Au service des créatifs, Sofia conçoit les éditeurs qui font gagner des heures à toute l'équipe.",
        skills: ["C#", "UX outils", "Automatisation"],
      },
    ],
  },

  art: {
    slug: "art",
    name: "Game Art",
    icon: "🎨",
    hue: 320,
    tagline: "Donner une âme visuelle à chaque univers.",
    mission:
      "L'équipe Art définit l'identité visuelle de nos jeux : direction artistique, modélisation 3D, animation, VFX et interface. Chaque pixel sert l'émotion et l'immersion.",
    focus: [
      "Direction artistique & concept art",
      "Modélisation 3D & sculpting",
      "Animation & rigging",
      "VFX & UI/UX visuelle",
    ],
    stack: ["Blender", "ZBrush", "Substance", "Maya", "Photoshop", "Houdini", "Spine", "Figma"],
    profiles: [
      {
        name: "Yuki Nakamura",
        role: "Directrice artistique",
        years: 13,
        bio: "Yuki impose une cohérence visuelle forte et reconnaissable à chaque production du studio.",
        skills: ["Direction artistique", "Color theory", "Concept"],
      },
      {
        name: "Thomas Leroy",
        role: "Lead environnement 3D",
        years: 8,
        bio: "Bâtisseur des cités flottantes d'Aetherion, Thomas sculpte des mondes crédibles et vivants.",
        skills: ["Environment art", "ZBrush", "World building"],
      },
      {
        name: "Nadia Haddad",
        role: "Character artist senior",
        years: 9,
        bio: "Nadia donne vie aux héros et créatures mémorables qui peuplent nos univers.",
        skills: ["Character design", "Sculpting", "Texturing"],
      },
      {
        name: "Eric Lindgren",
        role: "Animateur principal",
        years: 11,
        bio: "Eric insuffle le poids et la fluidité du mouvement, du combat le plus nerveux au geste le plus subtil.",
        skills: ["Animation", "Rigging", "Motion capture"],
      },
      {
        name: "Priya Sharma",
        role: "Artiste VFX",
        years: 6,
        bio: "Magie, explosions, météo : Priya orchestre les effets qui font vibrer l'écran.",
        skills: ["VFX", "Houdini", "Shaders FX"],
      },
    ],
  },

  design: {
    slug: "design",
    name: "Game Design",
    icon: "🎮",
    hue: 270,
    tagline: "Concevoir le plaisir, règle après règle.",
    mission:
      "L'équipe Game Design définit ce que le joueur ressent et fait. Systèmes, niveaux, narration et équilibrage : nous transformons des idées en expériences captivantes et justes.",
    focus: [
      "Systèmes & mécaniques de jeu",
      "Level design & rythme",
      "Narration & écriture",
      "Équilibrage & économie",
    ],
    stack: ["Aether Editor", "Figma", "Miro", "Twine", "Notion", "Excel", "Articy"],
    profiles: [
      {
        name: "Camille Dubois",
        role: "Directrice créative",
        years: 15,
        bio: "Gardienne de la vision, Camille s'assure que chaque jeu raconte quelque chose d'unique.",
        skills: ["Vision créative", "Game direction", "Narration"],
      },
      {
        name: "Kenji Watanabe",
        role: "Lead systems designer",
        years: 10,
        bio: "Kenji architecture les boucles de gameplay et les économies qui retiennent les joueurs.",
        skills: ["Systems design", "Économie", "Progression"],
      },
      {
        name: "Olivia Bennett",
        role: "Level designer senior",
        years: 8,
        bio: "Olivia sculpte le rythme des niveaux pour guider l'émotion sans jamais brider la liberté.",
        skills: ["Level design", "Pacing", "Encounter design"],
      },
      {
        name: "Lucas Fontaine",
        role: "Narrative designer",
        years: 7,
        bio: "Lucas tisse les récits ramifiés et les dialogues qui donnent du poids à chaque choix.",
        skills: ["Écriture", "Branching", "Worldbuilding"],
      },
      {
        name: "Mei Lin",
        role: "Game designer technique",
        years: 6,
        bio: "Pont entre design et code, Mei prototype rapidement les idées pour valider le fun au plus tôt.",
        skills: ["Prototypage", "Scripting", "Équilibrage"],
      },
    ],
  },

  production: {
    slug: "production",
    name: "Production",
    icon: "📊",
    hue: 175,
    tagline: "Orchestrer le chaos créatif.",
    mission:
      "L'équipe Production coordonne les talents, les plannings et les budgets. Nous protégeons la créativité des équipes en garantissant que les projets sortent à temps et dans de bonnes conditions.",
    focus: [
      "Gestion de projet & planning",
      "Coordination inter-équipes",
      "Budget & ressources",
      "Bien-être des équipes & qualité de vie",
    ],
    stack: ["Jira", "Notion", "Confluence", "Miro", "Slack", "Google Workspace"],
    profiles: [
      {
        name: "Sarah Cohen",
        role: "Directrice de production",
        years: 16,
        bio: "Sarah pilote le portefeuille de projets du studio et veille à un développement durable et humain.",
        skills: ["Gestion de portefeuille", "Stratégie", "Leadership"],
      },
      {
        name: "David N'Diaye",
        role: "Producteur senior",
        years: 11,
        bio: "David accompagne Aetherion de la pré-production au lancement, sereinement.",
        skills: ["Planning", "Risk management", "Communication"],
      },
      {
        name: "Elena Petrova",
        role: "Productrice associée",
        years: 7,
        bio: "Elena fluidifie le quotidien des équipes et fait sauter les blocages avant qu'ils ne grossissent.",
        skills: ["Scrum", "Coordination", "Suivi de prod"],
      },
      {
        name: "James Carter",
        role: "Chef de projet live",
        years: 8,
        bio: "James gère les jeux service comme Celestia, des saisons aux mises à jour communautaires.",
        skills: ["Live ops", "Roadmap", "Communauté"],
      },
    ],
  },

  audio: {
    slug: "audio",
    name: "Audio",
    icon: "🎧",
    hue: 40,
    tagline: "Le son qui fait battre le cœur du jeu.",
    mission:
      "L'équipe Audio compose la musique, conçoit le sound design et dirige le doublage. Le son est notre langage invisible : il porte l'émotion, l'information et l'immersion.",
    focus: [
      "Composition musicale",
      "Sound design & bruitage",
      "Audio interactif & implémentation",
      "Direction de doublage",
    ],
    stack: ["Wwise", "FMOD", "Ableton Live", "Pro Tools", "Reaper", "Aether Engine"],
    profiles: [
      {
        name: "Antoine Mercier",
        role: "Directeur audio",
        years: 14,
        bio: "Antoine signe les bandes-son orchestrales qui ont fait la réputation sonore du studio.",
        skills: ["Composition", "Orchestration", "Direction"],
      },
      {
        name: "Ji-woo Park",
        role: "Sound designer senior",
        years: 9,
        bio: "Ji-woo façonne les textures sonores d'Hollow Echoes et de nos univers les plus immersifs.",
        skills: ["Sound design", "Field recording", "Wwise"],
      },
      {
        name: "Clara Rossi",
        role: "Ingénieure audio interactif",
        years: 6,
        bio: "Clara connecte la musique au gameplay pour des transitions invisibles et réactives.",
        skills: ["Audio interactif", "FMOD", "Mix"],
      },
    ],
  },

  qa: {
    slug: "qa",
    name: "Qualité & Tests",
    icon: "🛡️",
    hue: 140,
    tagline: "Le dernier rempart avant les joueurs.",
    mission:
      "L'équipe QA garantit la qualité, la stabilité et l'accessibilité de nos jeux. Nous traquons les bugs, testons l'expérience et défendons le point de vue du joueur à chaque étape.",
    focus: [
      "Tests fonctionnels & non-régression",
      "Automatisation des tests",
      "Accessibilité & conformité",
      "Remontée & suivi des bugs",
    ],
    stack: ["Jira", "TestRail", "Python", "Selenium", "Aether Test Suite"],
    profiles: [
      {
        name: "Mohammed Al-Rashid",
        role: "Responsable QA",
        years: 12,
        bio: "Mohammed structure les stratégies de test et défend des standards de qualité élevés.",
        skills: ["Stratégie QA", "Management", "Process"],
      },
      {
        name: "Hannah Schmidt",
        role: "Ingénieure QA automatisation",
        years: 7,
        bio: "Hannah automatise les tests répétitifs pour libérer du temps aux tests créatifs.",
        skills: ["Automatisation", "Python", "CI/CD"],
      },
      {
        name: "Diego Ramirez",
        role: "Spécialiste accessibilité",
        years: 6,
        bio: "Diego s'assure que nos jeux soient jouables par le plus grand nombre, sans compromis.",
        skills: ["Accessibilité", "UX testing", "Conformité"],
      },
    ],
  },
};

window.DEPARTMENT_ORDER = ["programmation", "art", "design", "production", "audio", "qa"];
