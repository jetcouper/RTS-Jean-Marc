## - Encoding: UTF-8 -*-

import math
import random
import time
from AoEw_divers import *
from helper import Helper
from AoEw_biomes import *
from AoEw_batiments import *
from AoEw_persos import *
from AoEw_joueurs import *
from RTS_IA import *
from vue.fog import FogState, FogModel
from fog_memory import FogMemory




class Region():
    def __init__(self, parent, id, x, y, taillex, tailley, montype):
        self.parent = parent
        self.id = id
        self.debutx = x
        self.taillex = taillex
        self.debuty = y
        self.tailley = tailley
        self.montype = montype
        self.dicocases = {}

class Caseregion():
    def __init__(self, parent, id, x, y):
        self.parent = parent
        self.id = id
        self.montype = "plaine"
        self.ressources = {}
        self.x = x
        self.y = y

#######################  LE MODELE est la partie #######################
class Partie():
    valeurs = {"maison": {"nourriture": 10,
                          "arbre": 20,
                          "roche": 20,
                          "aureus": 2,
                          "delai": 50},
               "abri": {"nourriture": 10,
                        "arbre": 10,
                        "roche": 5,
                        "aureus": 1,
                        "delai": 30},
               "caserne": {"nourriture": 10,
                           "arbre": 10,
                           "roche": 5,
                           "aureus": 1,
                           "delai": 60},
               "usineballiste": {"nourriture": 10,
                                 "arbre": 10,
                                 "roche": 5,
                                 "aureus": 1,
                                 "delai": 80},
               "moulin": {"nourriture": 10,
                                 "arbre": 15,
                                 "roche": 10,
                                 "aureus": 2,
                                 "delai": 60}
               }

    def __init__(self, parent, nom_joueur_local, ia_info , mode_de_jeu):
        self.parent = parent
        self.nom_joueur = nom_joueur_local
        self.actions_a_faire = {}
        self.debut = int(time.time())
        self.aireX = 4000
        self.aireY = 4000
        # Decoupage de la surface
        self.taillecase = 20
        self.taillecarte = int(self.aireX / self.taillecase)
        self.cartecase = []
        self.make_carte_case()
        self.fog = FogModel(self.taillecarte, self.taillecarte)
        self.fog_memory = FogMemory(self)

        self.delaiprochaineaction = 20

        self.joueurs = {}
        self.classesbatiments = {"maison": Maison,
                                 "caserne": Caserne,
                                 "abri": Abri,
                                 "usineballiste": Usineballiste,
                                 "moulin": Moulin}
        self.classespersos = {"ouvrier": Ouvrier,
                              "soldat": Soldat,
                              "archer": Archer,
                              "chevalier": Chevalier,
                              "druide": Druide}
        self.ressourcemorte = []
        self.msggeneral = None
        self.msggeneraldelai = 30
        self.msggeneralcompteur = 0
        self.listebiotopes = []
        self.biotopes = {"daim": {},
                         "ours": {},
                         "arbre": {},
                         "roche": {},
                         "aureus": {},
                         "eau": {},
                         "marais": {},
                         "baie": {}}
        self.regions = {}

        self.regionstypes = [["arbre", 50, 20, 5, "forest green"],
                             ["eau", 10, 20, 12, "light blue"],
                             ["marais", 3, 8, 8, "DarkSeaGreen3"],
                             ["roche", 8, 3, 6, "gray60"],
                             ["aureus", 12, 3, 4, "gold2"], ]
        self.creer_regions()
        self.creer_biotopes()
        self.creer_population(ia_info)
        #self.ia_info = ia_info

    def trouver_valeurs(self):
        vals = Partie.valeurs
        return vals

    def montrer_msg_general(self, txt):
        self.msggeneral = txt

    def installer_batiment(self, nomjoueur, batiment):
        x1, y1, x2, y2 = self.parent.installer_batiment(nomjoueur, batiment)

        cartebatiment = self.get_carte_bbox(x1, y1, x2, y2)
        for i in cartebatiment:
            self.cartecase[i[1]][i[0]].montype = "batiment"
        batiment.cartebatiment = cartebatiment

    def position_libre_pour_batiment_complet(self, x, y, rayon=60):
        """
        Vérifie si un bâtiment peut être placé à la position (x, y) en tenant
        compte de tout le rayon autour du centre.
        - Aucun point du rayon ne doit être sur eau ou marais.
        - Empêche la proximité avec les ressources terrestres.
        """
        xmin = max(0, x - rayon)
        xmax = min(self.aireX - 1, x + rayon)
        ymin = max(0, y - rayon)
        ymax = min(self.aireY - 1, y + rayon)

        # Vérifie chaque case du rectangle englobant le rayon
        step = self.taillecase  # on peut aussi tester tous les pixels pour plus de sécurité
        for px in range(xmin, xmax, step):
            for py in range(ymin, ymax, step):
                case = self.trouver_case(px, py)
                if case.montype in ["eau", "marais"]:
                    return False

        # Vérifie la distance avec les ressources terrestres
        for bio in self.listebiotopes:
            if bio.montype in ["eau", "marais"]:
                continue
            if Helper.calcDistance(x, y, bio.x, bio.y) < rayon:
                return False

        return True
    def position_libre_pour_batiment(self, x, y, rayon=60):
        """
        Vérifie si un bâtiment peut être placé à la position (x, y).
        - Empêche les constructions sur l’eau ou les marais.
        - Empêche la proximité avec des ressources (arbres, roches, etc.)
        """
        # Vérifie la nature du terrain
        case = self.trouver_case(x, y)
        if case.montype in ["eau", "marais"]:
            return False

        # Vérifie qu’aucune ressource terrestre n’est trop proche
        for bio in self.listebiotopes:
            if bio.montype in ["eau", "marais"]:
                continue
            if Helper.calcDistance(x, y, bio.x, bio.y) < rayon:
                return False

        return True



    def creer_biotopes(self):
        # creer des daims éparpillés
        n = 20
        while n:
            x = random.randrange(self.aireX)
            y = random.randrange(self.aireY)
            case = self.trouver_case(x, y)
            if case.montype == "plaine":
                id = get_prochain_id()
                mondaim = Daim(self, id, x, y)
                self.biotopes["daim"][id] = mondaim
                self.listebiotopes.append(mondaim)
                n -= 1
                id = get_prochain_id()
                mondaim = Ours(self, id, x, y)
                self.biotopes["ours"][id] = mondaim
                self.listebiotopes.append(mondaim)
                n -= 1
        self.creer_biotope("arbre", "arbre", Arbre)
        self.creer_biotope("roche", "roche", Roche)
        self.creer_biotope("eau", "eau", Eau)
        self.creer_biotope("marais", "marais", Marais)
        self.creer_biotope("aureus", "aureus", Aureus)
        self.creer_baies_initiales(50)

    def creer_biotope(self, region, ressource, typeclasse):  # creation des forets
        typeressource = typeclasse.typeressource

        for cleregion in self.regions[region].keys():
            listecases = self.regions[region][cleregion].dicocases

            # Traitement spécial pour l'eau : remplir densément pour créer des lacs
            if ressource == "eau":
                # ÉTAPE 1 : Remplir toutes les cases avec de l'eau de base (dense)
                for cle, pos in listecases.items():
                    # Créer plusieurs éléments d'eau de base par case pour un effet de lac dense
                    nb_elements_par_case = random.randint(3, 6)  # 3 à 6 éléments par case
                    for _ in range(nb_elements_par_case):
                        x = random.randrange(self.taillecase)
                        y = random.randrange(self.taillecase)
                        xa = (pos.x * self.taillecase) + x
                        ya = (pos.y * self.taillecase) + y

                        # Utiliser uniquement l'eau de base
                        styleress = random.choice(typeclasse.typeressource_base)
                        id = get_prochain_id()
                        objet = typeclasse(self, id, styleress, xa, ya, ressource, cleregion, pos.id)
                        pos.ressources[id] = objet
                        self.biotopes[ressource][id] = (objet)
                        self.listebiotopes.append(objet)

                # ÉTAPE 2 : Ajouter des décorations de façon éparse (5-10% des cases)
                nb_decorations = int(len(listecases) * random.uniform(0.05, 0.10))
                cases_pour_decoration = random.sample(list(listecases.keys()), min(nb_decorations, len(listecases)))

                for cle in cases_pour_decoration:
                    pos = listecases[cle]
                    # 1 décoration par case choisie (réduit de 1-2 à 1)
                    for _ in range(1):
                        x = random.randrange(self.taillecase)
                        y = random.randrange(self.taillecase)
                        xa = (pos.x * self.taillecase) + x
                        ya = (pos.y * self.taillecase) + y

                        # Utiliser les éléments décoratifs
                        styleress = random.choice(typeclasse.typeressource_decoration)
                        id = get_prochain_id()
                        objet = typeclasse(self, id, styleress, xa, ya, ressource, cleregion, pos.id)
                        pos.ressources[id] = objet
                        self.biotopes[ressource][id] = (objet)
                        self.listebiotopes.append(objet)
            else:
                # Pour les ressources terrestres : génération par amas
                n_clusters = max(1, len(listecases) // 30)  # nombre de groupes de ressources dans la région
                taille_amas = random.randint(3, 8)  # ressources par groupe
                distance_cluster = 40  # distance moyenne entre les ressources du même groupe
                distance_min_entre_ressources = 30  # empêche les chevauchements
                distance_securite = 40  # distance minimale de l’e
                if ressource == "marais":
                    terrains_interdits = ["roche", "aureus", "arbre"]
                else:
                    terrains_interdits = ["eau", "marais"]

                tentatives_max = n_clusters * taille_amas * 10
                tentatives = 0
                creees = 0

                pos_centre = random.choice(list(listecases.values()))
                cx = (pos_centre.x * self.taillecase) + random.randrange(self.taillecase)
                cy = (pos_centre.y * self.taillecase) + random.randrange(self.taillecase)
                while creees < n_clusters * taille_amas and tentatives < tentatives_max:
                    tentatives += 1
                    # --- Si on commence un nouvel amas ---
                    if creees % taille_amas == 0:
                        pos_centre = random.choice(list(listecases.values()))
                        cx = (pos_centre.x * self.taillecase) + random.randrange(self.taillecase)
                        cy = (pos_centre.y * self.taillecase) + random.randrange(self.taillecase)
                    # --- Génération autour du centre ---
                    angle = random.uniform(0, 360)
                    dist = random.randint(10, distance_cluster)
                    xa, ya = Helper.getAngledPoint(angle, dist, cx, cy)


                    case_cible = self.trouver_case(xa, ya)
                    if case_cible.montype in terrains_interdits:
                        continue

                    # Trop proche de l’eau ?
                    proche_eau = False
                    for dx in range(-distance_securite, distance_securite + 1, self.taillecase):
                        for dy in range(-distance_securite, distance_securite + 1, self.taillecase):
                            case_voisine = self.trouver_case(xa + dx, ya + dy)
                            if case_voisine.montype == "eau":
                                proche_eau = True
                                break
                        if proche_eau:
                            break
                    if proche_eau:
                        continue



                    # Trop proche d’une autre ressource ?
                    chevauche = False
                    for autre in self.listebiotopes:
                        if autre.montype in ["eau", "marais"]:
                            continue
                        if Helper.calcDistance(xa, ya, autre.x, autre.y) < distance_min_entre_ressources:
                            chevauche = True
                            break
                    if chevauche:
                        continue


                    # Vérif spéciale : marais collés à l’eau
                    if ressource == "marais":
                        voisin_eau = False
                        for dx in [-self.taillecase, 0, self.taillecase]:
                            for dy in [-self.taillecase, 0, self.taillecase]:
                                case_voisine = self.trouver_case(xa + dx, ya + dy)
                                if case_voisine.montype == "eau":
                                    voisin_eau = True
                                    break
                            if voisin_eau:
                                break
                        if not voisin_eau:
                            continue
                    # Placement validé 🎯
                    styleress = random.choice(typeressource)
                    id = get_prochain_id()
                    objet = typeclasse(self, id, styleress, xa, ya, ressource, cleregion, pos_centre.id)
                    pos_centre.ressources[id] = objet
                    self.biotopes[ressource][id] = objet
                    self.listebiotopes.append(objet)
                    creees += 1

    def creer_baies_initiales(self, nombre):
        """Crée toutes les baies en une seule fois au début du jeu"""
        typeressource = Baie.typeressource
        n = nombre
        while n > 0:
            x = random.randrange(self.aireX)
            y = random.randrange(self.aireY)
            case = self.trouver_case(x, y)
            if case.montype == "plaine":
                id = get_prochain_id()
                img = random.choice(typeressource)
                baie = Baie(self, id, img, x, y, "baie")
                self.biotopes["baie"][id] = baie
                self.listebiotopes.append(baie)
                n -= 1


    def creer_regions(self):
        for reg in self.regionstypes:
            nomregion = reg[0]
            nbrreg = reg[1]
            minreg = reg[2]
            rndreg = reg[3]
            coulreg = reg[4]
            self.regions[nomregion] = {}
            for i in range(nbrreg):
                listecasereg = []
                # trouve une case dans la carte
                x = random.randrange(self.taillecarte)
                y = random.randrange(self.taillecarte)
                # calcule la largeur (x) et hauteur(y) de la regtion
                taillex = random.randrange(reg[3]) + reg[2]
                tailley = random.randrange(reg[3]) + reg[2]
                # verifie que la region de deborde pas vers l'exterieur du jeu
                # (ex: si le centre de la region est case 1,1
                # et on la veut 10 case de large, cette region debuterait a la case -5, qui n'existe pas
                x0 = x - int(taillex / 2)
                if x0 < 0:
                    x0 = 0

                x1 = x + int(taillex / 2)
                if x1 > self.taillecarte - 1:
                    x1 = self.taillecarte - 1

                y0 = y - int(tailley / 2)
                if y0 < 0:
                    y0 = 0

                y1 = y + int(tailley / 2)
                if y1 > self.taillecarte - 1:
                    y1 = self.taillecarte - 1

                taillex = x1 - x0
                tailley = y1 - y0

                id = get_prochain_id()
                newregion = Region(self, id, x0, y0, taillex, tailley, nomregion)

                dicoreg = {}
                for i in range(tailley):
                    for j in range(taillex):
                        self.cartecase[y0 + i][x0 + j].parent = newregion
                        self.cartecase[y0 + i][x0 + j].montype = nomregion
                        # listereg.append(self.cartecase[y0+i][x0+j])
                        casereg = self.cartecase[y0 + i][x0 + j]
                        casereg.parent = newregion
                        dicoreg[casereg.id] = casereg

                newregion.dicocases = dicoreg
                self.regions[nomregion][id] = newregion

    def creer_population(self, ia_info):
        noms_joueurs = [self.nom_joueur]
        for i in range(len(ia_info)):
            noms_joueurs.append("IA_"+str(i))

        couleurs = [["O", "orange"], ["R", "red"], ["B", "blue"], ["J", "yellow"], ["V", "lightgreen"]]

        nb_joueurs = len(noms_joueurs)
        positions_joueurs = []  # Liste pour stocker les positions déjà attribuées

        # Marge de sécurité depuis les bords
        marge = 200

        # Distance minimale entre deux joueurs (augmentée considérablement)
        distance_min_joueurs = 1500  # Distance minimale entre maisons

        # Positions prédéfinies pour différents nombres de joueurs
        if nb_joueurs == 2:
            # Pour 2 joueurs : coins opposés en diagonal
            positions_predefinies = [
                [marge, marge],  # Coin haut-gauche
                [self.aireX - marge, self.aireY - marge]  # Coin bas-droite
            ]
        elif nb_joueurs == 3:
            # Pour 3 joueurs : triangle
            positions_predefinies = [
                [marge, marge],  # Coin haut-gauche
                [self.aireX - marge, marge],  # Coin haut-droite
                [self.aireX // 2, self.aireY - marge]  # Centre-bas
            ]
        elif nb_joueurs == 4:
            # Pour 4 joueurs : un dans chaque coin
            positions_predefinies = [
                [marge, marge],  # Coin haut-gauche
                [self.aireX - marge, marge],  # Coin haut-droite
                [marge, self.aireY - marge],  # Coin bas-gauche
                [self.aireX - marge, self.aireY - marge]  # Coin bas-droite
            ]
        else:
            # Pour 5+ joueurs : distribution en cercle
            positions_predefinies = []
            centre_x = self.aireX // 2
            centre_y = self.aireY // 2
            rayon = min(self.aireX, self.aireY) // 2 - marge

            for i in range(nb_joueurs):
                angle = (2 * math.pi * i) / nb_joueurs
                x = int(centre_x + rayon * math.cos(angle))
                y = int(centre_y + rayon * math.sin(angle))
                positions_predefinies.append([x, y])

        z = 0
        for idx, nom_joueur in enumerate(noms_joueurs):
            id = get_prochain_id()
            coul = couleurs.pop() if couleurs else [["G", "green"]][0]

            # Utiliser la position prédéfinie
            pos_cible = positions_predefinies[idx]
            x_base, y_base = pos_cible

            # Chercher une position valide proche de la position cible
            position_trouvee = False
            rayon_recherche = 100
            max_tentatives = 1000

            for tentative in range(max_tentatives):
                # Chercher autour de la position cible
                if tentative < 100:
                    # D'abord essayer très proche
                    x = x_base + random.randrange(-rayon_recherche, rayon_recherche)
                    y = y_base + random.randrange(-rayon_recherche, rayon_recherche)
                else:
                    # Élargir la zone de recherche si nécessaire
                    rayon_elargi = rayon_recherche + (tentative - 100) * 2
                    x = x_base + random.randrange(-rayon_elargi, rayon_elargi)
                    y = y_base + random.randrange(-rayon_elargi, rayon_elargi)

                # Vérifier que la position est dans les limites
                if x < marge or x > self.aireX - marge or y < marge or y > self.aireY - marge:
                    continue

                # Vérifier que c'est une plaine
                case = self.trouver_case(x, y)
                if case.montype != "plaine":
                    continue

                # Vérifier la distance avec les autres joueurs déjà placés
                trop_proche = False
                for pos_existante in positions_joueurs:
                    distance = Helper.calcDistance(x, y, pos_existante[0], pos_existante[1])
                    if distance < distance_min_joueurs:
                        trop_proche = True
                        break

                if trop_proche:
                    continue

                # Position valide trouvée !
                position_trouvee = True
                positions_joueurs.append([x, y])

                if z == 0:
                    self.joueurs[nom_joueur] = Joueur(self, id, nom_joueur, coul, x, y)
                else:
                    self.joueurs[nom_joueur] = IA(self, id, nom_joueur, coul, x, y, ia_info[z - 1])

                break

            if not position_trouvee:
                # Fallback : utiliser la position de base même si pas idéale
                print(f"⚠️  Position de secours utilisée pour {nom_joueur}")
                x, y = x_base, y_base
                case = self.trouver_case(x, y)
                while case.montype != "plaine":
                    x = random.randrange(marge, self.aireX - marge)
                    y = random.randrange(marge, self.aireY - marge)
                    case = self.trouver_case(x, y)

                positions_joueurs.append([x, y])
                if z == 0:
                    self.joueurs[nom_joueur] = Joueur(self, id, nom_joueur, coul, x, y)
                else:
                    self.joueurs[nom_joueur] = IA(self, id, nom_joueur, coul, x, y, ia_info[z - 1])

            z += 1

    ################ Zone pour méthodes AI ###############################################
    def objets_dans_rayon(self, x, y, r):
    # Retourne des générateurs (ou listes) d’objets candidats, on garde simple au début.
    # 1) Ressources (biotopes)
        ressources = []
        for typ, d in self.biotopes.items():
            for obj in d.values():
                # Filtre rapide par distance
                if Helper.calcDistance(x, y, obj.x, obj.y) <= r:
                    ressources.append(obj)           
      # 2) Persos & bâtiments de tous les joueurs
        persos = []
        batiments = []
        for j in self.joueurs.values():
            for dico_persos in j.persos.values():
                for p in dico_persos.values():
                    if getattr(p, "etat", "vivant") != "vivant":
                        continue
                    if Helper.calcDistance(x, y, p.x, p.y) <= r:
                        persos.append(p)
            for dico_bats in j.batiments.values():
                for b in dico_bats.values():
                    if getattr(b, "etat", "vivant") != "vivant":
                        continue
                    # Pour les bâtiments on prend leur centre; leur emprise est déjà marquée sur la carte au placement
                    # via installer_batiment, mais pas besoin d'aller jusqu'aux cases ici.
                    if Helper.calcDistance(x, y, b.x, b.y) <= r:
                        batiments.append(b)

        return persos, batiments, ressources
    

    
    #############################################################################

    def deplacer(self):
        for i in self.joueurs:
            self.joueurs[i].deplacer()

    def jouer_prochain_coup(self, cadrecourant):
        self.ressourcemorte = []
        ##################################################################
        # faire nouvelle action recu du serveur si on est au bon cadrecourant
        # ATTENTION : NE PAS TOUCHER 
        if cadrecourant in self.actions_a_faire:
            for i in self.actions_a_faire[cadrecourant]:
                print(i)
                self.joueurs[i[0]].actions[i[1]](i[2])
        ##################################################################

        # demander aux objets de s'activer
        for i in self.biotopes["daim"].keys():
            self.biotopes["daim"][i].deplacer()

        for i in self.biotopes["ours"].keys():
            self.biotopes["ours"][i].deplacer()

        for i in self.biotopes["eau"].keys():
            self.biotopes["eau"][i].jouer_prochain_coup()

        # demander aux objets de s'activer
        for i in self.joueurs.keys():
            self.joueurs[i].jouer_prochain_coup()

        # Gestion du fog of war
        self.maj_fog_pour_joueur(self.nom_joueur)
        self.fog_memory.memoriser_visible(self.nom_joueur)


        if self.msggeneral:
            self.msggeneralcompteur += 1
            if self.msggeneralcompteur == self.msggeneraldelai:
                self.msggeneral = ""
                self.msggeneralcompteur = 0

        self.faire_action_partie()
        t = int(time.time())
        msg = "cadre: " + str(cadrecourant) + " - secs: " + str(t - self.debut)
        self.msggeneral = msg

    def faire_action_partie(self):
        if self.delaiprochaineaction == 0:
            self.produire_action()
            self.delaiprochaineaction = random.randrange(20, 30)
        else:
            self.delaiprochaineaction -= 1

    def produire_action(self):
        #typeressource = Baie.typeressource
        #n = 1
        #while n:
        #    x = random.randrange(self.aireX)
        #    y = random.randrange(self.aireY)
        #    case = self.trouver_case(x, y)
        #    if case.montype == "plaine":
        #        id = get_prochain_id()
        #        img = random.choice(typeressource)
        #        baie = Baie(self, id, img, x, y, "baie")
        #        self.biotopes["baie"][id] = baie
        #        n -= 1
        #        self.parent.afficher_bio(baie)
        pass

    # VERIFIER CES FONCTIONS SUR LA CARTECASE

    def make_carte_case(self):
        # NOTE: cette carte est carre
        taille = self.taillecarte
        self.cartecase = []
        for i in range(taille):
            t1 = []
            for j in range(taille):
                id = get_prochain_id()
                t1.append(Caseregion(None, id, j, i))
            self.cartecase.append(t1)

    def trouver_case(self, x, y):

        if x < 0:
            x = 0
        if y < 0:
            y = 0

        if x > (self.aireX - 1):
            x = self.aireX - 1
        if y > (self.aireY - 1):
            y = self.aireY - 1

        cx = int(x / self.taillecase)
        cy = int(y / self.taillecase)
        if cx != 0 and x % self.taillecase > 0:
            cx += 1

        if cy != 0 and y % self.taillecase > 0:
            cy += 1

        # possible d'etre dans une case trop loin
        if cx == self.taillecarte:
            cx -= 1
        if cy == self.taillecarte:
            cy -= 1
        # print(self.cartecase[cy][cx])
        return self.cartecase[cy][cx]  # [cx,cy]

    def get_carte_bbox(self, x1, y1, x2, y2):  # case d'origine en cx et cy,  pour position pixels x, y
        # case d'origine en cx et cy,  pour position pixels x, y
        if x1 < 0:
            x1 = 1
        if y1 < 0:
            y1 = 1
        if x2 >= self.aireX:
            x2 = self.aireX - 1
        if y2 >= self.aireY:
            y2 = self.aireY - 1

        cx1 = int(x1 / self.taillecase)
        cy1 = int(y1 / self.taillecase)

        cx2 = int(x2 / self.taillecase)
        cy2 = int(y2 / self.taillecase)
        t1 = []
        for i in range(cy1, cy2):
            for j in range(cx1, cx2):
                case = self.cartecase[i][j]
                t1.append([j, i])
        return t1

    # CORRECTION REQUISE : PAS SUR QUE CETTE FONCITON SOIT ENCORE REQUISE
    # VA DEPENDRE DE L'IMPLANTATION S'IL Y A TROP D'OBJETS À VÉRIFIER
    def get_subcarte(self, x, y, d):

        cx = int(x / self.taillecase)
        cy = int(y / self.taillecase)
        # possible d'etre dans une case trop loin
        if cx == self.largeurcase:
            cx -= 1
        if cy == self.hauteurcase:
            cy -= 1

        # le centre en pixels de la case d'origine
        pxcentrex = (cx * self.taillecase) + self.demicase
        pxcentrey = (cy * self.taillecase) + self.demicase

        # la case superieur gauche de la case d'origine
        casecoinx1 = cx - d
        casecoiny1 = cy - d
        # assure qu'on deborde pas
        if casecoinx1 < 0:
            casecoinx1 = 0
        if casecoiny1 < 0:
            casecoiny1 = 0
        # la case inferieur droite
        casecoinx2 = cx + d
        casecoiny2 = cy + d
        # assure qu'on deborde pas
        if casecoinx2 >= self.largeurcase:
            casecoinx2 = self.largeurcase - 1
        if casecoiny2 >= self.hauteurcase:
            casecoiny2 = self.hauteurcase - 1

        distmax = (d * self.taillecase) + self.demicase

        t1 = []
        for i in range(casecoiny1, casecoiny2):
            for j in range(casecoinx1, casecoinx2):
                case = self.carte[i][j]
                pxcentrecasex = (j * self.taillecase) + self.demicase
                pxcentrecasey = (i * self.taillecase) + self.demicase
                distcase = Helper.calcDistance(pxcentrex, pxcentrey, pxcentrecasex, pxcentrecasey)
                if distcase <= distmax:
                    t1.append(case)
        return t1

    def maj_fog_pour_joueur(self, nom_joueur):
        """
        Met à jour la carte de fog pour la perspective du joueur 'nom_joueur'.
        - Les cases VISIBLE passent d'abord en KNOWN
        - On recalcule la visibilité à partir du champ de vision
          des unités & bâtiments du joueur.
        """

        fog_map = self.fog.map

        # 1) Dégrader toutes les cases VISIBLE -> KNOWN
        for y in range(self.taillecarte):
            for x in range(self.taillecarte):
                if fog_map[y][x] == FogState.VISIBLE:
                    fog_map[y][x] = FogState.KNOWN

        # 2) Marquer comme VISIBLE autour de chaque perso/bâtiment du joueur
        joueur = self.joueurs.get(nom_joueur)
        if not joueur:
            return

        # helper interne
        def marquer_vision_cercle(px, py, rayon):
            tc = self.taillecase
            cx = int(px / tc)
            cy = int(py / tc)
            r_cells = int(rayon / tc) + 2  # un peu de marge

            for dy in range(-r_cells, r_cells + 1):
                yy = cy + dy
                if yy < 0 or yy >= self.taillecarte:
                    continue
                for dx in range(-r_cells, r_cells + 1):
                    xx = cx + dx
                    if xx < 0 or xx >= self.taillecarte:
                        continue

                    # centre de la case en pixels
                    case_cx = (xx * tc) + tc // 2
                    case_cy = (yy * tc) + tc // 2

                    if Helper.calcDistance(px, py, case_cx, case_cy) <= rayon:
                        fog_map[yy][xx] = FogState.VISIBLE

        # 2.a) Unités
        for dico_persos in joueur.persos.values():
            for p in dico_persos.values():
                rayon = getattr(p, "champvision", 150)
                marquer_vision_cercle(p.x, p.y, rayon)

        # 2.b) Bâtiments (tu peux ajuster champ de vision)
        for dico_bats in joueur.batiments.values():
            for b in dico_bats.values():
                rayon = getattr(b, "champvision", 200)
                marquer_vision_cercle(b.x, b.y, rayon)

    def case_fog(self, xpx, ypx):
        """Retourne l’état fog d’une position en pixels."""
        tc = self.taillecase
        cx = int(xpx / tc)
        cy = int(ypx / tc)
        if 0 <= cx < self.taillecarte and 0 <= cy < self.taillecarte:
            return self.fog.map[cy][cx]
        return FogState.VISIBLE   # fallback


    def eliminer_ressource(self, type, ress):
        if ress.idregion:
            # self.regions[ress.montype][ress.idregion].listecases.pop(ress.id)
            cr = self.regions[ress.montype][ress.idregion].dicocases[ress.idcaseregion]
            if ress.id in cr.ressources.keys():
                cr.ressources.pop(ress.id)

        if ress.id in self.biotopes[type]:
            self.biotopes[type].pop(ress.id)
        if ress not in self.ressourcemorte:
            self.ressourcemorte.append(ress)


    #Transmet les actions du AI vers le contrôleur
    def action_AI_vers_controleur(self, action):
        self.parent.actions_requises.append(action)

    #############################################################################
    # ATTENTION : NE PAS TOUCHER
    def ajouter_actions_a_faire(self, iteration, actionsrecues):
        for i in actionsrecues:
            iteration_cle = i[0]
            if (iteration - 1) > int(iteration_cle):
                print("PEUX PASSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS")
            if i[1]:
                #action = json.loads(i[1])
                action = i[1]
            else:
                action = None
            if action:
                if iteration_cle not in self.actions_a_faire.keys():
                    self.actions_a_faire[iteration_cle] = [action]
                else:
                    for j in action:
                        self.actions_a_faire[iteration_cle].append(j)
    ##############################################################################


