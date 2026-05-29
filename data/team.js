/* ============================================================
   MAISON BONBON — Secteurs de la maison & profils (fictifs)
   Donnée globale: window.DEPARTMENTS (objet indexé par slug)
   ============================================================ */
window.DEPARTMENTS = {
  patisserie: {
    slug: "patisserie",
    name: "Pâtisserie",
    icon: "🍰",
    hue: 330,
    tagline: "L'art du goût et de l'équilibre.",
    mission:
      "L'atelier Pâtisserie imagine et réalise nos entremets, tartes et desserts signatures. Du sourcing des fruits à l'assemblage final, chaque création est pensée pour offrir un équilibre parfait entre texture, parfum et émotion.",
    focus: [
      "Entremets & gâteaux de voyage",
      "Tartes & desserts de saison",
      "Crèmes, mousses & inserts",
      "Recherche & création de nouvelles recettes",
    ],
    stack: ["Vanille de Madagascar", "Fruits de saison", "Chocolat de couverture", "Tempérage", "Glaçage miroir", "Dressage"],
    profiles: [
      { name: "Camille Laurent", role: "Chef pâtissière", years: 18, bio: "Cheffe d'orchestre de l'atelier, Camille signe les créations signatures et garde le cap sur l'exigence du goût.", skills: ["Création", "Entremets", "Management"] },
      { name: "Hugo Tanaka", role: "Sous-chef pâtissier", years: 10, bio: "Spécialiste des textures, Hugo a mis au point notre Paris-Brest et notre crème mousseline maison.", skills: ["Pralinés", "Crèmes", "Précision"] },
      { name: "Amina Diallo", role: "Pâtissière de tour", years: 7, bio: "Reine des tartes de saison, Amina sélectionne les meilleurs fruits avec les producteurs locaux.", skills: ["Tartes", "Fruits", "Saisonnalité"] },
      { name: "Sofia Reyes", role: "Pâtissière entremets", years: 6, bio: "Sofia façonne mousses et inserts pour des entremets aussi beaux que bons.", skills: ["Mousses", "Glaçage", "Dressage"] },
    ],
  },

  boulangerie: {
    slug: "boulangerie",
    name: "Boulangerie & Viennoiserie",
    icon: "🥐",
    hue: 40,
    tagline: "Le feuilletage et le levain, chaque matin.",
    mission:
      "L'équipe Boulangerie pétrit, façonne et cuit nos pains, croissants et viennoiseries chaque matin. Au beurre AOP et au levain naturel, nous perpétuons un savoir-faire artisanal exigeant.",
    focus: [
      "Viennoiseries au beurre AOP",
      "Pains au levain naturel",
      "Feuilletage maison",
      "Cuissons du matin",
    ],
    stack: ["Beurre d'Isigny AOP", "Levain naturel", "Tourage", "Pétrissage lent", "Four à sole", "Pousse contrôlée"],
    profiles: [
      { name: "Thomas Leroy", role: "Chef boulanger", years: 16, bio: "Gardien du levain de la maison, Thomas veille à la régularité et au goût de chaque fournée.", skills: ["Levain", "Pains spéciaux", "Cuisson"] },
      { name: "Eric Lindgren", role: "Chef tourier", years: 12, bio: "Maître du feuilletage, Eric réalise nos croissants et kouign-amann à la main.", skills: ["Tourage", "Viennoiserie", "Feuilletage"] },
      { name: "Nadia Haddad", role: "Boulangère", years: 8, bio: "Nadia façonne pains et brioches avec une régularité impressionnante.", skills: ["Façonnage", "Brioches", "Pétrissage"] },
    ],
  },

  chocolaterie: {
    slug: "chocolaterie",
    name: "Chocolaterie & Confiserie",
    icon: "🍫",
    hue: 25,
    tagline: "Le cacao et le sucre, sublimés.",
    mission:
      "Notre chocolaterie travaille les grands crus de cacao et confectionne bonbons, tablettes et confiseries. Tempérage précis, ganaches parfumées et enrobages délicats : la maîtrise du chocolat dans tous ses états.",
    focus: [
      "Bonbons de chocolat & ganaches",
      "Tablettes & moulages",
      "Confiseries & caramels",
      "Macarons (coques & ganaches)",
    ],
    stack: ["Grands crus de cacao", "Tempérage", "Enrobage", "Pralinés maison", "Caramel beurre salé", "Moulage"],
    profiles: [
      { name: "Antoine Mercier", role: "Chef chocolatier", years: 15, bio: "Antoine sélectionne les fèves et compose des ganaches d'une finesse remarquable.", skills: ["Tempérage", "Ganaches", "Sourcing cacao"] },
      { name: "Ji-woo Park", role: "Confiseur", years: 9, bio: "Caramels, guimauves et pâtes de fruits : Ji-woo régale les amateurs de douceurs.", skills: ["Caramel", "Confiserie", "Pâtes de fruits"] },
      { name: "Clara Rossi", role: "Chocolatière macarons", years: 6, bio: "Clara perfectionne nos coques de macarons et leurs ganaches parfumées.", skills: ["Macarons", "Ganache montée", "Précision"] },
    ],
  },

  cakedesign: {
    slug: "cakedesign",
    name: "Cake Design & Décoration",
    icon: "🎂",
    hue: 300,
    tagline: "Donner vie aux gâteaux de vos rêves.",
    mission:
      "L'atelier Cake Design crée les pièces montées, wedding cakes et gâteaux personnalisés. Entre pâte à sucre, modelage et fleurs en sucre, nous transformons chaque événement en chef-d'œuvre comestible.",
    focus: [
      "Wedding cakes & pièces montées",
      "Number cakes & gâteaux d'anniversaire",
      "Modelage & fleurs en sucre",
      "Conseil & personnalisation client",
    ],
    stack: ["Pâte à sucre", "Modelage", "Fleurs en sucre", "Aérographe", "Ganache de couverture", "Structures à étages"],
    profiles: [
      { name: "Yuki Nakamura", role: "Cheffe cake designer", years: 13, bio: "Yuki imagine des gâteaux spectaculaires et accompagne les clients de l'idée à la réalisation.", skills: ["Design", "Pâte à sucre", "Conseil"] },
      { name: "Priya Sharma", role: "Décoratrice", years: 7, bio: "Spécialiste des fleurs en sucre, Priya apporte la touche poétique à chaque pièce.", skills: ["Fleurs en sucre", "Modelage", "Couleurs"] },
      { name: "Olivia Bennett", role: "Cake designer", years: 6, bio: "Olivia maîtrise les structures à étages et les finitions impeccables.", skills: ["Structures", "Finitions", "Aérographe"] },
    ],
  },

  production: {
    slug: "production",
    name: "Laboratoire & Production",
    icon: "🧁",
    hue: 160,
    tagline: "L'organisation au service de la gourmandise.",
    mission:
      "L'équipe Production coordonne le laboratoire : plannings de fabrication, approvisionnement, hygiène et qualité. Nous garantissons que chaque création arrive en boutique fraîche, parfaite et dans les temps.",
    focus: [
      "Planning de fabrication",
      "Approvisionnement & matières premières",
      "Hygiène & sécurité alimentaire (HACCP)",
      "Contrôle qualité & fraîcheur",
    ],
    stack: ["HACCP", "Gestion des stocks", "Traçabilité", "Chaîne du froid", "Planning", "Contrôle qualité"],
    profiles: [
      { name: "Sarah Cohen", role: "Responsable production", years: 17, bio: "Sarah orchestre le laboratoire et veille au respect des délais et de la qualité.", skills: ["Organisation", "Qualité", "Management"] },
      { name: "David N'Diaye", role: "Responsable approvisionnement", years: 11, bio: "David sélectionne les meilleures matières premières et fidélise nos producteurs.", skills: ["Sourcing", "Stocks", "Négociation"] },
      { name: "Elena Petrova", role: "Référente hygiène (HACCP)", years: 8, bio: "Elena garantit une hygiène irréprochable et la traçabilité de chaque ingrédient.", skills: ["HACCP", "Traçabilité", "Sécurité"] },
    ],
  },

  boutique: {
    slug: "boutique",
    name: "Boutique & Accueil",
    icon: "🛍️",
    hue: 345,
    tagline: "Le sourire qui accompagne chaque douceur.",
    mission:
      "Notre équipe de vente accueille, conseille et fait vivre l'expérience Maison Bonbon en boutique. Du choix d'un macaron à la commande d'un wedding cake, elle est le visage chaleureux de la maison.",
    focus: [
      "Accueil & conseil client",
      "Vente & mise en valeur des vitrines",
      "Commandes personnalisées",
      "Fidélisation & expérience client",
    ],
    stack: ["Sens du service", "Conseil produit", "Vitrine & mise en scène", "Encaissement", "Prise de commande", "Écoute"],
    profiles: [
      { name: "Marco Bianchi", role: "Responsable boutique", years: 12, bio: "Marco anime l'équipe de vente et veille à l'excellence de l'accueil.", skills: ["Service", "Management", "Relation client"] },
      { name: "Léa Moreau", role: "Conseillère de vente", years: 6, bio: "Léa connaît chaque produit sur le bout des doigts et guide les gourmands.", skills: ["Conseil", "Vitrine", "Vente"] },
      { name: "Mei Lin", role: "Chargée des commandes", years: 5, bio: "Mei coordonne les commandes personnalisées avec le sourire et la précision.", skills: ["Commandes", "Organisation", "Écoute"] },
    ],
  },
};

window.DEPARTMENT_ORDER = ["patisserie", "boulangerie", "chocolaterie", "cakedesign", "production", "boutique"];
