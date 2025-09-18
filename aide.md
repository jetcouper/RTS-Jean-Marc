# ÉTAT INITIAL DU JEU

0. Chaque joueur est identifié par son nom, affiché dans la barre de titre et dans la section de commande, à droite
1. L'aire de jeu fait 4000×4000 pixels
2. Les ressources du joueur sont affichées dans le HUD (Heads Up Display)
3. Boutons « Chat » et « Aide » dans le HUD (voir plus bas)
4. La couleur de fond du HUD correspond à votre couleur
5. L'aire de jeu est peuplée de biotopes
   - Régions de biotopes de 5 types : « arbres », « eau », « marais », « roche », « aureus »
6. Les régions « eau » et « marais » ne sont pas exploitées
7. AU DÉPART : la carte se positionne (scroll) pour mettre la maison d'origine de chaque joueur dans la section visible
8. La nourriture s'acquiert par le ramassage de baies
   - NOTE : les arbustes de baies sont générés aléatoirement et progressivement
9. Des cerfs peuplent aussi, aléatoirement, l'aire de jeu dès le départ ; ils ne sont pas encore exploitables
10. Une minicarte est créée et affiche initialement les biotopes
11. Les bâtiments sont représentés dans la minicarte
12. La minicarte est cliquable pour effectuer des déplacements dans l'aire de jeu

# MANIPULATION DANS L'AIRE DE JEU

## CRÉATION DE PERSONNAGES
- **Bouton-1 sur une maison** : crée un ouvrier attaché à cette maison
- **Bouton-1 sur une caserne** : crée un soldat

## MANIPULATION DES PERSONNAGES
- **Bouton-1 sur le terrain** : désélectionne tout
- **Bouton-1 sur les personnages** : sélectionne le personnage, affiche une barre jaune, affiche les commandes associées
- **Bouton-1 sur une ressource (si des ouvriers sont sélectionnés)** : commande d'aller ramasser cette ressource
  - NOTE : les ressources disponibles sont :
    - arbres → bois
    - roches → roche
    - aureus → aureus
    - baies → nourriture
  - ATTENTION : lorsque la ressource est épuisée, l'ouvrier s'arrête simplement et envoie un message aux autres ouvriers
- **Bouton-2 sur le terrain (si un personnage est sélectionné)** : dirige le personnage à cet endroit
- **Maj + Bouton-1, glisser, relâcher sur le terrain** : sélectionne le groupe de vos personnages à l'intérieur

## CRÉATION DE BÂTIMENT (si un personnage est choisi)
- **Bouton-1** : le bouton passe au vert (actif)
- **Bouton-3 sur le terrain** : construit le bâtiment choisi à cet endroit
  - ATTENTION : aucun test n'est effectué pour autoriser ou non le positionnement

# CHAT ET AIDE

1. Le chat permet l'envoi de messages à des joueurs spécifiques
   - NOTE : pas d'envoi de groupe pour le moment
2. Le bouton Chat change de couleur lorsqu'un joueur reçoit un message
3. Le chat fait apparaître un cadre dans la section gauche, en haut de la vue actuelle de la carte
4. Le bouton chat bascule la visibilité du cadre de chat (montre/cache)
5. Le chat se compose de la liste des messages, d'un menu déroulant pour choisir un joueur et d'un champ de saisie de texte
6. Le texte est envoyé avec la touche Entrée (le texte n'est pas supprimé du champ)
7. Le bouton aide affiche (et bascule) le cadre du texte d'aide
8. L'aide apparaît dans un cadre dans la section droite, en haut de la vue actuelle de la carte