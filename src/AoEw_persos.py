import random
import math
from helper import Helper
from AoEw_divers import *
from vue.fog import FogState

class Fleche():
    def __init__(self, parent, id, proie):
        self.parent = parent
        self.id = id
        self.vitesse = 18
        self.taille = 20
        self.force = 10
        self.proie = proie
        self.proiex = self.proie.x
        self.proiey = self.proie.y
        self.x = self.parent.x
        self.y = self.parent.y
        self.ang = Helper.calcAngle(self.x, self.y, self.proiex, self.proiey)
        angquad = math.degrees(self.ang)
        dir = "DB"
        if 0 <= angquad <= 89:
            dir = "DB"
        elif -90 <= angquad <= -1:
            dir = "DH"
        if 90 <= angquad <= 179:
            dir = "GB"
        elif -180 <= angquad <= -91:
            dir = "GH"
        self.image = "javelot" + dir

    def bouger(self):
        self.x, self.y, = Helper.getAngledPoint(self.ang, self.vitesse, self.x, self.y)
        dist = Helper.calcDistance(self.x, self.y, self.proie.x, self.proie.y)
        if dist <= self.taille:
            rep = self.cibleennemi.recevoircoup(self.force)
            return self

class Javelot():
    def __init__(self, parent, id, proie):
        self.parent = parent
        self.id = id
        self.vitesse = 18
        self.distance = 150
        self.taille = 20
        self.demitaille = 10
        self.proie = proie
        self.proiex = self.proie.x
        self.proiey = self.proie.y
        self.x = self.parent.x
        self.y = self.parent.y
        self.ang = Helper.calcAngle(self.x, self.y, self.proiex, self.proiey)
        angquad = math.degrees(self.ang)
        dir = "DB"
        if 0 <= angquad <= 89:
            dir = "DB"
        elif -90 <= angquad <= -1:
            dir = "DH"
        if 90 <= angquad <= 179:
            dir = "GB"
        elif -180 <= angquad <= -91:
            dir = "GH"
        self.image = "javelot" + dir

    def bouger(self):
        self.x, self.y, = Helper.getAngledPoint(self.ang, self.vitesse, self.x, self.y)
        dist = Helper.calcDistance(self.x, self.y, self.proie.x, self.proie.y)
        if dist <= self.demitaille:
            # tue daim
            self.parent.actioncourante = "ciblerressource"
            self.parent.javelots.remove(self)
            self.proie.mourir()
        else:
            dist = Helper.calcDistance(self.x, self.y, self.proiex, self.proiey)
            if dist < self.vitesse:
                self.parent.javelots.remove(self)
                self.parent.actioncourante = "ciblerproie"

