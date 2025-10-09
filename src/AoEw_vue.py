## -*- Encoding: UTF-8 -*-

from tkinter import ttk, messagebox
from tkinter.simpledialog import *
import os
from chargeurdimages import *
import AoEw_client_main as m # a enlever test only
import ctypes

from PIL import Image, ImageTk  # Pour redimensionner l’image


class Vue():
    def __init__(self, parent, nom_joueur_local): #, testdispo):
        self.parent = parent
        self.root = Tk()
        self.root.title("Age of Empire")
        self.root.attributes('-fullscreen', False)
        self.nom_joueur_local = StringVar()
        self.nom_joueur_local.set(nom_joueur_local)
        self.user = None

        # Centrer la fenêtre sur l'écran
        self.root.update_idletasks()
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        print(f"Ecran: {self.screen_width}x{self.screen_height}")
        self.largeur = 1600
        self.hauteur = 900
        x = (self.root.winfo_screenwidth() // 2) - (self.largeur // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.hauteur // 2)
        self.root.geometry(f"{self.largeur}x{self.hauteur}+{x}+{y}")
        self.root.minsize(1200, 600)

        ico_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src/" "images", "icon.ico")
        self.root.iconbitmap(ico_path)

        self.root.bind("<Double-Escape>", lambda e: self.root.destroy())
        self.root.bind("<F11>", lambda e: switch_fullscreen())

        # Interrupteur pour le mode plein écran avec les touches Échap et F11
        self.fullscreen = False
        def switch_fullscreen(event=None):
            self.fullscreen = not self.fullscreen
            self.root.attributes('-fullscreen', self.fullscreen)

        # attributs
        self.cadrechaton = 0
        self.textchat = ""
        self.infohud = {}
        # # minicarte
        self.tailleminicarte = 220
        self.cadreactif = None
        # # objet pour cumuler les manipulations du joueur pour generer une action de jeu
        self.action = Action(self)
        # cadre principal de l'application
        self.cadreapp = Frame(self.root, width=1000, height=800, bg="red")

        self.cadreapp.pack(expand=1, fill=BOTH)

        # # un dictionnaire pour conserver les divers cadres du jeu, creer plus bas
        self.cadres = {}
        self.creer_cadres()
        self.changer_cadre("login")

        # self.root.protocol("WM_DELETE_WINDOW", self.demanderabandon)
        # # sera charge apres l'initialisation de la partie, contient les donnees pour mettre l'interface a jour
        self.modele = None
        # # variable pour suivre le trace du multiselect
        self.debut_selection = []
        self.selecteuractif = None
        # # images des assets, definies dans le modue loadeurimages
        self.images = charger_images()
        self.gifs = charger_gifs()

    ####### INTERFACES GRAPHIQUES

    def changer_cadre(self, nomcadre: str):
        cadre = self.cadres[nomcadre]
        if self.cadreactif:
            self.cadreactif.pack_forget()
        self.cadreactif = cadre
        self.cadreactif.pack(expand=1, fill=BOTH)

    ###### LES CADRES ############################################################################################
    # Appel de la création des divers cadre
    def creer_cadres(self):
        self.cadres["mainlobby"] = self.creer_cadre_mainlobby()
        self.cadres["login"] = self.creer_cadre_login()
        self.cadres["jeu"] = self.creer_cadre_jeu()

    def creer_cadre_mainlobby(self) -> Frame:
        # === Cadre principal ===
        # Utiliser la largeur et hauteur de l'écran pour le cadre principal

        self.cadremain = Frame(self.cadreapp, bg="black", width=self.screen_width, height=self.screen_height)
        # NE PAS pack ici ! On pack seulement lors de changer_cadre
        self.cadremain.pack_propagate(False)

        # === Arrière-plan fixe ===
        bg_path = os.path.join(os.path.dirname(__file__), "images/lobby2.png")
        self.tk_bg = ImageTk.PhotoImage(Image.open(bg_path).resize((self.screen_width, self.screen_height), Image.Resampling.LANCZOS))
        self.label_bg = Label(self.cadremain, image=self.tk_bg)
        self.label_bg.place(x=0, y=0, relwidth=1, relheight=1)

        
        # === Paramètres du parallax === Comme dans tower defense
        self.vitesse_background = 15  # plus grand = mouvement plus lent
        self.background_zoom = 1.15   # image légèrement plus grande que l'écran pour que le mouvement ne révèle pas de bord noir
        self.pos_background_x = self.screen_width // 2
        self.pos_background_y = self.screen_height // 2

        # === Chargement des images ===
        bg_path = os.path.join(os.path.dirname(__file__), "images/lobby2.png")
        bg_img = Image.open(bg_path)
        splash_screen_size_x = int(self.screen_width * self.background_zoom)
        splash_screen_size_y = int(self.screen_height * self.background_zoom)
        self.original_bg = bg_img.resize((splash_screen_size_x, splash_screen_size_y), Image.Resampling.LANCZOS)

        # Création du Canvas principal
        self.background = Canvas(self.cadremain, width=self.screen_width, height=self.screen_height,
                     bd=0, highlightthickness=0, bg="black")
        self.background.pack(fill="both", expand=True)

        # Placement initial centré
        diffx = (splash_screen_size_x - self.screen_width) // 2
        diffy = (splash_screen_size_y - self.screen_height) // 2
        self.tk_bg = ImageTk.PhotoImage(self.original_bg)
        self.splash_screen = self.background.create_image(-diffx, -diffy, anchor="nw", image=self.tk_bg)
        self.background.image = self.tk_bg  # éviter le garbage collector

        # === Fonction de parallax (mouvement du fond selon la souris) ===
        def animate_background(event):
            # Décalage doux selon la position du curseur
            move_x = (event.x - self.screen_width // 2) / self.vitesse_background
            move_y = (event.y - self.screen_height // 2) / self.vitesse_background
            self.background.coords(self.splash_screen, -diffx + move_x, -diffy + move_y)

        self.background.bind("<Motion>", animate_background)

        # === MENU GAUCHE ===
        menu_frame = Frame(self.cadremain, bg="#3c2f2f")
        menu_frame.place(relx=0.05, rely=0.5, anchor="w")

        # === Colonne gauche (menu principal) ===
        menu_frame_size = int(self.screen_width // 4)
        menu_frame = Frame(self.cadremain, bg="#3c2f2f", width=menu_frame_size, height=self.screen_height , highlightthickness=2, highlightbackground="goldenrod2")
        menu_frame.pack_propagate(False)
        menu_frame.place(relx=0.03, rely=0.0, anchor="nw", relheight=1)

        def make_button(parent, text, image_path, font=("Times New Roman", 32, "bold"), command=None):
            # Cadre du "bouton"
            frame_width = int(self.screen_width // 5.12) 
            frame = Frame(parent, bg="#4a1d1d", width=frame_width, height=int(self.screen_height // 9.6) , highlightthickness=2, highlightbackground="goldenrod2")
            frame.pack_propagate(False)

            # Charger l'image
            img_path_full = os.path.join(os.path.dirname(__file__), image_path)
            img = Image.open(img_path_full).resize((frame_width, int(self.screen_height // 14.4)), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)

            # Créer widgets internes
            label_img = Label(frame, image=tk_img, bg="#4a1d1d")
            label_img.image = tk_img
            label_img.pack(side=TOP, pady=5)

            label_text = Label(frame, text=text, font=font, bg="#4a1d1d", fg="#D4AF37")
            label_text.pack(side=TOP, fill=BOTH, expand=True)

            # === Interaction (effet clic + hover) ===
            def on_enter(e):
                frame.config(bg="#7a3c3c")
                label_text.config(bg="#7a3c3c")
            def on_leave(e):
                frame.config(bg="#4a1d1d")
                label_text.config(bg="#4a1d1d")
            def on_click(e):
                if command:
                    command()

            # Bind des événements
            for widget in (frame, label_img, label_text):
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)

                # Switch des actions selon le texte du bouton
                actions = {
                    "Jouer": lambda: self.lancer_partie(),
                    "Tutoriel": lambda: print("Tutoriel cliqué"),
                    "Histoire": lambda: print("Histoire cliqué"),
                    "News": lambda: print("News cliqué"),
                    "Quitter": self.root.destroy,
                }
                
                widget.bind(
                    "<Button-1>",
                    lambda e, t=text: actions.get(t, lambda: print(f"{t} cliqué"))()
                )

            return frame
        

        logo_path = os.path.join(os.path.dirname(__file__), "images/logo.png")
        logo_img = Image.open(logo_path).resize((int(self.screen_width // 5.12), int(self.screen_height // 4.8)), Image.Resampling.LANCZOS)
        self.tk_logo = ImageTk.PhotoImage(logo_img)
        Label(menu_frame, image=self.tk_logo, bg="#3c2f2f").pack(pady=15)

        self.btn_jouer = make_button(menu_frame, "Jouer", image_path="images/login.jpg")
        self.btn_tutoriel = make_button(menu_frame, "Tutoriel", image_path="images/login.jpg")
        self.btn_histoire = make_button(menu_frame, "Histoire", image_path="images/login.jpg")
        self.btn_news = make_button(menu_frame, "News", image_path="images/login.jpg")
        self.btn_exit = make_button(menu_frame, "Quitter", image_path="images/login.jpg")


        # tout afficher
        for b in [self.btn_jouer, self.btn_tutoriel, self.btn_histoire, self.btn_news, self.btn_exit]:
            b.pack(pady=self.screen_width // 80)


        # === Version info (bas) ===
        Label(self.cadremain, text="Version 1.0.0", bg="#3c2f2f", fg="white", font=("Arial", 10, "italic")) \
            .pack(side=BOTTOM, pady=5)

        return self.cadremain
    

    # le login (ce qui 'login' à l'écran lors du démarrage)
    # sera le cadre visuel initial lors du lancement de l'application
    def creer_cadre_login(self):
        # === Cadre principal ===
        self.cadrelobby = Frame(self.cadreapp, bg="white", width=self.largeur, height=self.hauteur)
        self.cadrelobby.pack(fill=BOTH, expand=True)

        # === Deux sous-cadres (gauche = image / droite = login) ===
        self.frame_gauche = Frame(self.cadrelobby, bg="#cce6ff", width=500, height=800)
        self.frame_droite = Frame(self.cadrelobby, bg="white", width=500, height=800)

        self.frame_gauche.pack(side=LEFT, fill=BOTH, expand=True)
        self.frame_droite.pack(side=RIGHT, fill=BOTH, expand=True)

        # Fixe la taille minimale pour éviter le rétrécissement
        self.frame_gauche.pack_propagate(False)
        self.frame_droite.pack_propagate(False)
        self.cadrelobby.pack_propagate(False)

        # === Image (section gauche) ===
        # trouver le chemin de l'image
        img_path = os.path.join(os.path.dirname(__file__), "images/login.jpg")
        img = Image.open(img_path)
        self.original_img = img  # Conserver l'image originale pour le redimensionnement

        self.tk_image = ImageTk.PhotoImage(img)
        self.label_image = Label(self.frame_gauche, bg="#cce6ff", image=self.tk_image)
        self.label_image.place(relx=0, rely=0, relwidth=1, relheight=1)

        # changement adaptatif de la taille de l'image
        def resize_image(event):
            new_width = event.width
            new_height = event.height
            resized_img = self.original_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.tk_image = ImageTk.PhotoImage(resized_img)
            self.label_image.config(image=self.tk_image)
            self.label_image.image = self.tk_image  # enlever du garbage collector

        self.frame_gauche.bind("<Configure>", resize_image) # appelée à chaque redimensionnement

        # === Formulaire de connexion (section droite) ===
        self.cadre_login = Frame(self.frame_droite, bg="white")
        self.cadre_login.place(relx=0.5, rely=0.5, anchor=CENTER)

        # Widgets
        self.label_nom = Label(self.cadre_login, text="Nom d'utilisateur:", bg="white", font=("Arial", 12))
        self.entree_nom = Entry(self.cadre_login, font=("Arial", 12))
        self.label_mdp = Label(self.cadre_login, text="Mot de passe:", bg="white", font=("Arial", 12))
        self.entree_mdp = Entry(self.cadre_login, show="*", font=("Arial", 12))
        self.btn_enregistrer = Button(self.cadre_login, text="Enregistrer", font=("Arial", 12))
        self.btn_connexion = Button(self.cadre_login, text="Connexion", font=("Arial", 12))
        self.label_invite = Label(self.cadre_login, text="connectez-vous en tant qu'invité", bg="white", font=("Arial", 10, "italic"))

        # Placement dans une grille propre
        self.label_nom.grid(row=0, column=0, pady=(10, 0))
        self.entree_nom.grid(row=1, column=0, pady=5)
        self.label_mdp.grid(row=2, column=0)
        self.entree_mdp.grid(row=3, column=0, pady=5)
        self.btn_enregistrer.grid(row=4, column=0, pady=5)
        self.btn_connexion.grid(row=5, column=0, pady=5)
        self.label_invite.grid(row=6, column=0, pady=(10, 10))

        # === Bind des boutons (sans logique pour l’instant) ===
        self.btn_enregistrer.bind("<Button-1>", lambda e: self.enregistrer_et_changer())
        self.btn_connexion.bind("<Button-1>", lambda e: self.login_et_changer())
        self.label_invite.bind("<Button-1>", lambda e: (print("guest"), self.changer_cadre("mainlobby") , self.root.attributes('-fullscreen', True)))


        # on retourne ce cadre pour l'insérer dans le dictionnaires des cadres
        return self.cadrelobby

    def enregistrer(self, username,password):
        condition = self.parent.enregistrerUser(username, password)
        return condition

    def enregistrer_et_changer(self):
        if self.enregistrer(self.entree_nom.get(), self.entree_mdp.get()):
            self.nom_joueur_local.set(self.entree_nom.get())
            self.user = self.parent.user
            self.changer_cadre("mainlobby")
            self.root.attributes('-fullscreen', True)
        else:
            # Affiche ton message d'erreur (à adapter selon ton interface)
            messagebox.showerror("Erreur", "L'utilisateur existe déjà")

    def login(self, username,password):
        condition = self.parent.loginUser(username, password)
        return condition

    def login_et_changer(self):
        if self.login(self.entree_nom.get(), self.entree_mdp.get()):
            self.nom_joueur_local.set(self.entree_nom.get())
            self.user = self.parent.user
            self.changer_cadre("mainlobby")
            self.root.attributes('-fullscreen', True)
        else:
            # Affiche ton message d'erreur (à adapter selon ton interface)
            messagebox.showerror("Erreur", "L'utilisateur n'existe pas ou erreur de saisi du mot de passe.")


    def creer_cadre_jeu(self):
        # le cadre principal du jeu, remplace le Lobby
        self.cadrepartie = Frame(self.cadreapp, bg="green", width=400, height=400)
        # cadre du jeu et ses scrollbars
        self.creer_aire_de_jeu()
        # cadre pour info sur les ressources du joueur en haut de l'aire de jeu
        self.creer_HUD()
        # cadre pour commandes et infos des objets de jeu, situe a droite
        self.creer_cadre_jeu_action()
        # configuration de la section qui s'etire lorsque la fenetre change de taille
        self.cadrepartie.rowconfigure(0, weight=1)
        self.cadrepartie.columnconfigure(0, weight=1)
        # on retourne ce cadre pour l'insérer dans le dictionnaires des cadres
        return self.cadrepartie

    def creer_aire_de_jeu(self):
        # definition du cadre avec le canvas de jeu et les scrollbars
        self.cadrecanevas = Frame(self.cadrepartie)
        # on crée les scrollbar AVANT le canevas de jeu car le canevas est dépendant de leur
        self.scrollV = Scrollbar(self.cadrecanevas, orient=VERTICAL)
        self.scrollH = Scrollbar(self.cadrecanevas, orient=HORIZONTAL)
        self.canevas = Canvas(self.cadrecanevas, width=400, height=400, bg="DarkOliveGreen2",
                              yscrollcommand=self.scrollV.set,
                              xscrollcommand=self.scrollH.set)
        self.scrollV.config(command=self.canevas.yview)
        self.scrollH.config(command=self.canevas.xview)
        # on visualise utilisant grid (grille)
        # le grid avec 'sticky' indique que l'objet doit s'acroitre pour coller aux 'points cardinaux' (anglais)

        self.canevas.grid(row=1, column=0, sticky=N + S + E + W)
        self.scrollV.grid(row=1, column=1, sticky=N + S)
        self.scrollH.grid(row=2, column=0, sticky=E + W)

        # visualise le cadre qui contient le canevas de jeu
        self.cadrecanevas.grid(column=0, row=0, sticky=N + S + E + W)
        # on doit preciser quelle partie de la grille (grid) va s'accroitre, colonne et rangée
        # ici on precise que c'est le canevas et non les scrollbar qui doit s'agrandir
        self.cadrecanevas.rowconfigure(1, weight=1)
        self.cadrecanevas.columnconfigure(0, weight=1)
        self.connecter_event()

    def creer_HUD(self):
        self.cadrejeuinfo = Frame(self.cadrecanevas, bg="blue")
        # des etiquettes d'info
        self.infohud = {"Nourriture": None,
                        "Bois": None,
                        "Roche": None,
                        "Aureus": None}

        # fonction interne uniquement pour reproduire chaque item d'info
        def creer_champ_interne(listechamp):
            titre = Champ(self.cadrejeuinfo, text=i, bg="red", fg="white")
            varstr = StringVar()
            varstr.set(0)
            donnee = Champ(self.cadrejeuinfo, bg="red", fg="white", textvariable=varstr)
            titre.pack(side=LEFT)
            donnee.pack(side=LEFT)
            self.infohud[i] = [varstr, donnee]

        for i in self.infohud.keys():
            creer_champ_interne(i)

        varstr = StringVar()
        varstr.set("")

        champmsg = Label(self.cadrejeuinfo, text="", fg="red")
        champmsg.pack(side=LEFT)
        self.infohud["msggeneral"] = [champmsg]
        self.btnchat = Button(self.cadrejeuinfo, text="Chat", command=self.sauvegarder)
        self.btnaide = Button(self.cadrejeuinfo, text="Aide", command=self.action.aider)


        self.btnaide.pack(side=RIGHT)
        self.btnchat.pack(side=RIGHT)
        self.cadrejeuinfo.grid(row=0, column=0, sticky=E + W, columnspan=2)

    def sauvegarder(self):
        self.parent.sauvegarde()


    def creer_cadre_jeu_action(self):
        # Ajout du cadre d'action a droite pour identifier les objets permettant les commandes du joueur
        self.cadreaction = Frame(self.cadrepartie)
        self.cadreaction.grid(row=0, column=1, sticky=N + S)
        self.scrollVaction = Scrollbar(self.cadreaction, orient=VERTICAL)
        self.canevasaction = Canvas(self.cadreaction, width=200, height=300, bg="lightblue",
                                    yscrollcommand=self.scrollVaction.set)

        self.scrollVaction.config(command=self.canevasaction.yview)
        self.canevasaction.grid(row=0, column=0, sticky=N + S)
        self.scrollVaction.grid(row=0, column=1, sticky=N + S)
        # les widgets
        self.canevasaction.create_text(100, 30, text=self.parent.nom_joueur_local, font=("arial", 18, "bold"), anchor=S,
                                       tags=("nom"))

        # minicarte
        self.minicarte = Canvas(self.cadreaction, width=self.tailleminicarte, height=self.tailleminicarte, bg="tan1",
                                highlightthickness=0)
        self.minicarte.grid(row=2, column=0, columnspan=2)
        self.minicarte.bind("<Button-1>", self.deplacer_carte)

        # on retourne ce cadre pour l'insérer dans le dictionnaires des cadres
        self.canevasaction.rowconfigure(0, weight=1)
        self.cadreaction.rowconfigure(0, weight=1)

    def creer_aide(self):
        self.cadreaide = Frame(self.canevas)
        self.scrollVaide = Scrollbar(self.cadreaide, orient=VERTICAL)
        self.textaide = Text(self.cadreaide, width=50, height=10,
                             yscrollcommand=self.scrollVaide.set)
        self.scrollVaide.config(command=self.textaide.yview)
        self.textaide.pack(side=LEFT)
        self.scrollVaide.pack(side=LEFT, expand=1, fill=Y)
        #fichieraide = open("aide.txt")
        #monaide = fichieraide.read()
        #fichieraide.close()
        fichieraide = open(os.path.join(os.path.dirname(__file__), "aide.txt"), "r", encoding="utf-8")
        monaide = fichieraide.read()
        fichieraide.close()
        self.textaide.insert(END, monaide)
        self.textaide.config(state=DISABLED)

    def creer_chatter(self):
        self.cadrechat = Frame(self.canevas, bd=2, bg="orange")
        self.cadrechatlist = Frame(self.cadrechat)
        # Make topLevelWindow remain on top until destroyed, or attribute changes.
        self.scrollVchat = Scrollbar(self.cadrechatlist, orient=VERTICAL)
        self.textchat = Listbox(self.cadrechatlist, width=30, height=6,
                                yscrollcommand=self.scrollVchat.set)
        self.scrollVchat.config(command=self.textchat.yview)
        self.textchat.pack(side=LEFT)
        self.scrollVchat.pack(side=LEFT, expand=1, fill=Y)
        self.textchat.delete(0, END)
        self.cadrechatlist.pack()
        # inscrire texte et choisir destinataire
        self.cadreparler = Frame(self.cadrechat, bd=2)
        self.joueurs = ttk.Combobox(self.cadreparler,
                                    values=list(self.modele.joueurs.keys()))
        self.entreechat = Entry(self.cadreparler, width=20)
        self.entreechat.bind("<Return>")  # ,self.action.envoyerchat)
        self.joueurs.pack(expand=1, fill=X)
        self.entreechat.pack(expand=1, fill=X)
        self.cadreparler.pack(expand=1, fill=X)

    def connecter_event(self):
        # on attache (bind) desF événements soit aux objets eux même
        self.canevas.bind("<Button-1>", self.annuler_action)
        self.canevas.bind("<Button-3>", self.construire_batiment)
        # faire une multiselection
        self.canevas.bind("<Shift-Button-1>", self.debuter_selection)
        self.canevas.bind("<Shift-B1-Motion>", self.afficher_selection)
        self.canevas.bind("<Shift-ButtonRelease-1>", self.terminer_selection)

        self.canevas.bind("<Button-2>", self.indiquer_position)

        self.canevas.bind("<MouseWheel>", self.OnMouseWheel)
        self.canevas.bind("<Control-MouseWheel>", self.OnCtrlMouseWheel)
        self.canevas.bind("<ButtonPress-1>", self.start_drag)
        self.canevas.bind("<B1-Motion>", self.do_drag)
        
        # soit aux dessins, en vertu de leur tag (propriétés des objets dessinés)
        # ALL va réagir à n'importe quel dessin
        # sinon on spécifie un tag particulier, exemple avec divers tag, attaché par divers événements
        self.canevas.tag_bind("batiment", "<Button-1>", self.creer_entite)
        self.canevas.tag_bind("perso", "<Button-1>", self.ajouter_selection)
        self.canevas.tag_bind("arbre", "<Button-1>", self.ramasser_ressource)
        self.canevas.tag_bind("aureus", "<Button-1>", self.ramasser_ressource)
        self.canevas.tag_bind("roche", "<Button-1>", self.ramasser_ressource)
        self.canevas.tag_bind("baie", "<Button-1>", self.ramasser_ressource)
        self.canevas.tag_bind("eau", "<Button-1>", self.ramasser_ressource)
        self.canevas.tag_bind("daim", "<Button-1>", self.chasser_ressource)

    def OnMouseWheel(self, evt):
        print(evt.keysym)
        rep = self.scrollV.get()[0]
        if evt.delta < 0:
            rep = rep + 0.02
        else:
            rep = rep - 0.02
        self.canevas.yview_moveto(rep)

    def OnCtrlMouseWheel(self, evt):
        print("IN X")
        rep = self.scrollH.get()[0]
        if evt.delta < 0:
            rep = rep + 0.02
        else:
            rep = rep - 0.02
        self.canevas.xview_moveto(rep)

    def start_drag(self, event):
        self.canevas.scan_mark(event.x, event.y)

    def do_drag(self, event):
        self.canevas.scan_dragto(event.x, event.y, gain=1)

        # cette méthode sert à changer le cadre (Frame) actif de la fenêtre, on n'a qu'à fournir le cadre requis

    ##### FONCTION DU SPLASH #########################################################################
    def creer_partie(self):
        nom = self.nomsplash.get()
        ## ON VA LIRE LA VALEUR DE LA VARIABLE ASSOCIEE AU BTN RADION CHOISI
        # MORT urljeu = self.url_initial.get()
        self.parent.creer_partie(nom) #, urljeu)  # ,valciv)

    # ###  METHODES POUR SPLASH ET LOBBY INSCRIPTION pour participer a une partie
    # def update_splash(self, etat):
    #     if "attente" in etat or "courante" in etat:
    #         self.btncreerpartie.config(state=DISABLED)
    #     if "courante" in etat:
    #         self.etatdujeu.config(text="Desole - partie encours !")
    #         self.btninscrirejoueur.config(state=DISABLED)
    #     elif "attente" in etat:
    #         self.etatdujeu.config(text="Partie en attente de joueurs !")
    #         self.btninscrirejoueur.config(state=NORMAL)
    #     elif "dispo" in etat:
    #         self.etatdujeu.config(text="Bienvenue ! Serveur disponible")
    #         self.btninscrirejoueur.config(state=DISABLED)
    #         self.btncreerpartie.config(state=NORMAL)
    #     else:
    #         self.etatdujeu.config(text="ERREUR - un probleme est survenu")

    # ##### FONCTION DU LOBBY #############
    # def update_lobby(self, dico):
    #     self.listelobby.delete(0, END)
    #     for i in dico:
    #         self.listelobby.insert(END, i[0])
    #     if self.parent.ego_serveur:
    #         self.btnlancerpartie.config(state=NORMAL)

    # def inscrire_joueur(self):
    #     nom = self.nomsplash.get()
    #     urljeu = self.url_initial.get()
    #     self.parent.inscrire_joueur(nom, urljeu)

    def lancer_partie(self):
        self.parent.lancer_partie()


    # def reset_partie(self):
    #     rep = self.parent.reset_partie()

    def initialiser_avec_modele(self):
        # on reassigne le nom final localement pour eviter
        # de toujours le requerir du parent
        self.nom_joueur_local = self.parent.nom_joueur_local
        # on ajuste la taille du canevas de jeu
        self.canevas.config(scrollregion=(0, 0, self.modele.aireX, self.modele.aireY))
        self.canevasaction.delete("nom")
        self.canevasaction.create_text(100, 30, text=self.nom_joueur_local, font=("arial", 18, "bold"), anchor=S, tags=("nom"))

        # on cree les cadres affichant les items d'actions du joueur
        # cadre apparaissant si on selectionne un ouvrier
        coul = self.modele.joueurs[self.parent.nom_joueur_local].couleur
        self.cadrejeuinfo.config(bg=coul[1])
        self.creer_aide()
        self.creer_cadre_ouvrier(coul[0] + "_", ["maison", "caserne", "abri", "usineballiste"])
        self.creer_chatter()
        # on affiche les maisons, point de depart des divers joueurs
        self.afficher_depart()
        self.root.update()
        # self.centrer_maison()

    def creer_cadre_ouvrier(self, coul, artefacts):
        self.cadreouvrier = Frame(self.canevasaction)
        for i in artefacts:
            btn = Button(self.cadreouvrier, text=i, image=self.images[coul + i])
            btn.bind("<Button>", self.batir_artefact)
            btn.pack()

    ##FONCTIONS D'AFFICHAGES##################################
    def afficher_depart(self):
        self.modele.listebiotopes.sort(key=lambda c: c.y)
        for i in self.modele.listebiotopes:
            if i.montype == "daim":
                monitem = self.canevas.create_image(i.x, i.y, image=self.images[i.img], anchor=S,
                                                    tags=("mobile", "", i.id, "biotope", i.montype, ""))
                # tags=("mobile","",i.id,)
            else:
                monitem = self.canevas.create_image(i.x, i.y, image=self.images[i.img], anchor=S,
                                                    tags=("statique", "", i.id, "biotope", i.montype, ""))
                # tags=("mobile","",i.id,)

        self.modele.listebiotopes = []
        minitaillecase = int(self.tailleminicarte / self.modele.taillecarte)
        couleurs = {0: "",
                    "arbre": "light green",
                    "eau": "light blue",
                    "aureus": "tan",
                    "roche": "gray30",
                    "marais": "orange"}
        for i, t in enumerate(self.modele.regions):
            if t != "plaine":
                for j, c in enumerate(self.modele.regions[t]):
                    for cle, k in self.modele.regions[t][c].dicocases.items():
                        y1 = k.y * minitaillecase
                        y2 = y1 + minitaillecase
                        x1 = k.x * minitaillecase
                        x2 = x1 + minitaillecase
                        self.minicarte.create_rectangle(x1, y1, x2, y2, outline="",
                                                        # fill=couleurs[self.modele.cartecase[k[1]][k[0]].type]),
                                                        fill=couleurs[k.parent.montype])

        # Affichage des batiments intiaux sur l'aire de jeu et sur la minicarte
        px = int(self.tailleminicarte / self.modele.aireX)
        py = int(self.tailleminicarte / self.modele.aireY)

        for j in self.modele.joueurs.keys():
            for i in self.modele.joueurs[j].batiments["maison"].keys():
                m = self.modele.joueurs[j].batiments["maison"][i]
                coul = self.modele.joueurs[j].couleur[0]
                self.canevas.create_image(m.x, m.y, image=self.images[coul + "_maison"],
                                          tags=("statique", j, m.id, "batiment", m.montype, ""))
                # tags=("mobile","",i.id,)
                # afficher sur minicarte
                coul = self.modele.joueurs[j].couleur[1]
                x1 = int((m.x / self.modele.aireX) * self.tailleminicarte)
                y1 = int((m.y / self.modele.aireY) * self.tailleminicarte)
                self.minicarte.create_rectangle(x1 - 2, y1 - 2, x1 + 2, y1 + 2, fill=coul,
                                                tags=(j, m.id, "artefact", "maison"))

    def afficher_bio(self, bio):
        self.canevas.create_image(bio.x, bio.y, image=self.images[bio.img],
                                  tags=("statique", "", bio.id, "biotope", bio.montype, ""))

    def afficher_batiment(self, joueur, batiment):
        coul = self.modele.joueurs[joueur].couleur[0]

        self.canevas.delete(batiment.id)

        print(self.parent.nom_joueur_local)
        chose = self.canevas.create_image(batiment.x, batiment.y, image=self.images[batiment.image],
                                          tags=(
                                          "statique", self.parent.nom_joueur_local, batiment.id, "batiment", batiment.montype,
                                          ""))

        x0, y0, x2, y2 = self.canevas.bbox(chose)

        couleurs = {0: "",
                    1: "light green",
                    2: "light blue",
                    3: "tan",
                    4: "gray30",
                    5: "orange"}
        coul = self.modele.joueurs[joueur].couleur[1]
        x1 = int((batiment.x / self.modele.aireX) * self.tailleminicarte)
        y1 = int((batiment.y / self.modele.aireY) * self.tailleminicarte)
        self.minicarte.create_rectangle(x1 - 2, y1 - 2, x1 + 2, y1 + 2, fill=coul,
                                        tags=(self.parent.nom_joueur_local, batiment.id, "artefact", batiment.montype))
        return [x0, y0, x2, y2]

    def afficher_jeu(self):

        # On efface tout ce qui est 'mobile' (un tag)
        self.canevas.delete("mobile")

        # on se debarrasse des choses mortes (disparues), le id est dans le tag du dessin
        for i in self.modele.ressourcemorte:
            self.canevas.delete(i.id)

        # commencer par les choses des joueurs
        for j in self.modele.joueurs.keys():
            # ajuster les infos du HUD
            if j == self.parent.nom_joueur_local:
                self.infohud["Nourriture"][0].set(self.modele.joueurs[j].ressources["nourriture"])
                self.infohud["Bois"][0].set(self.modele.joueurs[j].ressources["arbre"])
                self.infohud["Roche"][0].set(self.modele.joueurs[j].ressources["roche"])
                self.infohud["Aureus"][0].set(self.modele.joueurs[j].ressources["aureus"])
                self.infohud["msggeneral"][0].config(text=self.modele.msggeneral)

            # ajuster les constructions de chaque joueur
            for p in self.modele.joueurs[j].batiments['siteconstruction']:
                s = self.modele.joueurs[j].batiments['siteconstruction'][p]
                if s.etat == "attente":
                    self.canevas.create_image(s.x, s.y, anchor=CENTER, image=self.images["siteX"],
                                              tags=("mobile", j, p, "batiment", type(s).__name__, ""))
                    # tags=(j,s.id,"artefact","mobile","siteconstruction","batiments"))
                else:
                    self.canevas.create_image(s.x, s.y, anchor=CENTER, image=self.images["EnConstruction"],
                                              tags=("mobile", j, p, "batiment", type(s).__name__, ""))

            # ajuster les persos de chaque joueur et leur dépendance (ici javelots des ouvriers)
            for p in self.modele.joueurs[j].persos.keys():
                for k in self.modele.joueurs[j].persos[p].keys():
                    i = self.modele.joueurs[j].persos[p][k]
                    coul = self.modele.joueurs[j].couleur[0]
                    self.canevas.create_image(i.x, i.y, anchor=S, image=self.images[i.image],
                                              tags=("mobile", j, k, "perso", type(i).__name__, ""))
                    # tags=(j,k,"artefact","mobile","perso",p))
                    if k in self.action.persochoisi:
                        self.canevas.create_rectangle(i.x - 10, i.y + 5, i.x + 10, i.y + 10, fill="yellow",
                                                      tags=("mobile", j, p, "perso", type(i).__name__, "persochoisi"))
                        # tags=(j,k,"artefact","mobile","persochoisi"))

                    # dessiner javelot de l'ouvrier
                    if p == "ouvrier":
                        for b in self.modele.joueurs[j].persos[p][k].javelots:
                            self.canevas.create_image(b.x, b.y, image=self.images[b.image],
                                                      tags=("mobile", j, b.id, "", type(b).__name__, ""))
                            # tags=(j,b.id,"artefact","mobile","javelot"))

        # ajuster les choses vivantes dependantes de la partie (mais pas des joueurs)
        for j in self.modele.biotopes["daim"].keys():
            i = self.modele.biotopes["daim"][j]
            if i.etat == "mort":
                self.canevas.create_image(i.x, i.y, image=self.images["daimMORT"],
                                          tags=("mobile", "", i.id, "biotope", i.montype, ""))
                # tags=("",i.id,"artefact","daim","mobile"))

            else:
                self.canevas.create_image(i.x, i.y, image=self.images[i.img],
                                          tags=("mobile", "", i.id, "biotope", i.montype, ""))
                # tags=("",i.id,"artefact","daim","mobile"))

        # ajuster les choses vivantes dependantes de la partie (mais pas des joueurs)
        for j in self.modele.biotopes["eau"].keys():
            i = self.modele.biotopes["eau"][j]
            if i.sprite:
                self.canevas.create_image(i.x, i.y, image=self.gifs[i.sprite][i.spriteno],
                                          tags=("mobile", "", i.id, "biotope", type(i).__name__, ""))
                # tags=("",i.id,"artefact","eau","mobile"))

        # mettre les chat a jour si de nouveaux messages sont arrives
        if self.textchat and self.modele.joueurs[self.parent.nom_joueur_local].chatneuf:
            self.textchat.delete(0, END)
            self.textchat.insert(END, *self.modele.joueurs[self.parent.nom_joueur_local].monchat)
            if self.modele.joueurs[self.parent.nom_joueur_local].chatneuf and self.action.chaton == 0:
                self.btnchat.config(bg="orange")
            self.modele.joueurs[self.parent.nom_joueur_local].chatneuf = 0

    def centrer_maison(self):
        self.root.update()
        cle = list(self.modele.joueurs[self.nom_joueur_local].batiments["maison"].keys())[0]
        x = self.modele.joueurs[self.nom_joueur_local].batiments["maison"][cle].x
        y = self.modele.joueurs[self.nom_joueur_local].batiments["maison"][cle].y

        x1 = self.canevas.winfo_width() / 2
        y1 = self.canevas.winfo_height() / 2

        pctx = (x - x1) / self.modele.aireX
        pcty = (y - y1) / self.modele.aireY

        self.canevas.xview_moveto(pctx)
        self.canevas.yview_moveto(pcty)

    ##### ACTIONS DU JOUEUR #######################################################################

    def annuler_action(self, evt):
        mestags = self.canevas.gettags(CURRENT)
        if not mestags:
            self.canevasaction.delete(self.action.widgetsactifs)
            if self.action.btnactif:
                self.action.btnactif.config(bg="SystemButtonFace")
            self.action = Action(self)

    def fermer_chat(self):
        self.textchat = None
        self.fenchat.destroy()

    def ajouter_selection(self, evt):
        mestags = self.canevas.gettags(CURRENT)
        if self.parent.nom_joueur_local == mestags[1]:
            if "Ouvrier" == mestags[4]:
                self.action.persochoisi.append(mestags[2])
                self.action.afficher_commande_perso()
            else:
                self.action.persochoisi.append(mestags[2])
        elif self.action.persochoisi != []:
            self.action.ciblechoisi = mestags
            self.action.attaquer()

    # Methodes pour multiselect
    def debuter_selection(self, evt):
        self.debutselect = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
        x1, y1 = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
        self.selecteuractif = self.canevas.create_rectangle(x1, y1, x1 + 1, y1 + 1, outline="red", width=2,
                                                            dash=(2, 2), tags=("", "selecteur", "", "artefact"))

    def afficher_selection(self, evt):
        if self.debutselect:
            x1, y1 = self.debutselect
            x2, y2 = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
            self.canevas.coords(self.selecteuractif, x1, y1, x2, y2)

    def terminer_selection(self, evt):
        if self.debutselect:
            x1, y1 = self.debutselect
            x2, y2 = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
            self.debutselect = []
            objchoisi = (list(self.canevas.find_enclosed(x1, y1, x2, y2)))
            for i in objchoisi:
                if self.parent.nom_joueur_local not in self.canevas.gettags(i):
                    objchoisi.remove(i)
                else:
                    self.action.persochoisi.append(self.canevas.gettags(i)[2])

            if self.action.persochoisi:
                self.action.afficher_commande_perso()
            self.canevas.delete("selecteur")

    ### FIN du multiselect

    def ramasser_ressource(self, evt):
        tag = self.canevas.gettags(CURRENT)
        if tag[1] == "" and self.action.persochoisi:
            self.action.ramasser_ressource(tag)
        else:
            print(tag[4])

    def chasser_ressource(self, evt):
        tag = self.canevas.gettags(CURRENT)
        if tag[1] == "" and self.action.persochoisi and tag[4] == "daim":
            self.action.chasser_ressource(tag)
        else:
            print(tag[3])

    def indiquer_position(self, evt):
        tag = self.canevas.gettags(CURRENT)
        if not tag:
            x, y = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
            self.action.position = [x, y]
            self.action.deplacer()

    # Cette fonction permet se se deplacer via un click sur la minicarte
    def deplacer_carte(self, evt):
        x = evt.x
        y = evt.y



        pctx = x / self.tailleminicarte
        pcty = y / self.tailleminicarte

        xl = (self.canevas.winfo_width() / 2) / self.modele.aireX
        yl = (self.canevas.winfo_height() / 2) / self.modele.aireY

        self.canevas.xview_moveto(pctx - xl)
        self.canevas.yview_moveto(pcty - yl)
        xl = self.canevas.winfo_width()
        yl = self.canevas.winfo_height()


    def batir_artefact(self, evt):
        obj = evt.widget
        if self.action.btnactif:
            if self.action.btnactif != obj:
                self.action.btnactif.config(bg="SystemButtonFace")
        # test de cout a cet endroit
        nomsorte = obj.cget("text")
        self.action.btnactif = obj

        vals = self.parent.trouver_valeurs()
        print(vals)
        ok = 1
        for k, val in self.modele.joueurs[self.nom_joueur_local].ressources.items():
            if val <= vals[nomsorte][k]:
                ok = 0
                break
        if ok:
            self.action.prochaineaction = obj.cget("text")
            obj.config(bg="lightgreen")
        else:
            print("VOUS N'AVEZ PAS ASSEZ DE", k)

    def construire_batiment(self, evt):
        mestags = self.canevas.gettags(CURRENT)
        if not mestags:
            pos = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
            self.action.construire_batiment(pos)

    def creer_entite(self, evt):
        x, y = evt.x, evt.y
        mestags = self.canevas.gettags(CURRENT)
        if self.parent.nom_joueur_local in mestags:
            if "batiment" in mestags:
                if "maison" in mestags:
                    pos = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
                    action = [self.parent.nom_joueur_local, "creerperso", ["ouvrier", mestags[4], mestags[2], pos]]
                if "caserne" in mestags:
                    pos = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
                    action = [self.parent.nom_joueur_local, "creerperso", ["soldat", mestags[4], mestags[2], pos]]
                if "abri" in mestags:
                    pos = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
                    action = [self.parent.nom_joueur_local, "creerperso", ["druide", mestags[4], mestags[2], pos]]
                if "usineballiste" in mestags:
                    pos = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
                    action = [self.parent.nom_joueur_local, "creerperso", ["ballista", mestags[4], mestags[2], pos]]
                self.parent.actions_requises.append(action)
        elif self.action.persochoisi != []:
            self.action.ciblechoisi = mestags
            self.action.attaquer()


# Singleton (mais pas automatique) sert a conserver les manipulations du joueur
# pour demander une action
class Action():
    def __init__(self, parent):
        self.parent = parent
        self.persochoisi = []
        self.ciblechoisi = None
        self.position = []
        self.btnactif = None
        self.prochaineaction = None
        self.widgetsactifs = []
        self.chaton = 0
        self.aideon = 0

    def attaquer(self):
        if self.persochoisi:
            qui = self.ciblechoisi[1]
            cible = self.ciblechoisi[2]
            sorte = self.ciblechoisi[5]
            action = [self.parent.parent.nom_joueur_local, "attaquer", [self.persochoisi, [qui, cible, sorte]]]
            self.parent.parent.actions_requises.append(action)

    def deplacer(self):
        if self.persochoisi:
            action = [self.parent.parent.nom_joueur_local, "deplacer", [self.position, self.persochoisi]]
            self.parent.parent.actions_requises.append(action)

    def chasser_ressource(self, tag):
        if self.persochoisi:
            action = [self.parent.parent.nom_joueur_local, "chasserressource", [tag[4], tag[2], self.persochoisi]]
            self.parent.parent.actions_requises.append(action)

    def ramasser_ressource(self, tag):
        if self.persochoisi:
            action = [self.parent.parent.nom_joueur_local, "ramasserressource", [tag[4], tag[2], self.persochoisi]]
            self.parent.parent.actions_requises.append(action)

    def construire_batiment(self, pos):
        self.btnactif.config(bg="SystemButtonFace")
        self.btnactif = None
        action = [self.parent.nom_joueur_local, "construirebatiment", [self.persochoisi, self.prochaineaction, pos]]
        self.parent.parent.actions_requises.append(action)

    def afficher_commande_perso(self):
        self.widgetsactifs = self.parent.canevasaction.create_window(100, 60,
                                                                     window=self.parent.cadreouvrier,
                                                                     anchor=N)
        self.parent.root.update()
        fh = self.parent.cadreouvrier.winfo_height()
        ch = int(self.parent.canevasaction.cget("height"))
        if fh + 60 > ch:
            cl = int(self.parent.canevasaction.cget("width"))
            self.parent.canevasaction.config(scrollregion=(0, 0, cl, fh + 60))

    def envoyer_chat(self, evt):
        txt = self.parent.entreechat.get()
        joueur = self.parent.joueurs.get()
        if joueur:
            action = [self.parent.nom_joueur_local, "chatter", [self.parent.nom_joueur_local + ": " + txt, self.parent.nom_joueur_local, joueur]]
            self.parent.parent.actions_requises.append(action)

    def chatter(self):
        if self.chaton == 0:
            x1, x2 = self.parent.scrollH.get()
            x3 = self.parent.modele.aireX * x1
            y1, y2 = self.parent.scrollV.get()
            y3 = self.parent.modele.aireY * y1
            self.parent.cadrechaton = self.parent.canevas.create_window(x3, y3,
                                                                        window=self.parent.cadrechat,
                                                                        anchor=N + W)
            self.parent.btnchat.config(bg="SystemButtonFace")
            self.chaton = 1
        else:
            self.parent.canevas.delete(self.parent.cadrechaton)
            self.parent.cadrechaton = 0
            self.chaton = 0

    def aider(self):
        if self.aideon == 0:
            x1, x2 = self.parent.scrollH.get()
            x3 = self.parent.modele.aireX * x2
            y1, y2 = self.parent.scrollV.get()
            y3 = self.parent.modele.aireY * y1
            self.aideon = self.parent.canevas.create_window(x3, y3,
                                                            window=self.parent.cadreaide,
                                                            anchor=N + E)
        else:
            self.parent.canevas.delete(self.aideon)
            self.aideon = 0

    ### FIN des methodes pour lancer la partie

# classe qui est une sous-classe d'une classe tkinter dont on change les proprietes
class Champ(Label):
    def __init__(self, master, *args, **kwargs):
        Label.__init__(self, master, *args, **kwargs)
        self.config(font=("arial", 13, "bold"))
        self.config(bg="goldenrod3")

# a enlever test only
if __name__ == '__main__':
    print("Bienvenue au RTS")
    c = m.Controleur()
    # print("FIN DE PROGRAMME")
