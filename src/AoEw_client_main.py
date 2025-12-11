## -*- Encoding: UTF-8 -*-

#MORT import requests
from AoEw_vue import *
from AoEw_modele import *
import Users as us
import pickle
from pathlib import Path
from AoEw_divers import reset_prochain_id

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
        self.jeu_en_pause = False
        # liste des noms de joueurs
        self.joueurs = self.user_manager.list_all_users()
        #MORT self.prochain_splash = None # requis pour sortir du splash et passer au lobby
        self.on_joue = 1 # si 0, indique qu'on saute un tour dans la boucle de jeu
        self.delai_de_boucle_de_jeu = 40
        self.info_ia = [] 
        self.mode_de_jeu = "commerce"  # solo ou multi
        self.default_seed = 14777
        self.seed = 12473  # valeur de random pour la partie
        self.victoire_msg = "Partie finie."
        self.conditions_victoire = {}
        
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


    def fin_de_partie(self, message):
        self.victoire_msg = message
        print(self.victoire_msg)

        self.arreter_boucle_jeu()
        # self.detruire_partie()
        self.vue.nettoyer_interface_jeu()
        self.vue.maj_message_victoire(message)
        self.vue.changer_topblack("blackgame")
        self.vue.changer_toplevel("gagner")


    def lancer_partie(self):
        self.initialiser_partie()
    # MORT
    #     url = self.url_serveur + "/lancer_partie"
    #     params = {"nom": self.nom_joueur_local}
    #     reptext = self.appeler_serveur(url, params, "POST")

    # methode de demarrage local de la boucle de jeu (partie demarre ainsi)
    def initialiser_partie(self):
        # on recoit les divers parametres d'initialisation du serveur
        # MORT initaleatoire = mondict[1][0][0]
        # ment, decommenter un ligne et commenter l'autre
        # mais pour tester c'est bien de toujours avoir la meme suite de random
        # random ALEATOIRE fourni par le serveur
        # random.seed(int(initaleatoire))
        # random FIXE pour test
        self.vue.changer_cadre("loading")
        if hasattr(self.vue, 'demarrer_animation_loading'):
            self.vue.demarrer_animation_loading()
        if hasattr(self.vue, 'loading_progress_var'):
            self.vue.loading_progress_var.set("Initialisation de la partie...")
        self.vue.root.update()
        self.jeu_en_pause = False
        reset_prochain_id()
        self.iteration_boucle_jeu = 0

        random.seed(self.seed)
        # # on recoit la derniere liste des joueurs pour la partie
        # listejoueurs = []
        # for i in self.joueurs:
        #     listejoueurs.append(i[0])
        # on cree le modele (la partie)
        self.partie = Partie(self, self.nom_joueur_local, self.info_ia , self.mode_de_jeu)
        # on passe le modele a la vue puisqu'elle trouvera toutes le sinfos a dessiner
        self.vue.modele = self.partie
        # on met la vue a jour avec les infos de partie
        self.vue.initialiser_avec_modele(self.chargement)
        # on change le cadre la fenetre pour passer dans l'interface de jeu
        self.vue.changer_cadre("jeu")
        self.vue.centrer_maison()
        # on lance la boucle de jeu
        self.boucler_sur_jeu()


    # La boucle principale pour jouer une partie
    def boucler_sur_jeu(self):
        self.iteration_boucle_jeu += 1

        # Précaution supplémentaire
        if not self.partie:
            print("⚠️ Partie inexistante, arrêt de la boucle")
            return

        if self.mode_de_jeu == "conquete":
            joueurs = getattr(self.partie, "joueurs", {})

            def extract(j):
                # support dict or object
                if isinstance(j, dict):
                    nom = j.get("nom") or j.get("name")
                    couleur = j.get("couleur") or j.get("color")
                    difficulte = j.get("difficulte") or j.get("diff")
                    typ = j.get("type")
                else:
                    nom = getattr(j, "nom", None)
                    couleur = getattr(j, "couleur", None)
                    difficulte = getattr(j, "diff", None) or getattr(j, "difficulte", None)
                    typ = getattr(j, "type", None)
                return nom, couleur, difficulte, typ

            conds = {}
            if isinstance(joueurs, dict):
                iterator = joueurs.values()
            else:
                try:
                    iterator = list(joueurs)
                except Exception:
                    iterator = []

            for pj in iterator:
                nom, couleur, difficulte, typ = extract(pj)
                if not nom or nom == self.nom_joueur_local:
                    continue
                conds[nom] = {"couleur": couleur}
                #conds[nom] = {"couleur": couleur, "difficulte": difficulte, "type": typ}
                #print(f"{nom} — couleur: {couleur}, difficulte: {difficulte}, type: {typ}")

            if conds:
                parts = []
                for nom, info in conds.items():
                    if isinstance(info, dict):
                        couleur = info.get("couleur")
                    else:
                        couleur = info
                    couleur_str = str(couleur) if couleur else "inconnue"
                    parts.append(f"{nom} ({couleur_str})")
                noms = " \n".join(parts)
                self.conditions_victoire = "Tous les conquérir \n" + noms
            else:
                self.conditions_victoire = "Tous les conquérir"
            try:
                self.vue.update_conditions_victoire_display()
            except Exception:
                pass

        if self.mode_de_jeu == "commerce":
            self.conditions_victoire = {"bois": 500 , "aureus": 350 , "nourriture": 300 , "roche": 450}
            self.vue.update_conditions_victoire_display()

            try:
                joueurs = getattr(self.partie, "joueurs", {})

                # Préparer un itérateur générique : supporte dict (nom->joueur) ou liste/iterable de joueurs
                if isinstance(joueurs, dict):
                    iterator = joueurs.items()
                else:
                    try:
                        iterator = [(getattr(j, "nom", str(i)), j) for i, j in enumerate(joueurs)]
                    except Exception:
                        # structure inconnue, rien à faire
                        return

                # Fonction utilitaire pour lire une ressource depuis différentes structures
                def get_res(ressources, cle, joueur=None):
                    # ressources peut être un dict
                    if isinstance(ressources, dict):
                        return ressources.get(cle, 0)
                    # si ressources a une méthode get (ex: mapping custom)
                    if hasattr(ressources, "get"):
                        try:
                            return ressources.get(cle, 0)
                        except Exception:
                            pass
                    # sinon, tenter de lire via attributs du joueur (ex: joueur.bois)
                    if joueur is not None:
                        # d'abord si le joueur a un attribut 'ressources' qui est un dict
                        r = getattr(joueur, "ressources", None)
                        if isinstance(r, dict):
                            return r.get(cle, 0)
                        # tenter attribut direct
                        if hasattr(joueur, cle):
                            try:
                                val = getattr(joueur, cle)
                                if val is None:
                                    return 0
                                return val
                            except Exception:
                                pass
                    return 0

                for jnom, joueur in iterator:

                    # Essayer plusieurs façons de récupérer les ressources du joueur
                    if isinstance(joueur, dict):
                        ressources = joueur.get("ressources", joueur)
                    else:
                        ressources = getattr(joueur, "ressources", None)

                    # Si on n'a pas de dict, construire un dict minimal en lisant les clés requises
                    if not isinstance(ressources, dict):
                        constructed = {}
                        for k in self.conditions_victoire.keys():
                            constructed[k] = get_res(ressources, k, joueur)
                        ressources = constructed

                    # Si toujours non dict (sécurité), on saute ce joueur
                    if not isinstance(ressources, dict):
                        continue

                    victoire = True
                    details = []

                    # vérifier chaque condition (ne pas s'arrêter au premier échec)
                    # gérer le cas où la partie utilise 'arbre' au lieu de 'bois' (ou autres variantes)
                    synonyms = {
                        'bois': ['arbre'],
                        'nourriture': ['nourriture'],
                        'roche': ['roche'],
                        'aureus': ['aureus' ]
                    }

                    for cle, seuil in self.conditions_victoire.items():
                        # tenter d'abord la clé telle quelle
                        valeur_raw = None
                        if isinstance(ressources, dict) and cle in ressources:
                            valeur_raw = ressources.get(cle, 0)
                        else:
                            valeur_raw = get_res(ressources, cle, joueur)

                        # si absent / nul et qu'il existe des synonymes, essayer-les
                        if (valeur_raw is None or valeur_raw == 0) and cle in synonyms:
                            for alt in synonyms[cle]:
                                if isinstance(ressources, dict) and alt in ressources:
                                    valeur_raw = ressources.get(alt, 0)
                                    break
                                val_alt = get_res(ressources, alt, joueur)
                                if val_alt:
                                    valeur_raw = val_alt
                                    break

                        try:
                            valeur_num = int(valeur_raw)
                        except Exception:
                            valeur_num = valeur_raw if isinstance(valeur_raw, (int, float)) else 0

                        details.append(f"{cle} = {valeur_num}/{seuil}")

                        if valeur_num < seuil:
                            victoire = False

                    # Si toutes les conditions sont remplies → victoire
                    if victoire:
                        details_str = "\n".join(details)
                        self.victoire_msg = (
                            f"'{jnom}' a atteint les conditions de victoire \n"
                            f"{details_str}. \nArrêt de la partie."
                        )
                        self.fin_de_partie(self.victoire_msg)
                        print(self.victoire_msg)
                        self.declencher_victoire(self.victoire_msg)
                        return

            except Exception as e:
                print(f"Erreur lors de la vérification de victoire : {e}")
                return

        

        if self.actions_requises:
            self.actions_requises.insert(0, self.iteration_boucle_jeu + 1)
            self.partie.ajouter_actions_a_faire(self.iteration_boucle_jeu,[self.actions_requises])
            self.actions_requises = []

        if not self.jeu_en_pause:
            self.iteration_boucle_jeu += 1
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

    def mettre_en_pause(self):
        """Met le jeu en pause sans arrêter la boucle"""
        self.jeu_en_pause = True
        print("Jeu mis en pause")

    def reprendre_jeu(self):
        """Reprend le jeu après une pause"""
        self.jeu_en_pause = False
        print("Jeu repris")
    def arreter_boucle_jeu(self):
        """Arrête la boucle de jeu en cours et nettoie les actions"""
        if self.after_id:
            try:
                self.vue.root.after_cancel(self.after_id)
                print("Boucle de jeu précédente arrêtée.")
            except Exception as e:
                print(f"Erreur lors de l'arrêt de la boucle: {e}")
            self.after_id = None

        #NETTOYER TOUTES LES ACTIONS EN ATTENTE
        self.actions_requises = []
        print("Actions en attente vidées.")

    def declencher_victoire(self, message: str):
        """Centralise l'envoi du message de victoire vers la vue puis arrête la partie proprement."""
        self.victoire_msg = message
        try:
            self.vue.maj_message_victoire(message)
        except Exception as e:
            print(f"Erreur maj message victoire : {e}")
        self.arreter_boucle_jeu()
        self.detruire_partie()
        self.vue.changer_topblack("blackgame")
        self.vue.changer_toplevel("gagner")
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

    def trouver_couts_persos(self):
        return self.partie.trouver_couts_persos()

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
        """
        if nom_sauvegarde is None:
            nom_sauvegarde = self.nom_joueur_local

        if not nom_sauvegarde:
            print("Erreur: Aucun nom de joueur spécifié")
            return False

        fichier = self.fichier_sauvegarde

        try:
            # ÉTAPE 1: Afficher l'écran de chargement
            self.vue.changer_cadre("loading")
            if hasattr(self.vue, 'demarrer_animation_loading'):
                self.vue.demarrer_animation_loading()
            self.vue.root.update()  # Force la mise à jour de l'interface

            # ÉTAPE 2: Mettre à jour le message de progression (optionnel)
            if hasattr(self.vue, 'loading_progress_var'):
                self.vue.loading_progress_var.set("Lecture du fichier de sauvegarde...")
                self.vue.root.update()

            self.arreter_boucle_jeu()
            self.iteration_boucle_jeu = 0

            # S'il existe une ancienne partie, la vider proprement
            if self.partie:
                try:
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

            # ÉTAPE 3: Charger les données
            if hasattr(self.vue, 'loading_progress_var'):
                self.vue.loading_progress_var.set("Chargement des données...")
                self.vue.root.update()

            with open(fichier, 'rb') as file:
                sauvegardes_dict = pickle.load(file)

                if not isinstance(sauvegardes_dict, dict):
                    raise ValueError("Le fichier ne contient pas un dictionnaire de sauvegardes")

                if nom_sauvegarde not in sauvegardes_dict:
                    print(f"Aucune sauvegarde trouvée pour '{nom_sauvegarde}'")
                    return False

                sauvegarde_data = sauvegardes_dict[nom_sauvegarde]
                self.arreter_boucle_jeu()

                # Support pour ancien format (liste) et nouveau format (dict)
                if isinstance(sauvegarde_data, dict):
                    self.partie = sauvegarde_data['partie']
                    self.iteration_boucle_jeu = sauvegarde_data['iteration']
                    date_sauvegarde = sauvegarde_data.get('date', 'inconnue')
                elif isinstance(sauvegarde_data, list) and len(sauvegarde_data) >= 2:
                    self.partie = sauvegarde_data[0]
                    self.iteration_boucle_jeu = sauvegarde_data[1]
                    date_sauvegarde = 'inconnue'
                else:
                    raise ValueError("Format de sauvegarde invalide")

                self.partie.parent = self

            # ÉTAPE 4: Préparer l'affichage
            if hasattr(self.vue, 'loading_progress_var'):
                self.vue.loading_progress_var.set("Préparation de la carte...")
                self.vue.root.update()

            if hasattr(self.vue, 'canevas'):
                self.vue.canevas.delete("ALL")
            if hasattr(self.vue, 'minicarte'):
                self.vue.minicarte.delete("ALL")

            # ÉTAPE 5: Initialiser le modèle (la partie la plus longue)
            if hasattr(self.vue, 'loading_progress_var'):
                self.vue.loading_progress_var.set("Génération du terrain...")
                self.vue.root.update()

            self.chargement = True
            self.vue.modele = self.partie

            # Utiliser after() pour laisser l'interface respirer
            def continuer_chargement():
                if hasattr(self.vue, 'loading_progress_var'):
                    self.vue.loading_progress_var.set("Chargement des ressources...")
                    self.vue.root.update()

                self.vue.initialiser_avec_modele(self.chargement)

                if hasattr(self.vue, 'loading_progress_var'):
                    self.vue.loading_progress_var.set("Finalisation...")
                    self.vue.root.update()

                self.vue.centrer_maison()
                self.jeu_en_pause = False

                # ÉTAPE 6: Arrêter l'animation et changer de cadre
                if hasattr(self.vue, 'arreter_animation_loading'):
                    self.vue.arreter_animation_loading()

                self.vue.changer_cadre("jeu")
                self.boucler_sur_jeu()

                print(f"Sauvegarde de '{nom_sauvegarde}' chargée avec succès (date: {date_sauvegarde})")

            # Utiliser after() pour laisser l'écran de chargement s'afficher
            self.vue.root.after(100, continuer_chargement)
            return True

        except Exception as e:
            print(f"Une erreur est arrivée: {e}")
            import traceback
            traceback.print_exc()

            # Arrêter l'animation en cas d'erreur
            if hasattr(self.vue, 'arreter_animation_loading'):
                self.vue.arreter_animation_loading()

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
