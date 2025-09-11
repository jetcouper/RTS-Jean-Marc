# Échéancier Projet AoEw - Reprise et Enrichissement
## Répartition des équipes (6 membres = 3 sous-équipes de 2 personnes)

### **Équipe A - Core & IA** (2 membres)
- **Focus principal** : Analyse du code existant, suppression réseau, IA et mécaniques de jeu
- **Responsabilités** : Architecture, intelligences artificielles, modes de jeu

### **Équipe B - Interface & Configuration** (2 membres)  
- **Focus principal** : Interface utilisateur, page de configuration, sauvegarde/chargement
- **Responsabilités** : Tkinter, lobby, gestion des parties, expérience utilisateur

### **Équipe C - Gameplay & Performance** (2 membres)
- **Focus principal** : Path-finding, fog-of-war, enrichissements de gameplay, optimisations
- **Responsabilités** : Algorithmes de déplacement, graphismes, nouvelles mécaniques

---

## **PHASE 1 : ANALYSE ET CONCEPTION (Semaines 1-3)**

### **Semaine 1**
**Équipe A: Ugo et Sean** :
- Analyse complète du code existant (architecture, composants)
- Identification des éléments réseau à supprimer
- Documentation de la boucle de jeu actuelle
- Compréhension du système joueur humain + IAs

**Équipe B Peterly et Antoine** :
- Analyse de l'interface Tkinter existante
- Étude du lobby actuel et besoins de transformation
- Documentation des interactions utilisateur
- Planification de l'interface de configuration

**Équipe C Fred et Alexiane** :
- Analyse du système de déplacement actuel
- Étude de la grille invisible et du terrain
- Recherche sur les algorithmes de path-finding (A*)
- Documentation des mécaniques de combat existantes

### **Semaine 2**
**Équipe A** :
- Purge du code réseau (commentaires et fonctionnalités)
- Tests de stabilité post-suppression
- Conception des 3 profils d'IA (Guerrière, Commerciale, Sage)
- Définition des comportements de base des IAs

**Équipe B** :
- Maquettage de la page de configuration
- Conception du système de sauvegarde (structure des données)
- Planification des améliorations visuelles avec Pillow
- Définition des paramètres configurables

**Équipe C** :
- Conception de l'algorithme de path-finding
- Planification du fog-of-war minimal
- Analyse des performances actuelles
- Conception des nouvelles mécaniques de combat

### **Semaine 3**
**Équipe A** :
- Finalisation du nettoyage réseau
- Implémentation des IAs naïves (base)
- Tests de compatibilité du modèle joueur/IA
- Documentation des modifications

**Équipe B** :
- Prototypage de l'interface de configuration
- Implémentation de base de la sauvegarde
- Tests des paramètres de jeu
- Intégration avec le système existant

**Équipe C** :
- Implémentation de base du path-finding
- Prototype de fog-of-war simple
- Tests de performance initiaux
- Intégration avec la grille existante

---

## **PHASE 2 : SPRINT 1 - FONDATIONS (Semaines 4-6)**

### **Semaine 4**
**Équipe A** :
- **IAs naïves complètes** :
  - Recherche de ressources automatique
  - Construction aléatoire de bâtiments
  - Croissance de population basique
- Tests des comportements IA vs joueur humain

**Équipe B** :
- **Page de configuration fonctionnelle** :
  - Sélection nombre d'IAs (limite 5 couleurs)
  - Configuration random seed
  - Sélection type de partie
- Interface de chargement des parties sauvegardées

**Équipe C** :
- **Path-finding opérationnel** :
  - Évitement des obstacles (murs, structures)
  - Intégration avec le système de déplacement
  - Détection de collisions améliorée
- **Combat simple** fonctionnel

### **Semaine 5**
**Équipe A** :
- Amélioration des IAs naïves (efficacité)
- Implémentation des modes de victoire :
  - Conquête totale
  - Structures clés
  - Paix durable/alliances
- Tests des différents modes de jeu

**Équipe B** :
- **Système de sauvegarde complet** :
  - Sauvegarde état complet (unités, ressources, terrain)
  - Chargement fiable des parties
  - Gestion des erreurs de fichiers
- Améliorations visuelles avec Pillow (textures de base)

**Équipe C** :
- **Fog-of-war minimal** :
  - Système basé sur la grille
  - Optimisé pour les performances Python
  - Révélation progressive du terrain
- Enrichissement des mécaniques de combat

### **Semaine 6**
**Équipe A** :
- Tests d'intégration des IAs avec tous les modes
- Débogage des interactions joueur-IA
- Documentation des comportements IA
- Préparation pour les IAs avec personnalités

**Équipe B** :
- Tests complets sauvegarde/chargement
- Intégration finale de la page de configuration
- Tests des paramètres dynamiques
- Polissage de l'interface utilisateur

