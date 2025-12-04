import random
import math
import time
from helper import Helper
from AoEw_divers import *

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
    def __init__(self, parent, id, proie, force=None, distance=None):
        self.parent = parent
        self.id = id
        self.vitesse = 18
        self.distance_max = distance if distance is not None else getattr(parent, "portee_attaque", 150)
        self.distance_parcourue = 0
        self.taille = 20
        self.demitaille = 10
        self.force = force if force is not None else getattr(parent, "force", 10)
        self.proie = proie
        self.proiex = getattr(self.proie, "x", 0)
        self.proiey = getattr(self.proie, "y", 0)
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

    def retirer(self):
        try:
            self.parent.javelots.remove(self)
        except (ValueError, AttributeError):
            pass

    def bouger(self):
        if not self.proie or getattr(self.proie, "etat", "vivant") == "mort":
            self.retirer()
            return

        self.x, self.y = Helper.getAngledPoint(self.ang, self.vitesse, self.x, self.y)
        self.distance_parcourue += self.vitesse

        dist_cible = Helper.calcDistance(self.x, self.y, self.proie.x, self.proie.y)
        if dist_cible <= self.demitaille:
            if hasattr(self.proie, "recevoir_coup"):
                self.proie.recevoir_coup(self.force)
            elif hasattr(self.proie, "mourir"):
                self.proie.mourir()
            self.retirer()
            return

        if self.distance_parcourue >= self.distance_max:
            self.retirer()

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
        self.etat = "vivant"
        self.temps_mort = None
        self.temps_mort_delai = 5
        self.mana_max = 100
        self.mana = 100
        self.force = 5
        self.champvision = 100
        self.vitesse = 5
        self.angle = None
        self.javelots = []
        self.portee_attaque = 40
        self.delai_attaque = 25
        self.cooldown_attaque = 0
        self.utilise_projectile = False
        self.projectile_portee = 180
        self.image_mort = "mort"
        self.etats_et_actions = {"bouger": self.bouger,
                                 "ciblerennemi": self.cibler_ennemi,
                                 "attaquerennemi": self.attaquer_ennemi,
                                 "retourbatimentmere": None,
                                 "attaquerbatiment": self.attaquer_ennemi,
                                 "validerjavelot": self.valider_javelot,
                                 }
        self.vision = {
            "persos_amis": {},
            "persos_ennemis": {},
            "batiments_amis": {},
            "batiments_ennemis": {},
            "ressources": {}
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
        if not ennemi or getattr(ennemi, "etat", "vivant") == "mort":
            return
        self.cibler(ennemi)
        self.actioncourante = "ciblerennemi"

    def attaquer_ennemi(self):
        cible = self.cible
        if not cible or getattr(cible, "etat", "vivant") == "mort":
            self.cible = None
            self.actioncourante = None
            return
        dist = Helper.calcDistance(self.x, self.y, cible.x, cible.y)
        if dist > self.portee_attaque:
            self.actioncourante = "ciblerennemi"
            return
        if self.cooldown_attaque > 0:
            return
        self.cooldown_attaque = self.delai_attaque
        if self.utilise_projectile:
            self.lancer_javelot(cible)
        else:
            if hasattr(cible, "recevoir_coup"):
                cible.recevoir_coup(self.force)

    def attaquer_batiment(self, batiment):
        self.attaquer(batiment)

    def valider_javelot(self):
        if not self.cible or getattr(self.cible, "etat", "vivant") == "mort":
            self.actioncourante = None
            return
        if not self.javelots:
            self.lancer_javelot(self.cible)
        self.mettre_a_jour_projectiles()

    def lancer_javelot(self, ennemi):
        if self.javelots:
            return
        id = get_prochain_id()
        self.javelots.append(Javelot(self, id, ennemi, force=self.force, distance=self.projectile_portee))

    def mettre_a_jour_projectiles(self):
        for proj in list(self.javelots):
            proj.bouger()

    def recevoir_coup(self, force):
        if self.etat == "mort":
            return 1
        self.mana -= force
        if self.mana <= 0:
            self.mourir()
            return 1
        return 0

    def mourir(self):
        if self.etat == "mort":
            return
        self.etat = "mort"
        self.mana = 0
        self.temps_mort = time.time()
        self.actioncourante = None
        self.position_visee = None
        self.cible = None
        self.javelots.clear()
        self.image = self.image_mort

    def preparer_tour(self):
        if self.cooldown_attaque > 0:
            self.cooldown_attaque -= 1
        self.mettre_a_jour_projectiles()
        if self.etat == "mort":
            if self.temps_mort and (time.time() - self.temps_mort) >= self.temps_mort_delai:
                self.parent.annoncer_mort(self)
            return False
        return True

    def jouer_prochain_coup(self):
        if not self.preparer_tour():
            return
        if self.actioncourante:
            self.etats_et_actions[self.actioncourante]()

    def deplacer(self, pos):
        self.position_visee = pos
        self.actioncourante = "bouger"

    def bouger(self):
        if self.position_visee:
            # le if sert à savoir si on doit repositionner notre visee pour un objet
            # dynamique comme le daim
            x = self.position_visee[0]
            y = self.position_visee[1]
            ang = Helper.calcAngle(self.x, self.y, x, y)
            x1, y1 = Helper.getAngledPoint(ang, self.vitesse, self.x, self.y)
            ######## ICI METTRE TEST PROCHAIN PAS POUR VOIR SI ON PEUT AVANCER
            self.test_etat_du_sol(x1, y1)
            ######## FIN DE TEST POUR SURFACE MARCHEE
            # si tout ba bien on continue avec la nouvelle valeur
            self.x, self.y = x1, y1
            # ici on test pour vori si nous rendu a la cible (en deca de la longueur de notre pas)
            dist = Helper.calcDistance(self.x, self.y, x, y)
            if dist <= self.vitesse:
                if self.actioncourante == "bouger":
                    self.actioncourante = None
                return "rendu"
            else:
                return dist
            
    def cibler_ennemi(self): 

        if not self.cible or getattr(self.cible, "etat", "vivant") == "mort":
            self.cible = None
            self.actioncourante = None
            return

        try:
            self.position_visee = [self.cible.x, self.cible.y]
        except AttributeError:
            self.cible = None
            self.actioncourante = None
            return

        dist = Helper.calcDistance(self.x, self.y, self.position_visee[0], self.position_visee[1])

        if dist <= self.portee_attaque:
            self.actioncourante = "attaquerennemi"
            return

        reponse = self.bouger()

        if reponse == "rendu":
            self.actioncourante = "attaquerennemi"
        elif isinstance(reponse, (int, float)) and reponse <= self.portee_attaque:
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
        else:
            self.position_visee = None

    def test_etat_du_sol(self, x1, y1):
        ######## SINON TROUVER VOIE DE CONTOURNEMENT
        # ici oncalcule sur quelle case on circule
        casex = x1 / self.parent.parent.taillecase
        if casex != int(casex):
            casex = int(casex) + 1
        casey = y1 / self.parent.parent.taillecase
        if casey != int(casey):
            casey = int(casey) + 1
        #####AJOUTER TEST DE LIMITE
        case = self.parent.parent.trouver_case(x1, y1)
        #
        # test si different de 0 (0=plaine), voir Partie pour attribution des valeurs
        # if case.montype != "plaine":
        #     # test pour être sur que de n'est 9 (9=batiment)
        #     if case.montype != "batiment":
        #         print("marche dans ", case.montype)
        #     else:
        #         print("marche dans batiment")

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
        self.portee_attaque = 25
        self.delai_attaque = 15

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
        self.force = 30
        self.portee_attaque = 260
        self.projectile_portee = 320
        self.delai_attaque = 40
        self.utilise_projectile = True
        self.javelots = []

    def cibler(self, cible):
        if hasattr(cible, "x"):
            self.cible = cible
            self.position_visee = [cible.x, cible.y]
        else:
            self.position_visee = cible

        self.angle = Helper.calcAngle(self.x, self.y, self.position_visee[0], self.position_visee[1])
        self.dir = "D" if self.x < self.position_visee[0] else "G"
        if self.y < self.position_visee[1]:
            self.dir = self.dir + "B"
        else:
            self.dir = self.dir + "H"

        self.image = self.image[:-2] + self.dir

    def attaquer(self, ennemi):
        super().attaquer(ennemi)

class Ouvrier(Perso):
    def __init__(self, parent, id, maison, couleur, x, y, montype):
        Perso.__init__(self, parent, id, maison, couleur, x, y, montype)
        self.force = 8
        self.portee_attaque = 160
        self.projectile_portee = 200
        self.delai_attaque = 30
        self.utilise_projectile = True
        self.activite = None  # sedeplacer, cueillir, chasser, pecher, construire, reparer, attaquer, fuir, promener,explorer,chercher
        self.typeressource = None
        self.quota = 20
        self.ramassage = 0
        self.cibletemp = None
        self.dejavisite = []
        self.champvision = random.randrange(100) + 300
        self.champchasse = 120
        self.javelots = []
        self.vitesse = random.randrange(5) + 20
        self.etats_et_actions = {"bouger": self.bouger,
                                 "ciblersiteconstruction": self.cibler_site_construction,
                                 "ciblerproie": self.cibler_proie,
                                 "ciblerennemi": self.cibler_ennemi,
                                 "attaquerennemi": self.attaquer_ennemi,
                                 "attaquerbatiment": self.attaquer_ennemi, 
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
        self.actioncourante = actiontype

    def retour_batiment_mere(self):
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
        reponse = self.bouger()
        if reponse == "rendu":
            self.actioncourante = "ramasserressource"

    def cibler_site_construction(self):
        reponse = self.bouger()
        if reponse == "rendu":
            self.actioncourante = "construirebatiment"

    def cibler_proie(self):
        self.position_visee = [self.cible.x, self.cible.y]
        reponse = self.bouger()
        if reponse == "rendu":
            if self.typeressource == "daim" or self.typeressource == "eau":
                self.actioncourante = "ramasserressource"
        elif isinstance(reponse, (int, float)) and reponse <= self.champchasse and self.cible.etat == "vivant":
            self.actioncourante = "validerjavelot"

    def valider_javelot(self):
        if not self.cible or getattr(self.cible, "etat", "vivant") == "mort":
            if getattr(self.cible, "montype", None) in ("daim", "eau"):
                self.actioncourante = "ramasserressource"
            else:
                self.actioncourante = None
            return
        if not self.javelots:
            self.lancer_javelot(self.cible)
        self.mettre_a_jour_projectiles()

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
        if not self.preparer_tour():
            return

        if self.actioncourante:
            # V?rifier la coh?rence des constructions
            if self.actioncourante in ["construirebatiment", "ciblersiteconstruction"]:
                if self.cible is None:
                    print(f"{self.id}: Aucune cible de construction - retour au repos")
                    self.actioncourante = None
                    return

                if hasattr(self.cible, 'id') and self.cible.id not in self.parent.batiments.get('siteconstruction', {}):
                    print(f"{self.id}: Site de construction {self.cible.id} introuvable - abandon")
                    self.cible = None
                    self.actioncourante = None
                    return
            self.etats_et_actions[self.actioncourante]()

    def lancer_javelot(self, proie):
        if self.javelots:
            return
        id = get_prochain_id()
        self.javelots.append(Javelot(self, id, proie, force=self.force, distance=self.projectile_portee))

    def chercher_nouvelle_ressource(self, typ, idreg):

        # Types à régions (arbre/roche/eau/marais/aureus) → même région
        if typ in self.parent.parent.regions:
            reg = self.parent.parent.regions[typ]
            if idreg in reg:
                regspec = reg[idreg]
                n = len(regspec.dicocases)
                while n > 0:
                    clecase = list(regspec.dicocases.keys())
                    case = regspec.dicocases[random.choice(clecase)]
                    n -= 1
                    if case.ressources:
                        clecase2 = list(case.ressources.keys())
                        newress = case.ressources[random.choice(clecase2)]
                        if newress.montype == typ:
                            return newress
            return None
        else:
            # Pas de régions (ex.: daim, baie) → choisir dans les biotopes de ce type
            candidats = self.parent.parent.biotopes.get(typ, {})
            if not candidats:
                return None
            meilleur = None
            best = 10**9
            for obj in candidats.values():
                if obj is self.cible:
                    continue
                dist = Helper.calcDistance(self.x, self.y, obj.x, obj.y)
                if dist < best and dist <= self.champvision:
                    meilleur, best = obj, dist
            return meilleur
        
        # print("Je cherche nouvelle ressource")
        # #if typ != "baie" and typ != "daim":
        # reg = self.parent.parent.regions[typ]
        # if idreg in reg:
        #     regspec = self.parent.parent.regions[typ][idreg]
        #     n = len(regspec.dicocases)
        #     while n > 0:
        #         clecase = list(regspec.dicocases.keys())
        #         case = regspec.dicocases[random.choice(clecase)]
        #         n -= 1
        #         if case.ressources:
        #             clecase2 = list(case.ressources.keys())
        #             newress = case.ressources[random.choice(clecase2)]
        #             if newress.montype == typ:
        #                 return newress
        #     return None
        # else:
        #    nb = len(self.parent.parent.biotopes[typ])
        #    for i in range(nb):
        #        rep = random.choice(list(self.parent.parent.biotopes[typ].keys()))
        #        obj = self.parent.parent.biotopes[typ][rep]
        #        if obj != self.cible:
        #            distance = Helper.calcDistance(self.x, self.y, obj.x, obj.y)
        #            if distance <= self.champvision:
        #                return obj
        #    return None

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
            if self.actioncourante == "ciblerressource" or self.actioncourante == "retourbatimentmere" or self.actioncourante == "ramasserresource":
                self.actioncourante = "retourbatimentmere"
            else:
                self.actioncourante = "retourbatimentmere"
                self.position_visee = [self.batimentmere.x, self.batimentmere.y]

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