class Perso():
    def __init__(self, parent, id, batiment, couleur, x, y, montype):
        self.parent = parent
        self.id = id
        self.actioncourante = None
        self.batimentmere = batiment
        self.dir = "D"
        self.image = couleur[0] + "_" + montype + self.dir
        self.x = x
        self.y = y
        self.montype = montype
        self.cible = None
        self.position_visee = None
        self.cibleennemi = None
        self.ciblebatiment = None
        self.mana_max = 100
        self.mana = 100
        self.force = 5
        self.champvision = 100
        self.vitesse = 5
        self.angle = None
        self.javelots = []
        self.chemin_planifie = []
        self.chemin_restant = []
        self.destination_finale = None
        self.replans_restants = 0
        self.stuck_frames = 0
        self.derniere_pos = (self.x, self.y)
        self.etats_et_actions = {"bouger": self.bouger,
                                 "ciblerennemi": self.cibler_ennemi,
                                 "attaquerennemi": self.attaquer_ennemi,
                                 "retourbatimentmere": None, #à vérifier car fct ds ouvrier
                                 "attaquerbatiment": self.attaquer_batiment, 
                                 "validerjavelot": self.valider_javelot,
                                 }
        self.vision = {
            "persos_amis": {},
            "persos_ennemis": {},
            "batiments_amis": {},
            "batiments_ennemis": {},
            "ressources": {}  # par type: {"daim": {...}, "arbre": {...}, ...} 
            }
    

    ################ Zone AI ####################################
    def mettre_a_jour_vision(self):
        persos, bats, ressources = self.parent.parent.objets_dans_rayon(self.x, self.y, self.champvision)

        # reset
        self.vision = {
            "persos_amis": {},
            "persos_ennemis": {},
            "batiments_amis": {},
            "batiments_ennemis": {},
            "ressources": {}
        }

        mon_joueur = self.parent  # le Joueur propriétaire de ce perso

        # Persos
        for p in persos:
            cle = getattr(p, "id", id(p))
            if p.parent is mon_joueur:
                self.vision["persos_amis"][cle] = p
            else:
                self.vision["persos_ennemis"][cle] = p

        # Bâtiments
        for b in bats:
            cle = getattr(b, "id", id(b))
            if b.parent is mon_joueur:
                self.vision["batiments_amis"][cle] = b
            else:
                self.vision["batiments_ennemis"][cle] = b

        # Ressources (groupées par type)
        for r in ressources:
            typ = getattr(r, "montype", "inconnu")
            self.vision["ressources"].setdefault(typ, {})
            cle = getattr(r, "id", id(r))
            self.vision["ressources"][typ][cle] = r

    ##################################################################################################

    def attaquer(self, ennemi):

        if not ennemi:
            return 
        # self.cibleennemi = ennemi
        # x = self.cibleennemi.x
        # y = self.cibleennemi.y
        self.cibler(ennemi)

        # dist = Helper.calcDistance(self.x, self.y, x, y)
        # if dist <= self.vitesse:
        #     self.actioncourante = "attaquerennemi"
        # else:
        self.actioncourante = "ciblerennemi"

    def attaquer_ennemi(self):

        if not self.cible:
            self.actioncourante = None
            return 
        
        if not hasattr(self.cible, "recevoir_coup"): #si on ne peut pas attaquer, cancelled
            self.cible = None
            self.actioncourante = None 

        rep = self.cibleennemi.recevoir_coup(self.force)
        if rep == 1:
            self.cibleennemi = None
            self.cible = None
        else:
            self.actioncourante = "validerjavelot"
        #   gestion delai compteur attaque? 
    
    def attaquer_batiment(self, batiment):
        self.ciblebatiment = batiment 
        x = self.ciblebatiment.x
        y = self.ciblebatiment.y 
        self.cibler(batiment)

        dist = Helper.calcDistance(self.x, self.y, x, y)
        if dist <= self.vitesse:
            self.actioncourante = "attaquerbatiment"
        else:
            self.actioncourante = "ciblerennemi"
    
    def valider_javelot(self):
        self.lancer_javelot(self.cible)
        for i in self.javelots:
            i.bouger()
    
    def lancer_javelot(self, ennemi):
        if self.javelots == []:
            id = get_prochain_id()
            self.javelots.append(Javelot(self, id, ennemi))

    def recevoir_coup(self, force):
        self.mana -= force
        print("Ouch")
        if self.mana < 1:
            print("MORTS")
            self.parent.annoncer_mort(self)
            return 1

    def jouer_prochain_coup(self):
        if self.actioncourante:
            reponse = self.etats_et_actions[self.actioncourante]()

    def planifier_chemin(self, pos, preserve_action=False):
        """Utilise A* pour créer un chemin, sans ou avec changement d'état."""
        pathfinder = self.parent.parent.pathfinder
        cible = tuple(pos)
        # si on a déjà un chemin vers cette cible, ne pas recalculer inutilement
        if self.destination_finale == cible and self.chemin_restant:
            return True
        chemin = pathfinder.trouver_chemin((self.x, self.y), pos)
        if not chemin or len(chemin) == 1:
            # aucun chemin utilisable -> on ne part pas en ligne droite au travers des obstacles
            self.chemin_planifie = []
            self.chemin_restant = []
            self.position_visee = None
            if not preserve_action:
                self.actioncourante = None
            return False
        # évite un "snap" : ignore le premier point trop proche de la position courante
        remaining = chemin
        if chemin and Helper.calcDistance(self.x, self.y, chemin[0][0], chemin[0][1]) < self.vitesse * 0.5:
            remaining = chemin[1:]
        self.chemin_planifie = [(self.x, self.y)] + remaining
        self.chemin_restant = remaining
        self.position_visee = self.chemin_restant[0] if self.chemin_restant else pos
        self.destination_finale = cible
        self.replans_restants = 3
        self.stuck_frames = 0
        self.derniere_pos = (self.x, self.y)
        if not preserve_action:
            self.actioncourante = "bouger"
        return True

    def deplacer(self, pos):
        self.planifier_chemin(pos, preserve_action=False)

    def replan_path(self):
        """Recalcule un chemin vers la destination finale si possible."""
        if not self.destination_finale or self.replans_restants <= 0:
            return False
        self.replans_restants -= 1
        pathfinder = self.parent.parent.pathfinder
        nouveau = pathfinder.trouver_chemin((self.x, self.y), self.destination_finale)
        if not nouveau or len(nouveau) < 2:
            return False
        remaining = nouveau
        if Helper.calcDistance(self.x, self.y, nouveau[0][0], nouveau[0][1]) < self.vitesse * 0.5:
            remaining = nouveau[1:]
        self.chemin_planifie = [(self.x, self.y)] + remaining
        self.chemin_restant = remaining
        self.position_visee = self.chemin_restant[0] if self.chemin_restant else self.destination_finale
        return True

    def bouger(self):
        if self.position_visee:
            # le if sert à savoir si on doit repositionner notre visee pour un objet
            # dynamique comme le daim
            cible = self.chemin_restant[0] if self.chemin_restant else self.position_visee
            x = cible[0]
            y = cible[1]
            ang = Helper.calcAngle(self.x, self.y, x, y)
            vit_pas = self.get_vitesse_locale(x, y)
            x1, y1 = Helper.getAngledPoint(ang, vit_pas, self.x, self.y)
            ######## ICI METTRE TEST PROCHAIN PAS POUR VOIR SI ON PEUT AVANCER
            if not self.test_etat_du_sol(x1, y1):
                # on bloque le mouvement si le prochain pas est sur un obstacle
                if not self.replan_path():
                    self.position_visee = None
                    self.chemin_restant = []
                    self.actioncourante = None
                    self.destination_finale = None
                    return
                # après replanification, reprendre sur le nouveau chemin
                return self.bouger()
            ######## FIN DE TEST POUR SURFACE MARCHEE
            # si tout ba bien on continue avec la nouvelle valeur
            self.x, self.y = x1, y1
            # détection de blocage : si on ne progresse pas assez, on replannifie
            dist_step = Helper.calcDistance(self.x, self.y, *self.derniere_pos)
            if dist_step < 0.1:
                self.stuck_frames += 1
            else:
                self.stuck_frames = 0
                self.derniere_pos = (self.x, self.y)
            if self.stuck_frames >= 3:
                if not self.replan_path():
                    self.position_visee = None
                    self.chemin_restant = []
                    self.actioncourante = None
                    self.destination_finale = None
                    return
                return self.bouger()
            # ici on test pour vori si nous rendu a la cible (en deca de la longueur de notre pas)
            dist = Helper.calcDistance(self.x, self.y, x, y)
            if dist <= vit_pas:
                if self.chemin_restant:
                    # on enlève l'étape atteinte et vise la prochaine
                    self.chemin_restant.pop(0)
                    if self.chemin_restant:
                        self.position_visee = self.chemin_restant[0]
                        return dist

                if self.actioncourante == "bouger":
                    self.actioncourante = None
                self.position_visee = None
                self.chemin_restant = []
                self.destination_finale = None
                return "rendu"
            else:
                # si on est coincé mais qu'il reste du chemin/destination, tenter un replanning
                if self.destination_finale and self.replan_path():
                    return self.bouger()
                return dist
            
    def cibler_ennemi(self): 

        if not self.cible: # si pas de cible, ne rien faire
            self.actioncourante = None
            return

        if getattr(self.cible, "etat", None) == "mort": #si l'objet est mort, ne rien faire 
            self.cible = None
            self.actioncourante = None
            return 
        
        try:  
            self.position_visee = [self.cible.x, self.cible.y]
        except AttributeError: #si erreur, ne fait rien 
            self.cible = None
            self.actioncourante = None
            return 

        reponse = self.bouger()

        if reponse == "rendu":
            if any(obj is self.cible for obj in self.vision.get("persos_ennemis", {}).values()):
                self.actioncourante = "attaquerennemi"
            elif any(obj is self.cible for obj in self.vision.get("batiments_ennemis", {}).values()):
                self.actioncourante = "attaquerbatiment"
            else:
                self.actioncourante = None 

        else:
            if isinstance(reponse, (int, float)):
                dist = reponse
            if dist <= self.vitesse:
                if getattr(self.cible, "montype", None) == "daim":
                    self.actioncourante = "validerjavelot"
                else:
                    self.actioncourante = "attaquerennemi"


    def cibler(self, obj):
        self.cible = obj
        if obj:
            self.position_visee = [self.cible.x, self.cible.y]
            if self.x < self.position_visee[0]:
                self.dir = "D"
            else:
                self.dir = "G"
            self.image = self.image[:-1] + self.dir
            # planifie un chemin sans casser l'action courante (attaque/construction)
            self.planifier_chemin(self.position_visee, preserve_action=True)
        else:
            self.position_visee = None

    def test_etat_du_sol(self, x1, y1):
        ######## SINON TROUVER VOIE DE CONTOURNEMENT
        pf = self.parent.parent.pathfinder
        cx, cy = pf.pixel_to_case(x1, y1)
        return pf.est_traversable(cx, cy)

    def get_vitesse_locale(self, cible_x, cible_y):
        """Renvoie la vitesse ajustée selon le terrain de la case visée."""
        pf = self.parent.parent.pathfinder
        cx, cy = pf.pixel_to_case(cible_x, cible_y)
        case = self.parent.parent.cartecase[cy][cx]
        if getattr(case, "montype", None) in getattr(pf, "RALENTIS", ()):
            return self.vitesse * 0.5
        return self.vitesse

    

    def test_etat_du_sol1(self, x1, y1):
        ######## SINON TROUVER VOIE DE CONTOURNEMENT
        # ici oncalcule sur quelle case on circule
        casex = x1 / self.parent.parent.taillecase
        if casex != int(casex):
            casex = int(casex) + 1
        casey = y1 / self.parent.parent.taillecase
        if casey != int(casey):
            casey = int(casey) + 1
        #####AJOUTER TEST DE LIMITE
        # test si different de 0 (0=plaine), voir Partie pour attribution des valeurs
        if self.parent.parent.cartecase[int(casey)][int(casex)].montype != "plaine":
            # test pour être sur que de n'est 9 (9=batiment)
            if self.parent.parent.cartecase[int(casey)][int(casex)].montype != "batiment":
                print("marche dans ", )
            else:
                print("marche dans batiment")

