from AoEw_joueurs import *

# CORRECTION REQUISE : cette classe doit etre comlpetemnent revue 
# La classe IA herite des attributs et methodes mais redefinit les methodes... 
class IA(Joueur):

    def __init__(self, parent, id, nom, couleur, x, y, info_ia):
        super().__init__(parent, id, nom, couleur, x, y)

        self.cibles_unites = {"ouvrier": 1, "soldat": 1, "archer": 1}
        
        self.diff = info_ia["difficulte"]
        self.type = info_ia["type"]


        if self.diff == "Facile":
            self.delai_action = 30
        elif self.diff == "Difficile":
            self.delai_action = 10
        else:
            self.delai_action = 20

        #self.actions={"creerouvrier":self.creerouvrier,
        #              "ouvrierciblermaison":self.ouvrierciblermaison,
        #              "colorierouvrier":self.colorierouvrier,
        #              "ciblerbalise":self.ciblerbalise}

    #Override la méthode de base
    def creer_point_origine(self, x, y):
        idmaison = get_prochain_id()
        self.batiments["maison"][idmaison] = Maison(self, idmaison, self.couleur, x, y, "maison")

        
    def colorierouvrier(self):
        if self.ouvriers.keys():
            idouvrier=random.choice(list(self.ouvriers.keys()))
            h=self.ouvriers[idouvrier]
            h.couleur=h.maison.couleur
        
    def ouvrierciblermaison(self):
        if self.ouvriers:
            idouvrier=random.choice(list(self.ouvriers.keys()))
            self.ouvriers[idouvrier].trouvercible(self.parent.joueurs)
        
    def creerouvrier(self):
        #idmaison=random.choice(list(self.maisons.keys()))
        #maison = self.batiments["maison"][0]
        #chatgpt******************************
        idmaison = next(iter(self.batiments["maison"].keys()))
        maison = self.batiments["maison"][idmaison]
        #*************************************
        sorteperso="ouvrier"
        batimentsource="maison"
        
        #maison=self.maisons[idmaison]
        x=maison.x+40+(random.randrange(30)-15)
        y=maison.y +(random.randrange(30)-15)
        pos = [x, y]
        #self.persos["ouvrier"][idouvrier]=Ouvrier(self,idouvrier,maison,x,y)

        action = [self.nom, "creerperso", [sorteperso, batimentsource, idmaison, pos]]
        self.parent.action_AI_vers_controleur(action)
        print(f"IA {self.nom}: Action créer ouvrier envoyée")


        
    #Comment fonctionne sa prise de décision: il cible la plus proche? n'importe quelle? a-t-il besoin de la fonction ciblerununit?
    #On va sûrement faire une attaque de tous les units plutôt que ciblée (version naive), plus tard on ajoute qu'il cible les units selon leurs forces
    
    # def ciblerbalise(self):
    #     pass
        
    #def jouerprochaincoup(self):
    #    self.decideraction()
    #    
    #    for i in self.ouvriers.keys():
    #        self.ouvriers[i].deplacer()
    

    #RENDU ICI : FAIRE SPAWN LE BONHOMME, ÇA NE FONCTIONNE PAS TOUT A FAIT*******************************************
    def jouer_prochain_coup(self): #nom à changer
        #Ordre de prioritée d'attaque soldats > ouvriers > bâtiments
        #Quand un ouvrier est idle, il l'envoie chercher de nouvelles ressources (ce qu'il a besoin > le plus proche)
        #Quand il veut construire un bâtiment ou créer une unité, il va cher
        #Enovyer plus d'ouvriers quand on est low en une ressource (<300)

        for typ, dico in self.persos.items():
            for p in list(dico.values()):
                p.mettre_a_jour_vision()
                p.jouer_prochain_coup()

        if self.delai_action==0:
            #action=random.choice(list(self.actions.keys())) #On ne veut pas que ses choix soient random
            #self.actions[action]()
            self.decider_action()
            self.delai_action=20
        else:
            self.delai_action-=1
        

    def decider_action(self):
        # anti-spam
        if self.delai_action > 0:
            self.delai_action -= 1
            return

        # 0) sécurité : au moins 1 ouvrier (respecte le plafond cibles_unites["ouvrier"])
        if len(self.persos["ouvrier"]) < self.cibles_unites["ouvrier"]:
            intent = self.decider_entrainement()
            if intent and intent[0] == "ouvrier":
                self.agir_entrainement(*intent)
                self.delai_action = 10  # petit cooldown
                return

        # 1) Construire si besoin (abri -> caserne), une seule action
        intent_bat = self.decider_construction()
        if intent_bat:
            self.agir_construction(*intent_bat)
            self.delai_action = 10
            return

        # 2) Produire des unités (respecte plafonds), une seule action
        intent_unit = self.decider_entrainement()
        if intent_unit:
            self.agir_entrainement(*intent_unit)
            self.delai_action = 8
            return

        # 3) Récolte : peut en envoyer plusieurs, mais raisonnable
        intentions = self.decider_recolte()
        for id_ouvrier, t, idr in intentions[:3]:  # limite 3 ordres par tick
            self.agir_recolte(id_ouvrier, t, idr)
        if intentions:
            self.delai_action = 4

 
    

    # récolte des infos ##########

    # --- Helpers d'état (aucun effet de bord) ------------------------------------

    def _ouvriers_libres(self, max_n=2):
        libres = []
        for id_ouvrier, ouvrier in self.persos["ouvrier"].items():
            etat = getattr(ouvrier, "actioncourante", None)
            if etat in (None, "", "idle"):
                libres.append(id_ouvrier)
            if len(libres) >= max_n:
                break
        return libres

    def _peut_payer_batiment(self, type_bat):
        vals = type(self).valeurs  # Joueur.valeurs (coûts) :contentReference[oaicite:3]{index=3}
        for ress, cout in vals[type_bat].items():
            if ress != "delai" and self.ressources[ress] < cout:
                print("Too broke")
                return False
        return True

    def _batiment_quelconque(self, type_bat):
        if not self.batiments[type_bat]:
            return None, None
        idb = next(iter(self.batiments[type_bat].keys()))
        return idb, self.batiments[type_bat][idb]

    def _position_autour(self, cx, cy, rayon=140):
        dx = random.randrange(-rayon, rayon)
        dy = random.randrange(-rayon, rayon)
        x = max(0, min(self.parent.aireX - 1, cx + dx))
        y = max(0, min(self.parent.aireY - 1, cy + dy))
        return [x, y]

    def _ordre_priorite_ressources(self):
        ordre = ["arbre", "roche", "daim", "aureus"]
        # booste celles en manque
        for cle in ("nourriture", "arbre", "roche", "aureus"):
            if self.ressources.get(cle, 9999) < 150:
                if cle == "nourriture":
                    for t in ("daim"):
                        if t in ordre: ordre.remove(t)
                        ordre.insert(0, t)
                else:
                    if cle in ordre: ordre.remove(cle)
                    ordre.insert(0, cle)
        return ordre

    def _ressource_plus_proche(self, ouvrier, types):
        meilleure, best = None, 10**9
        for t in types:
            for idr, obj in self.parent.biotopes.get(t, {}).items():  # sur le modèle :contentReference[oaicite:4]{index=4}
                if getattr(obj, "valeur", 1) <= 0:
                    continue
                d = Helper.calcDistance(ouvrier.x, ouvrier.y, obj.x, obj.y)
                if d < best:
                    best = d
                    meilleure = (t, idr)
        return meilleure



    # def ordre_priorite_ressources(self):
    #     # Base "meta-RTS": bois > pierre > nourriture > or
    #     ordre = ["arbre", "roche", "daim", "eau", "aureus"]

    #     # Ajuste selon stocks: si une ressource tombe < 150, pousse-la en tête
    #     manquantes = sorted(self.ressources.keys(), key=lambda k: self.ressources[k])
    #     # garde l'ordre de base en injectant celles qui manquent le plus devant
    #     for r in reversed(manquantes):
    #         if self.ressources[r] < 150 and r in ["nourriture", "arbre", "roche", "aureus"]:
    #             if r == "nourriture":
    #                 # map nourriture -> sources concrètes visibles (daim/eau en premier)
    #                 for t in ["daim", "eau"]:
    #                     if t in ordre:
    #                         ordre.remove(t)
    #                     ordre.insert(0, t)
    #             else:
    #                 if r in ordre:
    #                     ordre.remove(r)
    #                 ordre.insert(0, r)
    #     return ordre
    
    # def _ressource_plus_proche(self, ouvrier, types):
    #     # types: liste ordonnée ("arbre", "roche", "daim", "eau", "aureus", ...)

    #     modele = self.parent  # le Modele
    #     meilleur = None
    #     meilleure_dist = 10**9
    #     meilleur_type = None

    #     for t in types:
    #         for rid, obj in modele.biotopes.get(t, {}).items():  # Les biotopes vivent sur le modèle/Partie :contentReference[oaicite:1]{index=1}
    #             if getattr(obj, "valeur", 1) <= 0:
    #                 continue
    #             d = Helper.calcDistance(ouvrier.x, ouvrier.y, obj.x, obj.y)
    #             if d < meilleure_dist:
    #                 meilleure_dist = d
    #                 meilleur = (t, rid)  # ← seulement 2 valeurs
    #     return meilleur

    # --- Décision (aucun effet de bord) ------------------------------------------

    def decider_construction(self):
        """Retourne (type_bat, ids_ouvriers, pos) ou None."""
        nb_abri = len(self.batiments["abri"])
        nb_caserne = len(self.batiments["caserne"])

        type_bat = None
        if nb_abri < 1 and self._peut_payer_batiment("abri"):
            type_bat = "abri"
        elif nb_caserne < 1 and self._peut_payer_batiment("caserne"):
            type_bat = "caserne"
        if not type_bat:
            return None

        ids_ouvriers = self._ouvriers_libres(max_n=2)
        if not ids_ouvriers:
            return None

        id_maison, maison = self._batiment_quelconque("maison")
        if not id_maison:
            return None
        pos = self._position_autour(maison.x, maison.y, 140)
        return (type_bat, ids_ouvriers, pos)

    def decider_entrainement(self):
        """
        Retourne (type_unite, type_batiment, id_batiment, pos) ou None.
        Respecte les plafonds `self.cibles_unites`.
        """
        cibles = self.cibles_unites

        # 1) Ouvriers via maison (respecte le plafond)
        id_maison, maison = self._batiment_quelconque("maison")
        if id_maison and len(self.persos["ouvrier"]) < cibles["ouvrier"]:
            pos = [maison.x + 60 + (random.randrange(30) - 15),
                maison.y + (random.randrange(30) - 15)]
            return ("ouvrier", "maison", id_maison, pos)

        # 2) Soldats/archers via caserne (respecte plafonds)
        id_caserne, caserne = self._batiment_quelconque("caserne")
        if not id_caserne:
            return None

        def manque(t): return max(0, cibles[t] - len(self.persos[t]))
        for t in sorted(("soldat", "archer"), key=lambda x: (-manque(x), x)):
            if manque(t) > 0:
                pos = [caserne.x + 60 + (random.randrange(30) - 15),
                    caserne.y + (random.randrange(30) - 15)]
                return (t, "caserne", id_caserne, pos)

        return None

    def decider_recolte(self):
        """Retourne une liste [(id_ouvrier, type_ress, id_ress), ...]."""
        intentions = []
        ordre = self._ordre_priorite_ressources()
        for id_ouvrier, ouvrier in self.persos["ouvrier"].items():
            etat = getattr(ouvrier, "actioncourante", None)
            if etat in ("ciblerressource","ramasserressource","ciblerproie",
                        "validerjavelot","retourbatimentmere","construirebatiment"):
                continue
            cible = self._ressource_plus_proche(ouvrier, ordre)
            if cible:
                t, idr = cible
                intentions.append((id_ouvrier, t, idr))
        return intentions

    
    # --- Actions (effet de bord : envoie vers le moteur) --------------------------

    def agir_construction(self, type_bat, ids_ouvriers, pos):
        action = [self.nom, "construirebatiment", [ids_ouvriers, type_bat, pos]]
        self.parent.action_AI_vers_controleur(action)  # file d’actions :contentReference[oaicite:5]{index=5}

    def agir_entrainement(self, type_unite, type_batiment, id_batiment, pos):
        action = [self.nom, "creerperso", [type_unite, type_batiment, id_batiment, pos]]
        self.parent.action_AI_vers_controleur(action)

    def agir_recolte(self, id_ouvrier, type_ress, id_ress):
        if type_ress in ("daim", "eau"):
            action = [self.nom, "chasserressource", [type_ress, id_ress, [id_ouvrier]]]
        else:
            action = [self.nom, "ramasserressource", [type_ress, id_ress, [id_ouvrier]]]
        self.parent.action_AI_vers_controleur(action)


      
    
    ## action de récolter ressource ###############

    # def envoyer_ouvriers_recolter(self):
    #     if not self.persos["ouvrier"]:
    #         return

    #     ordre = self.ordre_priorite_ressources()
    #     for oid, ouvrier in self.persos["ouvrier"].items():
    #         # Ne reroute pas un ouvrier déjà occupé
    #         if getattr(ouvrier, "actioncourante", None) in ("ciblerressource", "ramasserressource",
    #                                                     "ciblerproie", "validerjavelot",
    #                                                     "retourbatimentmere", "construirebatiment"):
    #             continue

    #         cible = self._ressource_plus_proche(ouvrier, ordre)
            
    #         if not cible:
    #             continue

    #         t, rid,  = cible
    #         # Action selon type
    #         if t in ("daim", "eau"):
    #             action = [self.nom, "chasserressource", [t, rid, [oid]]]
    #         else:
    #             action = [self.nom, "ramasserressource", [t, rid, [oid]]]

    #         self.parent.action_AI_vers_controleur(action)

