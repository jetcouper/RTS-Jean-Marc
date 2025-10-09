from AoEw_joueurs import *

# CORRECTION REQUISE : cette classe doit etre comlpetemnent revue 
# La classe IA herite des attributs et methodes mais redefinit les methodes... 
class IA(Joueur):
    def __init__(self,parent,nom,id, x,y):
        Joueur.__init__(self,parent,nom,id,x,y)

        self.delaiaction=20
        self.actions={"creerouvrier":self.creerouvrier,
                      "ouvrierciblermaison":self.ouvrierciblermaison,
                      "colorierouvrier":self.colorierouvrier,
                      "ciblerbalise":self.ciblerbalise}

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
        maison = self.batiments["maison"][0]
        sorteperso="ouvrier"
        batimentsource="maison"
        idmaison = maison.id
        idouvrier=get_prochain_id()
        
        #maison=self.maisons[idmaison]
        x=maison.x+40+(random.randrange(30)-15)
        y=maison.y +(random.randrange(30)-15)
        self.ouvriers[idouvrier]=Ouvrier(self,idouvrier,maison,x,y)

        
        
    #Comment fonctionne sa prise de décision: il cible la plus proche? n'importe quelle? a-t-il besoin de la fonction ciblerununit?
    #On va sûrement faire une attaque de tous les units plutôt que ciblée (version naive), plus tard on ajoute qu'il cible les units selon leurs forces
    
    def ciblerbalise(self):
        pass

    def chercher_nouvelle_ressource(self, typ, idreg):
        print("Je cherche nouvelle ressource")
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
    
    def jouerprochaincoup(self):
        #Ordre de prioritée d'attaque soldats > ouvriers > bâtiments
        #Quand un ouvrier est idle, il l'envoie chercher de nouvelles ressources (ce qu'il a besoin > le plus proche)
        #Quand il veut construire un bâtiment ou créer une unité, il va cher
        #Enovyer plus d'ouvriers quand on est low en une ressource (<300)
        if self.delaiaction==0:
            #action=random.choice(list(self.actions.keys())) #On ne veut pas que ses choix soient random
            #self.actions[action]()
            self.decideraction()
            self.delaiaction=20
        else:
            self.delaiaction-=1

            
    def decideraction(self):
        #TEST première action : Doit spawn un dude en début de game

        pass