**Équipe C** :
- Optimisation des performances path-finding + fog-of-war
- Tests de charge (multiple unités)
- Integration complète avec le système de combat
- Préparation pour les effets graphiques avancés

---

## **PHASE 3 : SPRINT 2 - PERSONNALITÉS ET RAFFINEMENT (Semaines 7-9)**

### **Semaine 7**
**Équipe A** :
- **IAs avec personnalités distinctes** :
  - **Guerrière** : Focus conquête, attaques agressives
  - **Commerciale** : Accumulation ressources, échanges
  - **Sage** : Développement sciences/magie, structures avancées
- Implémentation des niveaux de difficulté (facile, moyen, difficile)

**Équipe B** :
- **Enrichissement interface** :
  - Animations via extraction GIF (compréhension système existant)
  - Améliorations graphiques Pillow avancées
  - Interface plus immersive
- Configuration avancée des personnalités IA

**Équipe C** :
- **Action de groupe intelligente** :
  - Coordination multiple unités
  - Formations de combat
  - Déplacements de groupe optimisés
- **Effets graphiques améliorés** directement en Tkinter/Canvas

### **Semaine 8**
**Équipe A** :
- **Mécaniques politiques et commerce** :
  - Traités de non-agression
  - Système d'échange/troc
  - Alliances dynamiques
- Tests des interactions entre personnalités IA différentes

**Équipe B** :
- **Enrichissement contenu** :
  - Nouveaux personnages/unités
  - Nouveaux bâtiments et outils
  - Diversification des biomes
- Intégration graphique des nouveaux éléments

**Équipe C** :
- **Système magie/religion/sciences** :
  - Conception et implémentation de base
  - Intégration avec les personnalités IA
  - Effets visuels associés
- Performance et optimisation continue

### **Semaine 9**
**Équipe A** :
- Tests intensifs des 3 personnalités IA
- Équilibrage des comportements
- Tests des modes coopératifs (joueur + IA vs autres IAs)
- Documentation des stratégies IA

**Équipe B** :
- Tests d'usage complets de l'interface
- Validation de tous les paramètres de configuration
- Tests de charge des sauvegardes
- Finalisation des améliorations visuelles

**Équipe C** :
- Optimisation finale des algorithmes
- Tests de performance à grande échelle
- Finalisation des nouveaux systèmes de jeu
- Intégration de tous les enrichissements

---

## **PHASE 4 : SPRINT 3 - FINALISATION ET POLISH (Semaines 10-12)**

### **Semaine 10**
**Équipe A** :
- **Débogage à grande échelle** :
  - Implémentation try/except généralisé
  - Prévention des crashes algorithmiques
  - Robustesse des IAs
- Tests croisés par les autres équipes

**Équipe B** :
- **Tests d'usage finaux** :
  - Tests par membres d'autres équipes
  - Validation de toutes les fonctionnalités
  - Correction des bugs interface
- Préparation de la démonstration finale

**Équipe C** :
- **Raffinement algorithmes comportementaux** :
  - Optimisation des décisions IA
  - Amélioration de l'intelligence locale
  - Performance finale
- Tests de tous les enrichissements de gameplay

### **Semaine 11**
**Toutes les équipes** :
- **Intégration finale** et tests système complets
- **Documentation code** et commentaires
- **Préparation démonstrations** des 3 modes de jeu
- **Rédaction rapports** individuels sur utilisation des IA
- **Finalisation fichier Excel** méthode Jean-Marc

### **Semaine 12**
**Toutes les équipes** :
- **Démonstrations finales** :
  - Mode Conquête avec IA Guerrière
  - Mode Construction avec IA Sage  
  - Mode Pacification avec IA Commerciale
- **Validation path-finding** (contournement murs)
- **Validation configuration** (random seed, types de parties)
- **Livraison finale** avec tous les délivrables

---

## **Livrables par Équipe**

### **Équipe A - Core & IA**
- Code IA documenté avec 3 personnalités
- Rapport d'analyse du code existant
- Documentation des comportements et stratégies IA
- Tests de validation des modes de jeu

### **Équipe B - Interface & Configuration**  
- Page de configuration fonctionnelle
- Système de sauvegarde/chargement complet
- Améliorations visuelles (Pillow + Tkinter)
- Interface utilisateur finalisée

### **Équipe C - Gameplay & Performance**
- Algorithme de path-finding opérationnel
- Système de fog-of-war minimal
- Enrichissements de gameplay (combat, magie, etc.)
- Optimisations de performance

### **Tous** (collaboratif)
- Rapport personnel utilisation des IA chatbots
- Fichier Excel gestion projet (méthode Jean-Marc)
- Code source final documenté
- Journal des contributions individuelles