class Soldat(Perso):
    def __init__(self, parent, id, maison, couleur, x, y, montype):
        Perso.__init__(self, parent, id, maison, couleur, x, y, montype)
        self.force = 20

class Archer(Perso):
    def __init__(self, parent, id, maison, couleur, x, y, montype):
        Perso.__init__(self, parent, id, maison, couleur, x, y, montype)

class Chevalier(Perso):
    def __init__(self, parent, id, maison, couleur, x, y, montype):
        Perso.__init__(self, parent, id, maison, couleur, x, y, montype)

class Druide(Perso):
    def __init__(self, parent, id, maison, couleur, x, y, montype):
        Perso.__init__(self, parent, id, maison, couleur, x, y, montype)

class Ingenieur(Perso):
    def __init__(self, parent, id, maison, couleur, x, y, montype):
        Perso.__init__(self, parent, id, maison, couleur, x, y, montype)

class Ballista(Perso):
    def __init__(self, parent, id, maison, couleur, x, y, montype):
        Perso.__init__(self, parent, id, maison, couleur, x, y, montype)

        self.dir = "DH"
        self.image = couleur[0] + "_" + montype + self.dir
        self.cible = None
        self.angle = None
        self.distancefeumax = 30
        self.distancefeu = 30
        self.fleches = []
        self.cibleennemi = None
        # self.nomimg="ballista"

    def cibler(self, pos):
        self.position_visee = pos

        self.angle = Helper.calcAngle(self.x, self.y, self.position_visee[0], self.position_visee[1])
        if self.x < self.position_visee[0]:
            self.dir = "D"
        else:
            self.dir = "G"
        if self.y < self.position_visee[1]:
            self.dir = self.dir + "B"
        else:
            self.dir = self.dir + "H"

        self.image = self.image[:-2] + self.dir

    def attaquer(self, ennemi):
        self.cibleennemi = ennemi
        x = self.cibleennemi.x
        y = self.cibleennemi.y
        self.position_visee = [x, y]
        dist = Helper.calcDistance(self.x, self.y, x, y)
        if dist <= self.distancefeu:
            self.actioncourante = "attaquerennemi"
        else:
            self.actioncourante = "ciblerennemi"

    def attaquerennemi(self):
        if self.delaifeu == 0:
            id = get_prochain_id()
            fleche = Fleche(self, id, self.ciblennemi)
            self.delaifeu = self.delaifeumax
        for i in self.fleches:
            rep = i.bouger()
        if rep:
            rep = self.cibleennemi.recevoir_coup(self.force)
            self.fleches.remove(rep)

