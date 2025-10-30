from AoEw_joueurs import *

# CORRECTION REQUISE : cette classe doit etre comlpetemnent revue 
# La classe IA herite des attributs et methodes mais redefinit les methodes... 
class IA(Joueur):

    def __init__(self, parent, id, nom, couleur, x, y):
        Joueur.__init__(self, parent, id, nom, couleur, x, y)

        self.delaiaction=20
        
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
    
    def ciblerbalise(self):
        pass

    def chercher_nouvelle_ressource(self, typ, idreg):
        print("Ai cherche nouvelle ressource")
        if typ != "baie" and typ != "daim":
            reg = self.parent.parent.regions[typ]
            if idreg in reg:
                regspec = self.parent.parent.regions[typ][idreg]
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
            nb = len(self.parent.parent.biotopes[typ])
            for i in range(nb):
                rep = random.choice(list(self.parent.parent.biotopes[typ].keys()))
                obj = self.parent.parent.biotopes[typ][rep]
                if obj != self.cible:
                    distance = Helper.calcDistance(self.x, self.y, obj.x, obj.y)
                    if distance <= self.champvision:
                        return obj
            return None
        
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
            for p in dico.values():
                p.mettre_a_jour_vision()
                p.jouer_prochain_coup()

        if self.delaiaction==0:
            #action=random.choice(list(self.actions.keys())) #On ne veut pas que ses choix soient random
            #self.actions[action]()
            self.decideraction()
            self.delaiaction=20
        else:
            self.delaiaction-=1
        

    
    
            
    def decideraction(self):

        # ex: 1) s’assurer d’avoir au moins 1 ouvrier
        if len(self.persos["ouvrier"]) < 3:
            self.creerouvrier()

        # 2) envoyer les ouvriers vers la meilleure ressource
        self.envoyer_ouvriers_recolter()


    #### Arbre décisionnel pour les actions #####################
    def ordre_priorite_ressources(self):
        # Base "meta-RTS": bois > pierre > nourriture > or
        ordre = ["arbre", "roche", "daim", "eau", "aureus"]

        # Ajuste selon stocks: si une ressource tombe < 150, pousse-la en tête
        manquantes = sorted(self.ressources.keys(), key=lambda k: self.ressources[k])
        # garde l'ordre de base en injectant celles qui manquent le plus devant
        for r in reversed(manquantes):
            if self.ressources[r] < 150 and r in ["nourriture", "arbre", "roche", "aureus"]:
                if r == "nourriture":
                    # map nourriture -> sources concrètes visibles (daim/eau en premier)
                    for t in ["daim", "eau"]:
                        if t in ordre:
                            ordre.remove(t)
                        ordre.insert(0, t)
                else:
                    if r in ordre:
                        ordre.remove(r)
                    ordre.insert(0, r)
        return ordre
    

    # récolte des infos ##########
    def _ressource_plus_proche(self, ouvrier, types):
        # types: liste ordonnée ("arbre", "roche", "daim", "eau", "aureus", ...)

        modele = self.parent  # le Modele
        meilleur = None
        meilleure_dist = 10**9
        meilleur_type = None

        for t in types:
            for rid, obj in modele.biotopes.get(t, {}).items():  # Les biotopes vivent sur le modèle/Partie :contentReference[oaicite:1]{index=1}
                if getattr(obj, "valeur", 1) <= 0:
                    continue
                d = Helper.calcDistance(ouvrier.x, ouvrier.y, obj.x, obj.y)
                if d < meilleure_dist:
                    meilleure_dist = d
                    meilleur = (t, rid)  # ← seulement 2 valeurs
        return meilleur

      
    
    ## action de récolter ressource ###############

    def envoyer_ouvriers_recolter(self):
        if not self.persos["ouvrier"]:
            return

        ordre = self.ordre_priorite_ressources()
        for oid, ouvrier in self.persos["ouvrier"].items():
            # Ne reroute pas un ouvrier déjà occupé
            if getattr(ouvrier, "actioncourante", None) in ("ciblerressource", "ramasserressource",
                                                        "ciblerproie", "validerjavelot",
                                                        "retourbatimentmere", "construirebatiment"):
                continue

            cible = self._ressource_plus_proche(ouvrier, ordre)
            
            if not cible:
                continue

            t, rid,  = cible
            # Action selon type
            if t in ("daim", "eau"):
                action = [self.nom, "chasserressource", [t, rid, [oid]]]
            else:
                action = [self.nom, "ramasserressource", [t, rid, [oid]]]

            self.parent.action_AI_vers_controleur(action)