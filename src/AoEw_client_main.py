## -*- Encoding: UTF-8 -*-

#MORT import requests
from AoEw_vue import *
from AoEw_modele import *
import Users as us
import pickle
from pathlib import Path


class Controleur():
    def __init__(self):
        #MORT self.ego_serveur = 0 # 1 si le joueur a creer la partie (seul lui peut 'lancer' la partie)
        self.user_manager = us.UserManager()
        self.objets = []  # Liste de vos objets
        self.fichier_sauvegarde = 'data/sauvegarde.pkl'
        self.chargement = False
        self.iteration_boucle_jeu = 0
        self.actions_requises = []
        self.user = None
        self.partie = None
        self.nom_joueur_local = ""
        self.sauvegardes = []
        self.after_id = None
        # liste des noms de joueurs
        self.joueurs = self.user_manager.list_all_users()
        #MORT self.prochain_splash = None # requis pour sortir du splash et passer au lobby
        self.on_joue = 1 # si 0, indique qu'on saute un tour dans la boucle de jeu
        self.delai_de_boucle_de_jeu = 40
        # frequence des appels vers le serveur
        #MORT self.modulo_appeler_serveur = 4
        # adresses du URL du serveur de jeu, adresse 127.0.0.1 est pour des tests avec un serveur local... utile pour tester
        # self.url_serveur = "http://jmdeschamps.pythonanywhere.com"
        #MORT self.url_serveur = "http://127.0.0.1:8000"
        #MORT self.session = None
        self.vue = Vue(self, self.nom_joueur_local)

        self.vue.root.mainloop()

    # MORT
    # # methode speciale pour remettre les parametres du serveur a leurs valeurs par defaut
    # def reset_partie(self):
    #     le_url = self.url_serveur + "/reset_jeu"
    #     rep_text = self.appeler_serveur(le_url, 0)
    #     self.vue.update_splash(rep_text[0][0])
    #     return rep_text

    # a partir du splash, permet de creer une partie (lance le lobby pour permettre a d'autres joueurs de se connecter)
    def creer_partie(self, nom_joueur_local):
        # MORT
        # if self.prochain_splash:
        #     self.vue.root.after_cancel(self.prochain_splash)
        #     self.prochain_splash = None
        # self.nom_joueur_local = nom_joueur_local
        # url = self.url_serveur + "/creer_partie"
        # data = {'nom': self.nom_joueur_local
        #         }
        # reptext = self.appeler_serveur(url, data, "POST")
        # self.ego_serveur = True  # je suis la personne qui a demarrer une nouvelle partie
        # MORT
        if not nom_joueur_local or nom_joueur_local == "":
            nom_joueur_local = "invité"

        self.vue.root.title("je suis " + nom_joueur_local)
        self.nom_joueur_local = nom_joueur_local
        self.vue.changer_cadre("lobby")
        #MORT self.boucler_sur_lobby()

    # MORT
    # def inscrire_joueur(self, nom, urljeu):
    #     if self.prochain_splash:
    #         self.vue.root.after_cancel(self.prochain_splash)
    #         self.prochain_splash = None
    #     if nom:
    #         self.nom_joueur_local = nom
    #     url = self.url_serveur + "/inscrire_joueur"
    #     params = {"nom": self.nom_joueur_local}
    #     reptext = self.appeler_serveur(url, params, "POST")
    #     self.vue.root.title("je suis " + self.nom_joueur_local)
    #     self.vue.changer_cadre("lobby")
    #     self.boucler_sur_lobby()


    def lancer_partie(self):
        self.initialiser_partie()
    # MORT
    #     url = self.url_serveur + "/lancer_partie"
    #     params = {"nom": self.nom_joueur_local}
    #     reptext = self.appeler_serveur(url, params, "POST")

    # methode de demarrage local de la boucle de jeu (partie demarre ainsi)
    def initialiser_partie(self, nb_IAs=1):
        # on recoit les divers parametres d'initialisation du serveur
        # MORT initaleatoire = mondict[1][0][0]
        # ment, decommenter un ligne et commenter l'autre
        # mais pour tester c'est bien de toujours avoir la meme suite de random
        # random ALEATOIRE fourni par le serveur
        # random.seed(int(initaleatoire))
        # random FIXE pour test
        random.seed(12473)
        # # on recoit la derniere liste des joueurs pour la partie
        # listejoueurs = []
        # for i in self.joueurs:
        #     listejoueurs.append(i[0])
        # on cree le modele (la partie)
        if self.partie == None:
            self.partie = Partie(self, self.nom_joueur_local, nb_IAs)
        # on passe le modele a la vue puisqu'elle trouvera toutes le sinfos a dessiner
        self.vue.modele = self.partie
        # on met la vue a jour avec les infos de partie
        self.vue.initialiser_avec_modele(self.chargement)
        # on change le cadre la fenetre pour passer dans l'interface de jeu
        self.vue.changer_cadre("jeu")
        self.vue.centrer_maison()
        # on lance la boucle de jeu
        self.boucler_sur_jeu()

    # MORT
    # APRES AVOIR OBTENU UNE CONNECTION AU SERVEUR
    # def initialiser_splash_post_connection(self,url_serveur):
    #     self.session = requests.Session()
    #     self.url_serveur = url_serveur
    #     self.boucler_sur_splash()

    # MORT
    # boucle de communication initiale avec le serveur pour creer ou s'inscrire a la partie
    # def boucler_sur_splash(self):
    #     url = self.url_serveur + "/tester_jeu"
    #     params = {"nom": self.nom_joueur_local}
    #     mondict = self.appeler_serveur(url, params)
    #     #print(self.nom_joueur_local, mondict)
    #     if mondict:
    #         self.vue.update_splash(mondict[0])
    #     self.prochain_splash = self.vue.root.after(50, self.boucler_sur_splash)

    # MORT
    # on boucle sur le lobby en attendant l'inscription de tous les joueurs attendus
    # def boucler_sur_lobby(self):
    #     url = self.url_serveur + "/boucler_sur_lobby"
    #     params = {"nom": self.nom_joueur_local}
    #     mondict = self.appeler_serveur(url, params, "POST")
    #     # si l'etat est courant, c'est que la partie vient d'etre lancer
    #     if "courante" in mondict[0]:
    #         self.initialiser_partie(mondict)
    #     else:
    #         self.joueurs = mondict
    #         self.vue.update_lobby(mondict)
    #         self.vue.root.after(50, self.boucler_sur_lobby)

    # La boucle principale pour jouer une partie
    def boucler_sur_jeu(self):
        self.iteration_boucle_jeu += 1
        # MORT
        # test pour communiquer avec le serveur periodiquement
        # if self.iteration_boucle_jeu % self.modulo_appeler_serveur == 0:
        #     actions = []
        #     if self.actions_requises:
        #         actions = self.actions_requises
        #         self.actions_requises = []
        #     url = self.url_serveur + "/boucler_sur_jeu"
        #     if actions == []:
        #         actions = ''
        #     data = {"nom": self.nom_joueur_local,
        #               "iteration_boucle_jeu": self.iteration_boucle_jeu,
        #               "actions_requises": actions}
        #     try:
        #         mondict = self.appeler_serveur(url, data, method = "POST")
        #         # verifie pour requete d'attente d'un joueur plus lent
        #         if "ATTENTION" in mondict:
        #             print("SAUTER TOUR")
        #             self.on_joue = 0
        #         elif mondict:
        #             self.partie.ajouter_actions_a_faire(self.iteration_boucle_jeu,mondict)
        #
        #     except requests.exceptions.RequestException as e:
        #         print("An error occurred:", e)
        #         self.on_joue = 0
        # Précaution supplémentaire
        if not self.partie:
            print("⚠️ Partie inexistante, arrêt de la boucle")
            return

        if self.actions_requises:
            self.actions_requises.insert(0, self.iteration_boucle_jeu + 1)
            self.partie.ajouter_actions_a_faire(self.iteration_boucle_jeu,[self.actions_requises])
            self.actions_requises = []

        if self.on_joue:
            # envoyer les messages au modele et a la vue de faire leur job
            self.partie.jouer_prochain_coup(self.iteration_boucle_jeu)
            self.vue.afficher_jeu()
        else:
            self.iteration_boucle_jeu -= 1
            self.on_joue = 1
        # appel ulterieur de la meme fonction jusqu'a l'arret de la partie
        if self.vue and self.vue.root:
            self.after_id = self.vue.root.after(self.delai_de_boucle_de_jeu, self.boucler_sur_jeu)
    def detruire_partie(self):
        self.partie = None

    def arreter_boucle_jeu(self):
        """Arrête la boucle de jeu en cours et nettoie les actions"""
        if self.after_id:
            try:
                self.vue.root.after_cancel(self.after_id)
                print("Boucle de jeu précédente arrêtée.")
            except Exception as e:
                print(f"Erreur lors de l'arrêt de la boucle: {e}")
            self.after_id = None

        # 🔴 NETTOYER TOUTES LES ACTIONS EN ATTENTE
        self.actions_requises = []
        print("Actions en attente vidées.")
    ###################################################################
    # MORT
    # # fonction qui fait les appels au serveur
    # def appeler_serveur(self, url, paramsjm, method="GET"):
    #     if method == "GET":
    #         response = self.session.get(url, params=paramsjm)
    #     elif method == "POST":
    #         response = self.session.post(url, json=paramsjm)
    #     response.raise_for_status()
    #     return response.json()
    ###################################################################
    # generateur de nouveau nom (erreur possible si doublon)
    def generer_nom(self):
        nom_joueur_local = "JAJA_" + str(random.randrange(100, 1000))
        return nom_joueur_local

    def abandonner(self):
        action = [self.nom_joueur_local, "abandonner", [self.nom_joueur_local + ": J'ABANDONNE !"]]
        self.actionsrequises = action
        self.vue.root.after(500, self.vue.root.destroy)
    ###############################################################################
    ### Placez vos fonctions ici
    def afficher_batiment(self, nom, batiment):
        self.vue.afficher_batiment(nom, batiment)

    def afficher_bio(self, bio):
        self.vue.afficher_bio(bio)

    def installer_batiment(self, nomjoueur, batiment):
        x1, y1, x2, y2 = self.vue.afficher_batiment(nomjoueur, batiment)
        return [x1, y1, x2, y2]

    def trouver_valeurs(self):
        vals = self.partie.trouver_valeurs()
        return vals

    def enregistrerUser(self, username, password):
        message = self.user_manager.add_user(username, password)
        if message == "Réussi":
            self.nom_joueur_local = username
            self.user = self.user_manager.get_user_data(username)
            return True
        if message == "Vide":
            return message
        else:
            self.nom_joueur_local = ""
            return False
    def loginUser(self, username, password):
        message = self.user_manager.get_user(username, password)
        if message == True:
            self.nom_joueur_local = username
            self.user = self.user_manager.get_user_data(username)
            return True
        if message == "Vide":
            return message
        else:
            self.nom_joueur_local = ""
            return False

    def sauvegarde(self, nom_sauvegarde=None):
        """
        Sauvegarde la partie avec le nom du joueur comme identifiant

        Args:
            nom_sauvegarde: nom de la sauvegarde (utilise self.nom_joueur_local par défaut)
        """
        if nom_sauvegarde is None:
            nom_sauvegarde = self.nom_joueur_local

        # Si c'est un invité sans nom, générer un nom par défaut
        if not nom_sauvegarde or nom_sauvegarde == "":
            nom_sauvegarde = "invité"

        fichier = self.fichier_sauvegarde

        # Créer le dossier si nécessaire
        Path(fichier).parent.mkdir(parents=True, exist_ok=True)

        try:
            # Charger le dictionnaire des sauvegardes existantes
            sauvegardes_dict = {}
            if Path(fichier).exists():
                try:
                    with open(fichier, 'rb') as f:
                        sauvegardes_dict = pickle.load(f)
                        # Vérifier que c'est bien un dictionnaire
                        if not isinstance(sauvegardes_dict, dict):
                            sauvegardes_dict = {}
                except Exception as e:
                    print(f"Impossible de charger les sauvegardes existantes: {e}")
                    sauvegardes_dict = {}

            # Préparer la nouvelle sauvegarde
            import datetime
            self.partie.parent = None
            data_save = {
                'partie': self.partie,
                'iteration': self.iteration_boucle_jeu,
                'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'joueur': nom_sauvegarde
            }



            # Ajouter ou mettre à jour la sauvegarde pour ce joueur
            sauvegardes_dict[nom_sauvegarde] = data_save

            # Sauvegarder tout le dictionnaire
            with open(fichier, 'wb') as f:
                pickle.dump(sauvegardes_dict, f)
            self.partie.parent = self

            print(f"Sauvegarde réussie pour '{nom_sauvegarde}' (total: {len(sauvegardes_dict)} sauvegardes)")
            messagebox.showinfo("Succes", "Partie sauvegardée.")
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde : {e}")

            import traceback
            traceback.print_exc()
            # Restaurer la référence parent même en cas d'erreur
            if hasattr(self, 'partie') and self.partie:
                self.partie.parent = self
            return False

    def charger(self, nom_sauvegarde=None):
        """
        Charge une sauvegarde selon le nom du joueur

        Args:
            nom_sauvegarde: nom de la sauvegarde à charger (utilise self.nom_joueur_local par défaut)
        """
        if nom_sauvegarde is None:
            nom_sauvegarde = self.nom_joueur_local

        if not nom_sauvegarde:
            print("Erreur: Aucun nom de joueur spécifié")
            return False

        fichier = self.fichier_sauvegarde

        try:

            self.arreter_boucle_jeu()
            self.iteration_boucle_jeu = 0
            # 🔴 S'il existe une ancienne partie, la vider proprement
            if self.partie:
                try:
                    # Vider les actions du modèle aussi
                    if hasattr(self.partie, 'actions_a_faire'):
                        self.partie.actions_a_faire = {}
                    if hasattr(self.partie, 'actions_futures'):
                        self.partie.actions_futures = []
                except Exception as e:
                    print(f"Erreur nettoyage partie: {e}")
                self.partie = None

            if not Path(fichier).exists():
                print(f"Le fichier {fichier} n'existe pas")
                return False

            with open(fichier, 'rb') as file:
                sauvegardes_dict = pickle.load(file)

                # Vérifier que c'est bien un dictionnaire
                if not isinstance(sauvegardes_dict, dict):
                    raise ValueError("Le fichier ne contient pas un dictionnaire de sauvegardes")

                # Vérifier que la sauvegarde existe
                if nom_sauvegarde not in sauvegardes_dict:
                    print(f"Aucune sauvegarde trouvée pour '{nom_sauvegarde}'")
                    print(f"Sauvegardes disponibles: {', '.join(sauvegardes_dict.keys())}")
                    return False

                # Charger la sauvegarde
                sauvegarde_data = sauvegardes_dict[nom_sauvegarde]
                self.arreter_boucle_jeu()
                # Support pour ancien format (liste) et nouveau format (dict)
                if isinstance(sauvegarde_data, dict):
                    self.partie = sauvegarde_data['partie']
                    self.iteration_boucle_jeu = sauvegarde_data['iteration']
                    date_sauvegarde = sauvegarde_data.get('date', 'inconnue')
                elif isinstance(sauvegarde_data, list) and len(sauvegarde_data) >= 2:
                    # Support pour ancien format
                    self.partie = sauvegarde_data[0]
                    self.iteration_boucle_jeu = sauvegarde_data[1]
                    date_sauvegarde = 'inconnue'
                else:
                    raise ValueError("Format de sauvegarde invalide")

                self.partie.parent = self
            if hasattr(self.vue, 'canevas'):
                self.vue.canevas.delete("ALL")
            if hasattr(self.vue, 'minicarte'):
                self.vue.minicarte.delete("ALL")

            # Reconnecter la vue au modèle existant
            self.chargement = True
            self.vue.modele = self.partie
            self.vue.changer_cadre("jeu")
            self.vue.initialiser_avec_modele(self.chargement)
            self.vue.centrer_maison()
            self.boucler_sur_jeu()
            print(f"Sauvegarde de '{nom_sauvegarde}' chargée avec succès (date: {date_sauvegarde})")
            return True

        except Exception as e:
            print(f"Une erreur est arrivée: {e}")
            import traceback
            traceback.print_exc()
            return False

    def lister_sauvegardes(self):
        """
        Liste toutes les sauvegardes disponibles dans le fichier

        Returns: Liste de tuples (nom_joueur, iteration, date) ou liste vide si erreur
        """
        fichier = self.fichier_sauvegarde

        try:
            if not Path(fichier).exists():
                print("Aucun fichier de sauvegarde trouvé")
                return []

            with open(fichier, 'rb') as file:
                sauvegardes_dict = pickle.load(file)

                if not isinstance(sauvegardes_dict, dict):
                    return []

                sauvegardes_info = []
                for nom_joueur, sauvegarde_data in sauvegardes_dict.items():
                    if isinstance(sauvegarde_data, dict):
                        iteration = sauvegarde_data.get('iteration', '?')
                        date = sauvegarde_data.get('date', 'inconnue')
                        sauvegardes_info.append((nom_joueur, iteration, date))
                    elif isinstance(sauvegarde_data, list) and len(sauvegarde_data) >= 2:
                        iteration = sauvegarde_data[1]
                        sauvegardes_info.append((nom_joueur, iteration, 'inconnue'))

                return sauvegardes_info

        except Exception as e:
            print(f"Erreur lors de la lecture des sauvegardes: {e}")
            return []

    def supprimer_sauvegarde(self, nom_sauvegarde):
        """
        Supprime une sauvegarde spécifique

        Args:
            nom_sauvegarde: nom de la sauvegarde à supprimer
        """
        fichier = self.fichier_sauvegarde

        try:
            if not Path(fichier).exists():
                print(f"Le fichier {fichier} n'existe pas")
                return False

            with open(fichier, 'rb') as file:
                sauvegardes_dict = pickle.load(file)

            if not isinstance(sauvegardes_dict, dict):
                print("Format de fichier invalide")
                return False

            if nom_sauvegarde not in sauvegardes_dict:
                print(f"Aucune sauvegarde trouvée pour '{nom_sauvegarde}'")
                return False

            # Supprimer la sauvegarde
            del sauvegardes_dict[nom_sauvegarde]

            # Sauvegarder le dictionnaire mis à jour
            with open(fichier, 'wb') as file:
                pickle.dump(sauvegardes_dict, file)

            print(f"Sauvegarde de '{nom_sauvegarde}' supprimée avec succès")
            return True

        except Exception as e:
            print(f"Erreur lors de la suppression: {e}")
            return False



if __name__ == '__main__':
    print("Bienvenue au RTS")
    c = Controleur()
    # print("FIN DE PROGRAMME")