class Ouvrier(Perso):
    def __init__(self, parent, id, maison, couleur, x, y, montype):
        Perso.__init__(self, parent, id, maison, couleur, x, y, montype)
        self.activite = None  # sedeplacer, cueillir, chasser, pecher, construire, reparer, attaquer, fuir, promener,explorer,chercher
        self.typeressource = None
        self.quota = 20
        self.ramassage = 0
        self.cibletemp = None
        self.dejavisite = []
        self.champvision = random.randrange(100) + 300
        self.champchasse = 120
        self.javelots = []
        self.vitesse = random.randrange(5) + 5
        self.etats_et_actions = {"bouger": self.bouger,
                                 "ciblersiteconstruction": self.cibler_site_construction,
                                 "ciblerproie": self.cibler_proie,
                                 "ciblerennemi": self.cibler_ennemi,
                                 "attaquerennemi": self.attaquer_ennemi,
                                 "attaquerbatiment": self.attaquer_batiment, 
                                 "construirebatiment": self.construire_batiment,
                                 "ramasserressource": self.ramasser,
                                 "ciblerressource": self.cibler_ressource,
                                 "retourbatimentmere": self.retour_batiment_mere,
                                 "validerjavelot": self.valider_javelot,
                                 }
    
    def chasser_ramasser(self, objetcible, sontype, actiontype):
        self.cible = objetcible
        self.typeressource = sontype
        self.position_visee = [self.cible.x, self.cible.y]
        # planifie un chemin vers la ressource (redirigé par le pathfinder si bloquante)
        self.planifier_chemin(self.position_visee, preserve_action=True)
        self.actioncourante = actiontype

    def retour_batiment_mere(self):
        # cible la maison la plus proche
        maisons = self.parent.batiments.get("maison", {})
        if maisons:
            best = None
            best_dist = float("inf")
            for m in maisons.values():
                d = Helper.calcDistance(self.x, self.y, m.x, m.y)
                if d < best_dist:
                    best_dist = d
                    best = m
            cible_tuple = (best.x, best.y) if best else None
            if best and (not self.chemin_restant or self.destination_finale != cible_tuple):
                self.planifier_chemin(cible_tuple, preserve_action=True)
        reponse = self.bouger()
        if reponse == "rendu":
            if self.cible:
                if self.typeressource == "baie" or self.typeressource == "daim" or self.typeressource == "eau":
                    self.parent.ressources["nourriture"] += self.ramassage
                else:
                    self.parent.ressources[self.typeressource] += self.ramassage
                self.ramassage = 0
                if self.cible.valeur < 1:
                    rep = self.chercher_nouvelle_ressource(self.cible.montype, self.cible.idregion)
                    self.cibler(rep)
                if self.cible:
                    self.cibler(self.cible)
                    if self.cible.montype == "daim":
                        self.actioncourante = "ciblerproie"
                    else:
                        self.actioncourante = "ciblerressource"
                else:
                    self.actioncourante = None
        else:
            pass

    def cibler_ressource(self):
        if self.cible and not self.chemin_restant:
            self.planifier_chemin((self.cible.x, self.cible.y), preserve_action=True)
        reponse = self.bouger()
        if reponse == "rendu":
            self.actioncourante = "ramasserressource"

    def cibler_site_construction(self):
        if self.cible and not self.chemin_restant:
            self.planifier_chemin((self.cible.x, self.cible.y), preserve_action=True)
        reponse = self.bouger()
        if reponse == "rendu":
            self.actioncourante = "construirebatiment"

    def cibler_proie(self):
        self.position_visee = [self.cible.x, self.cible.y]
        if self.cible and not self.chemin_restant:
            self.planifier_chemin(self.position_visee, preserve_action=True)
        reponse = self.bouger()
        if reponse == "rendu":
            if self.typeressource == "daim" or self.typeressource == "eau":
                self.actioncourante = "ramasserressource"
        elif isinstance(reponse, (int, float)) and reponse <= self.champchasse and getattr(self.cible, "etat", None) == "vivant":
            self.actioncourante = "validerjavelot"

    def valider_javelot(self):
        self.lancer_javelot(self.cible)
        for i in self.javelots:
            i.bouger()

    def ramasser(self):
        self.ramassage += 1
        self.cible.valeur -= 1
        if self.cible.valeur == 0 or self.ramassage == self.quota:
            self.actioncourante = "retourbatimentmere"
            self.position_visee = [self.batimentmere.x, self.batimentmere.y]
            if self.cible.valeur == 0:
                self.parent.avertir_ressource_mort(self.typeressource, self.cible)
                # rep = self.chercher_nouvelle_ressource(self.cible.montype, self.cible.idregion)
                # if rep:
                #     if self.id != rep.id:
                #         self.cible=rep
        else:
            self.x = self.x + random.randrange(4) - 2
            self.y = self.y + random.randrange(4) - 2

    def construire_batiment(self):

        # if batiment.id not in self.parent.batiments['siteconstruction']:
        #     self.actioncourante = ""
        #     self.cible = None
        #     return 0
        
        self.cible.decremente_delai()
        if self.cible.delai < 1:
            batiment = self.parent.parent.classesbatiments[self.cible.sorte](self, self.cible.id, self.parent.couleur,
                                                                             self.cible.x, self.cible.y,
                                                                             self.cible.sorte)
            self.parent.batiments[self.cible.sorte][self.cible.id] = batiment

        #Avant de manipuler l’entrée, sécuriser son existence
            sitecons = self.parent.batiments['siteconstruction'].get(batiment.id)

            if sitecons is None:
                # Le site a déjà été converti en vrai bâtiment par un autre ouvrier
                # -> on nettoie l’état et on quitte proprement
                self.actioncourante = ""
                self.cible = None
                return 0  # ou "termine" selon ta convention

            #... progression / validation ...
            #Au moment de retirer le site (premier ouvrier à terminer)
            sitecons = self.parent.batiments['siteconstruction'].pop(batiment.id, None)
            if sitecons is None:
                # Déjà retiré entre-temps par un autre ouvrier (course)
                self.actioncourante = ""
                self.cible = None
                return 0
            
            print(sitecons)

            self.parent.installer_batiment(batiment)

            if self.cible.sorte == "maison":
                self.batimentmere = batiment
            
            self.cible = None
            self.actioncourante = None

                #ici: créer/installer le vrai bâtiment, puis:
            self.actioncourante = ""
            self.cible = None
            return 1

    

     

    def construire_site_construction(self, site_construction):
        self.cibler(site_construction)
        self.actioncourante = "ciblersiteconstruction"
        # pass #monte le batiment par etapes on pourrait montrer l'anavancement de la construciton

    def jouer_prochain_coup(self):
        if self.actioncourante:
            # VÉRIFIER LA COHÉRENCE DES CONSTRUCTIONS
            if self.actioncourante in ["construirebatiment", "ciblersiteconstruction"]:
                if self.cible is None:
                    print(f"{self.id}: Aucune cible de construction - retour au repos")
                    self.actioncourante = None
                    return

                # Vérifier que le site existe toujours
                if hasattr(self.cible, 'id') and self.cible.id not in self.parent.batiments.get('siteconstruction', {}):
                    print(f"{self.id}: Site de construction {self.cible.id} introuvable - abandon")
                    self.cible = None
                    self.actioncourante = None
                    return
            reponse = self.etats_et_actions[self.actioncourante]()

    def lancer_javelot(self, proie):
        if self.javelots == []:
            id = get_prochain_id()
            self.javelots.append(Javelot(self, id, proie))

    def chercher_nouvelle_ressource(self, typ, idreg):
        """Ressource la plus proche de la ressource initiale, dans un rayon de 20 cases."""
        candidates = []
        if typ in self.parent.parent.regions and idreg in self.parent.parent.regions[typ]:
            regspec = self.parent.parent.regions[typ][idreg]
            for case in regspec.dicocases.values():
                candidates.extend(case.ressources.values())
        else:
            candidates = list(self.parent.parent.biotopes.get(typ, {}).values())

        # point de référence : l'ancienne cible si dispo, sinon la position de l'ouvrier
        ref_x, ref_y = (self.cible.x, self.cible.y) if self.cible else (self.x, self.y)
        rayon_px = 20 * self.parent.parent.taillecase

        best = None
        best_dist = float("inf")
        for obj in candidates:
            if obj is self.cible:
                continue
            dist = Helper.calcDistance(ref_x, ref_y, obj.x, obj.y)
            if dist > rayon_px:
                continue
            if dist < best_dist:
                best_dist = dist
                best = obj
        return best
    # def deplacer(self,pos):
    #     self.position_visee = pos
    #     self.actioncourante = "bouger"
    #
    # def bouger(self):
    #     if self.position_visee:
    #         # le if sert à savoir si on doit repositionner notre visee pour un objet
    #         # dynamique comme le daim
    #         x = self.position_visee[0]
    #         y = self.position_visee[1]
    #         ang = Helper.calcAngle(self.x, self.y, x, y)
    #         x1, y1 = Helper.getAngledPoint(ang, self.vitesse, self.x, self.y)
    #         ######## ICI METTRE TEST PROCHAIN PAS POUR VOIR SI ON PEUT AVANCER
    #         self.test_etat_du_sol(x1, y1)
    #         ######## FIN DE TEST POUR SURFACE MARCHEE
    #         # si tout ba bien on continue avec la nouvelle valeur
    #         self.x, self.y = x1, y1
    #         # ici on test pour vori si nous rendu a la cible (en deca de la longueur de notre pas)
    #         dist = Helper.calcDistance(self.x, self.y, x, y)
    #         if dist <= self.vitesse:
    #             if self.actioncourante=="bouger":
    #                 self.actioncourante=None
    #             return "rendu"
    #         else:
    #             return dist

    # def test_etat_du_sol(self,x1, y1):
    #     ######## SINON TROUVER VOIE DE CONTOURNEMENT
    #     # ici oncalcule sur quelle case on circule
    #     casex = x1 / self.parent.parent.taillecase
    #     if casex != int(casex):
    #         casex = int(casex) + 1
    #     casey = y1 / self.parent.parent.taillecase
    #     if casey != int(casey):
    #         casey = int(casey) + 1
    #     #####AJOUTER TEST DE LIMITE
    #     # test si different de 0 (0=plaine), voir Partie pour attribution des valeurs
    #     if self.parent.parent.cartecase[int(casey)][int(casex)].montype != "plaine":
    #         # test pour être sur que de n'est 9 (9=batiment)
    #         if self.parent.parent.cartecase[int(casey)][int(casex)].montype != "batiment":
    #             print("marche dans ", )
    #         else:
    #             print("marche dans batiment")

    def abandonner_ressource(self, ressource):
        if ressource == self.cible:
            # si on transporte déjà quelque chose, on retourne déposer
            if self.ramassage > 0:
                self.actioncourante = "retourbatimentmere"
                self.position_visee = [self.batimentmere.x, self.batimentmere.y]
                self.destination_finale = tuple(self.position_visee)
            else:
                # sinon on tente une nouvelle ressource proche, sans passer par la maison
                rep = self.chercher_nouvelle_ressource(ressource.montype, getattr(ressource, "idregion", None))
                if rep:
                    self.cible = rep
                    self.position_visee = [self.cible.x, self.cible.y]
                    if getattr(self.cible, "montype", "") == "daim":
                        self.actioncourante = "ciblerproie"
                    else:
                        self.actioncourante = "ciblerressource"
                    self.planifier_chemin(self.position_visee, preserve_action=True)
                else:
                    self.cible = None
                    self.actioncourante = None

    ## PAS UTILISER POUR LE MOMENT
    def scanner_alentour(self):
        dicojoueurs = self.parent.parent.joueurs
        for i in dicojoueurs.values():
            for j in i.ouvriers.values():
                if j != self:
                    if Helper.calcDistance(self.x, self.y, j.x, j.y) <= self.champvision:
                        pass
        return 0

    # def trouver_cible(self, joueurs):
    #     c = None
    #     while c == None:
    #         listeclesj = list(joueurs.keys())
    #         c = random.choice(listeclesj)
    #         if joueurs[c].nom != self.parent.nom:
    #             listeclesm = list(joueurs[c].maisons.keys())
    #             maisoncible = random.choice(listeclesm)
    #             self.cible = joueurs[c].maisons[maisoncible]
    #         else:
    #             c = None
    #     self.angle = Helper.calcAngle(self.x, self.y, self.cible.x, self.cible.y)

