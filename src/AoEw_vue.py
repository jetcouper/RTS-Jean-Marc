from tkinter import *
from tkinter import ttk, messagebox
from tkinter.simpledialog import *
import os
from chargeurdimages import *
import AoEw_client_main as m # a enlever test only
import ctypes
from datetime import datetime
from vue.fog import FogOverlay, FogState
from vue.minimap import MiniMapRenderer

from PIL import Image, ImageTk  # Pour redimensionner l’image

#Commentaire de push
class Vue():
    def __init__(self, parent, nom_joueur_local): #, testdispo):
        self.parent = parent
        self.root = Tk()
        self.root.title("Age of Empire")
        self.root.attributes('-fullscreen', False)
        self.nom_joueur_local = StringVar()
        self.nom_joueur_local.set(nom_joueur_local)
        self.user = None
        self.fog_overlay: FogOverlay
        self.minimap_renderer: MiniMapRenderer

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

        self.root.bind_all("<q>", lambda e: self.root.destroy())
        self.root.bind_all("<Q>", lambda e: self.root.destroy())

        self.root.bind_all("<F11>", lambda e: switch_fullscreen())  

        def deselectionner_tout(event=None):
            # Désélectionner uniquement quand on est dans le jeu
            if hasattr(self, 'action') and hasattr(self, 'canevasaction'):
                if self.action.widgetsactifs:
                    if isinstance(self.action.widgetsactifs, list):
                        for widget_id in self.action.widgetsactifs:
                            self.canevasaction.delete(widget_id)
                    else:
                        self.canevasaction.delete(self.action.widgetsactifs)

                if self.action.btnactif:
                    self.action.btnactif.config(bg="SystemButtonFace")
                self.action = Action(self)
                print("élection annulée")
        def toggle_escape(event=None):
            if self.toplevelactif:
                self.reprendre_partie()
                self.changer_toplevel(None)
                self.changer_topblack(None)
            else:
                # choix du toplevel en fonction du cadre actif
                nom_cadre_actif = None
                for nom, cadre in self.cadres.items():
                    if cadre is self.cadreactif:
                        nom_cadre_actif = nom
                        break

                if nom_cadre_actif == "jeu":
                    self.mettre_en_pause_partie()
                    self.changer_topblack("blackgame")
                    self.changer_toplevel("gameescape")
                elif nom_cadre_actif == ("gamemenu"):
                    self.changer_topblack("blackgame")
                    self.changer_toplevel("option")               


        # bind sur tous les widgets (fonctionne même quand le toplevel a le focus)
        self.root.bind_all("<Escape>", toggle_escape)
        self.root.bind_all("<d>", deselectionner_tout)
        self.root.bind_all("<D>", deselectionner_tout)
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
        self.tailleminicarte = 200
        self.cadreactif = None
        self.toplevelactif = None
        self.topblackactif = None

        # # objet pour cumuler les manipulations du joueur pour generer une action de jeu
        self.action = Action(self)
        # cadre principal de l'application
        self.cadreapp = Frame(self.root, width=1000, height=800, bg="red")

        self.cadreapp.pack(expand=1, fill=BOTH)

        # # un dictionnaire pour conserver les divers cadres du jeu, creer plus bas
        self.cadres = {}
        self.toplevel = {}
        self.topblack = {}

        self.creer_cadres()
        self.creer_toplevel()

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
        self._ajouter_sprite_mort()

    def _ajouter_sprite_mort(self):
        if "mort" in self.images:
            return
        sprite = PhotoImage(width=24, height=24)
        sprite.put("#2b1b1b", to=(0, 0, 23, 23))
        for i in range(24):
            sprite.put("#8b0000", to=(i, i))
            sprite.put("#8b0000", to=(23 - i, i))
        self.images["mort"] = sprite


    ####### INTERFACES GRAPHIQUES

    def changer_cadre(self, nomcadre: str):
        cadre = self.cadres[nomcadre]
        if self.cadreactif:
            self.cadreactif.pack_forget()
        self.cadreactif = cadre
        self.cadreactif.pack(expand=1, fill=BOTH)

    def changer_toplevel(self, nomcadre: str):
        # suprrime le toplevel si 
        if nomcadre is None:
            if self.toplevelactif:
                self.toplevelactif.withdraw()
                self.toplevelactif = None
                return

        toplevel = self.toplevel.get(nomcadre)
        if not toplevel:
            return

        if self.toplevelactif and self.toplevelactif is not toplevel:
            self.toplevelactif.withdraw()

        self.toplevelactif = toplevel
        self.toplevelactif.overrideredirect(True)  # enlever bar du haut

        self.toplevelactif.deiconify()
        self.toplevelactif.update_idletasks()

        self.toplevelactif.transient(self.root)
        self.toplevelactif.lift()
        self.toplevelactif.focus_force()

    def changer_topblack(self, nomcadre: str):
        # suprrime le toplevel si 
        if nomcadre is None:
            if self.topblackactif:
                self.topblackactif.withdraw()
                self.topblackactif = None
                return

        toplevel = self.topblack.get(nomcadre)
        if not toplevel:
            return

        if self.topblackactif and self.topblackactif is not toplevel:
            self.topblackactif.withdraw()

        self.topblackactif = toplevel
        self.topblackactif.overrideredirect(True)  # enlever bar du haut

        self.topblackactif.deiconify()
        self.topblackactif.update_idletasks()

        self.topblackactif.geometry(f"{self.screen_width}x{self.screen_height}+{0}+{0}")
        self.topblackactif.transient(self.root)
        self.topblackactif.lift()
        self.topblackactif.focus_force()

    ###### LES CADRES ############################################################################################
    # Appel de la création des divers cadre
    def creer_cadres(self):
        self.cadres["mainlobby"] = self.creer_cadre_mainlobby()
        self.cadres["gamemenu"] = self.creer_cadre_gamemenu()
        self.cadres["login"] = self.creer_cadre_login()
        self.cadres["jeu"] = self.creer_cadre_jeu()
        self.cadres["loading"] = self.creer_cadre_loading()

    def creer_toplevel(self,):
        self.toplevel["gameescape"] = self.creer_top_escape()
        self.toplevel["option"] = self.creer_top_option()
        self.toplevel["useroption"] = self.creer_top_user()
        self.topblack["blackgame"] = self.creer_topblack()
        self.toplevel["gagner"] = self.creer_top_gagner()


    def creer_cadre_mainlobby(self) -> Frame:
        # === Cadre principal ===
        # Utiliser la largeur et hauteur de l'écran pour le cadre principal

        self.cadremain = Frame(self.cadreapp, bg="black", width=self.screen_width, height=self.screen_height)
        # NE PAS pack ici ! On pack seulement lors de changer_cadre
        self.cadremain.pack_propagate(False)

        # === Arrière-plan fixe ===
        bg_path = os.path.join(os.path.dirname(__file__), "images/lobby2.png")
        # create a small ready image (kept as attribute) but do not place a Label that would sit above the Canvas
        # the parallax background will be rendered directly on the Canvas so it can receive Motion events
        self.tk_bg = ImageTk.PhotoImage(Image.open(bg_path).resize((self.screen_width, self.screen_height), Image.Resampling.LANCZOS))

        
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
                    "Jouer": lambda: self.changer_cadre("gamemenu"),
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

    def creer_cadre_loading(self) -> Frame:
        """
        Crée un écran de chargement avec animation
        """
        cadre_loading = Frame(self.cadreapp, bg="#1a1a1a", width=self.screen_width, height=self.screen_height)
        cadre_loading.pack_propagate(False)

        # Conteneur central
        container = Frame(cadre_loading, bg="#1a1a1a")
        container.place(relx=0.5, rely=0.5, anchor="center")

        # Titre
        Label(
            container,
            text="Chargement de la partie...",
            font=("Times New Roman", 72, "bold"),
            fg="#D4AF37",  # Or
            bg="#1a1a1a"
        ).pack(pady=20)

        # Barre de progression (optionnelle)
        self.loading_progress_var = StringVar()
        self.loading_progress_var.set("Initialisation...")

        Label(
            container,
            textvariable=self.loading_progress_var,
            font=("Arial", 32),
            fg="white",
            bg="#1a1a1a"
        ).pack(pady=10)

        # Animation de points (optionnelle)
        self.loading_label = Label(
            container,
            text="●",
            font=("Arial", 96 , "bold"),
            fg="#D4AF37",
            bg="#1a1a1a"
        )
        self.loading_label.pack(pady=20)

        # Variable pour l'animation
        self.loading_animation_running = False

        return cadre_loading

    def animer_loading(self):
        """
        Anime l'écran de chargement avec des points qui bougent
        """
        if not self.loading_animation_running:
            return

        current_text = self.loading_label.cget("text")

        # Cycle: ● → ●● → ●●● → ●
        if current_text == "●":
            self.loading_label.config(text="●●●")
        elif current_text == "●●":
            self.loading_label.config(text="●●●")
        else:
            self.loading_label.config(text="●●●")

        # Rappeler cette fonction après 500ms
        self.root.after(100, self.animer_loading)

    def demarrer_animation_loading(self):
        """Démarre l'animation de chargement"""
        self.loading_animation_running = True
        self.animer_loading()

    def arreter_animation_loading(self):
        """Arrête l'animation de chargement"""
        self.loading_animation_running = False



    def creer_cadre_gamemenu(self) -> Frame:
        # === Cadre principal ===
        self.cadre_lobby_partie = Frame(self.cadreapp, bg="black", width=self.screen_width, height=self.screen_height)
        self.cadre_lobby_partie.pack_propagate(False)


        splash_screen_size_x = int(self.screen_width * self.background_zoom)
        splash_screen_size_y = int(self.screen_height * self.background_zoom)

        self.background2 = Canvas(
            self.cadre_lobby_partie, width=self.screen_width, height=self.screen_height,
            bd=0, highlightthickness=0, bg="black"
        )
        self.background2.pack(fill="both", expand=True)

        diffx = (splash_screen_size_x - self.screen_width) // 2
        diffy = (splash_screen_size_y - self.screen_height) // 2
        self.tk_bg = ImageTk.PhotoImage(self.original_bg)
        self.splash_screen = self.background2.create_image(-diffx, -diffy, anchor="nw", image=self.tk_bg)
        self.background2.image = self.tk_bg

        def animate_background(event):
            move_x = (event.x - self.screen_width // 2) / self.vitesse_background
            move_y = (event.y - self.screen_height // 2) / self.vitesse_background
            self.background2.coords(self.splash_screen, -diffx + move_x, -diffy + move_y)

        self.background2.bind("<Motion>", animate_background)

        # === FONCTION POUR FAIRE DES BOUTONS JOLIS ===
        def make_button(parent, text, color="#3c2f2f", hover="#7a3c3c", command=None):
            btn = Label(parent, text=text, font=("Times New Roman", 22, "bold"), bg=color, fg="gold", width=15, height=2, bd=2, relief="raised")
            def on_enter(e): btn.config(bg=hover)

            def on_leave(e): btn.config(bg=color)

            def on_click(e):
                if command: command()

            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            btn.bind("<Button-1>", on_click)
            return btn

        # === CADRE GAUCHE (Créer/Commencer/IA...) ===
        left_frame = Frame(self.background2, bg="#2e1f1f", highlightbackground="goldenrod2", highlightthickness=2)
        left_frame.place(relx=0.05, rely=0.05, relwidth=0.4, relheight=0.9)

        # Ligne du haut (Créer partie / Commencer)
        top_bar = Frame(left_frame, bg="#3c2f2f")
        top_bar.pack(fill=X, pady=10)
        Label(top_bar, text="Créer partie", font=("Times New Roman", 22, "bold"), bg="#4a1d1d", fg="gold", width=15, height=2, bd=2, relief="raised").pack(side=LEFT, expand=True, padx=10)
        make_button(top_bar, "Commencer", "#2d6a2d", hover="#3fa63f",
                command=lambda: self.lancer_partie()
               ).pack(side=LEFT, expand=True, padx=10)

        # === Liste IA avec Scroll
        ia_frame = Frame(left_frame, bg="#3c2f2f")
        ia_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        # Scroll components
        canvas = Canvas(ia_frame, bg="#3c2f2f", highlightthickness=0)
        scrollbar = Scrollbar(ia_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = Frame(canvas, bg="#3c2f2f")
        
        # Quand le contenu change, mettre à jour la zone scrollable
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Créer la fenêtre dans le canvas 
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Ajuster dynamiquement la largeur du contenu quand le canvas change
        def resize_scrollable(event):
            canvas.itemconfig(window_id, width=event.width)

        canvas.bind("<Configure>", resize_scrollable)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # === Données IA disponibles ===
        types_ia = ["IA Agressive", "IA Conquête", "IA Défensive"]
        difficultes = ["Facile", "Moyenne", "Difficile"]

        ia_lignes = []
        ia_list = []

        def getIa():
            ia_list.clear()
            for ia in ia_lignes:
                ia_info = {
                    "type": ia["type_var"].get(),
                    "difficulte": ia["difficulte_var"].get()
                }
                ia_list.append(ia_info)
            print("IAs sélectionnées :", ia_list)
            self.parent.info_ia = ia_list

        def creer_ligne_ia(type_init="IA Agressive", difficulte_init="Facile"):
            ligne = Frame(scrollable_frame, bg="#4a1d1d", highlightbackground="goldenrod2", highlightthickness=2, padx=5, pady=5)
            ligne.pack(pady=20)

            def supprimer():
                ia_lignes.remove(ia_entry)
                ligne.destroy()
                getIa()

            btn_del = Label(ligne, text="X", font=("Arial", 16, "bold"), bg="#7a3c3c", fg="white", width=2)
            btn_del.pack(side=LEFT, padx=5)
            btn_del.bind("<Button-1>", lambda e: supprimer())

            inner = Frame(ligne, bg="#4a1d1d")
            inner.pack(side=LEFT, fill=BOTH, expand=True)

            top_row = Frame(inner, bg="#4a1d1d")
            top_row.pack(fill=X, pady=2)

            Label(top_row, text="Type       :", bg="#4a1d1d", fg="white", font=("Arial", 14)).pack(side=LEFT, padx=5)
            label_type = Label(top_row, text=type_init, bg="#3c2f2f", fg="gold", font=("Arial", 14), width=15)
            label_type.pack(side=LEFT, padx=5)

            def changer_type():
                current = types_ia.index(label_type.cget("text"))
                label_type.config(text=types_ia[(current + 1) % len(types_ia)])
                ia_entry["type_var"].set(label_type.cget("text"))

            btn_type = Label(top_row, text="▼", bg="#2d2d2d", fg="white", width=2)
            btn_type.pack(side=LEFT, padx=5)
            btn_type.bind("<Button-1>", lambda e: changer_type())

            bottom_row = Frame(inner, bg="#4a1d1d")
            bottom_row.pack(fill=X, pady=2)

            Label(bottom_row, text="Difficulté :", bg="#4a1d1d", fg="white", font=("Arial", 14)).pack(side=LEFT, padx=5)
            label_diff = Label(bottom_row, text=difficulte_init, bg="#3c2f2f", fg="gold", font=("Arial", 14), width=15)
            label_diff.pack(side=LEFT, padx=5)

            def changer_diff():
                current = difficultes.index(label_diff.cget("text"))
                label_diff.config(text=difficultes[(current + 1) % len(difficultes)])
                ia_entry["difficulte_var"].set(label_diff.cget("text"))

            btn_diff = Label(bottom_row, text="▼", bg="#2d2d2d", fg="white", width=2)
            btn_diff.pack(side=LEFT, padx=5)
            btn_diff.bind("<Button-1>", lambda e: changer_diff())

            ia_entry = {
                "frame": ligne,
                "type_var": StringVar(value=type_init),
                "difficulte_var": StringVar(value=difficulte_init)
            }
            ia_lignes.append(ia_entry)

        for i in range(1):
            creer_ligne_ia(type_init=types_ia[i % len(types_ia)], difficulte_init=difficultes[i % len(difficultes)])

        def ajouter_ia():
            if (len(self.parent.info_ia) < 4):
                creer_ligne_ia()
                getIa()

        make_button(left_frame, "Ajouter IA", "#4a1d1d", command=ajouter_ia).pack(pady=10)


        # Mode de jeu
        Label(left_frame, text="Mode de jeu", font=("Times New Roman", 20, "bold"), fg="white", bg="#2e1f1f").pack(pady=5)
        # Mode de jeu - radio buttons on one line
        self.mode_jeu = StringVar(value="paix")
        modes = [("Paix mondial", "paix"), ("Commerce", "commerce"), ("Achèvement", "achevement")]
        rb_frame = Frame(left_frame, bg="#2e1f2f")
        rb_frame.pack(pady=5, fill=X)
        for text, val in modes:
            rb = Radiobutton(
            rb_frame, text=text, variable=self.mode_jeu, value=val,
            font=("Arial", 14), bg="#2e1f2f", fg="gold",
            selectcolor="#4a1d1d", activebackground="#7a3c3c",
            activeforeground="gold", indicatoron=1,
            command=lambda v=val: setattr(self.parent, "mode_de_jeu", v)
            )
            rb.pack(side=LEFT, padx=8, expand=True)

        # === MILIEU (Option partie) ===
        # Option Partie as a button instead of a frame
        make_button(
            self.background2,
            "Option Partie",
            color="#4a1d1d",
            hover="#7a3c3c",
            command=lambda: (self.changer_topblack("blackgame"), self.changer_toplevel("option"))
        ).place(relx=0.53, rely=0.5, anchor="center")

        # === DROITE (Charger Partie + Table de jeu) ===
        right_frame = Frame(self.background2, bg="#2e1f1f", highlightbackground="goldenrod2", highlightthickness=2)
        right_frame.place(relx=0.62, rely=0.05, relwidth=0.33, relheight=0.9)

        Label(right_frame, text="Charger Partie", font=("Times New Roman", 22, "bold"), bg="#4a1d1d", fg="gold", width=15, height=2, bd=2, relief="raised").pack(pady=10)
        # === Game saves treeview (chargement de parties) ===
        saves_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(saves_dir, exist_ok=True)


        tree_frame = Frame(right_frame, bg="#2e1f1f")
        tree_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        #cols = ("name", "modified", "size_kb")
        cols = ("name", "date", "iteration")
        self.saves_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse", height=8)
        self.saves_tree.heading("name", text="Joueur")
        self.saves_tree.heading("date", text="Date")
        self.saves_tree.heading("iteration", text="Itération")
        self.saves_tree.column("name", width=150, anchor="w")
        self.saves_tree.column("date", width=170, anchor="center")
        self.saves_tree.column("iteration", width=100, anchor="e")

        ysb = Scrollbar(tree_frame, orient="vertical", command=self.saves_tree.yview)
        self.saves_tree.configure(yscroll=ysb.set)
        self.saves_tree.pack(side=LEFT, fill=BOTH, expand=True)
        ysb.pack(side=RIGHT, fill=Y)

        def populate_saves():
            """
            Affiche toutes les sauvegardes du joueur connecté
            """
            saves_dir = "data"
            os.makedirs(saves_dir, exist_ok=True)

            # Vider la liste actuelle
            for i in self.saves_tree.get_children():
                self.saves_tree.delete(i)

            try:
                fichier = os.path.join(saves_dir, "sauvegarde.pkl")

                if not os.path.exists(fichier):
                    return

                # CHARGER TOUTES LES SAUVEGARDES
                import pickle
                with open(fichier, 'rb') as f:
                    sauvegardes_dict = pickle.load(f)

                # Vérifier que c'est un dictionnaire
                if not isinstance(sauvegardes_dict, dict):
                    return

                # RÉCUPÉRER LE NOM DU JOUEUR CONNECTÉ
                nom_joueur_actuel = self.parent.nom_joueur_local

                if not nom_joueur_actuel:
                    print("⚠️ Aucun joueur connecté")
                    return

                # VÉRIFIER SI CE JOUEUR A UNE SAUVEGARDE
                if nom_joueur_actuel not in sauvegardes_dict:
                    print(f"Aucune sauvegarde trouvée pour '{nom_joueur_actuel}'")
                    return

                # AFFICHER LA SAUVEGARDE DU JOUEUR
                sauvegarde_data = sauvegardes_dict[nom_joueur_actuel]

                try:
                    if isinstance(sauvegarde_data, dict):
                        date_save = sauvegarde_data.get('date', 'N/A')
                        iteration = sauvegarde_data.get('iteration', '?')
                    else:
                        date_save = "N/A"
                        iteration = "?"

                    # Afficher avec le nom du joueur comme identifiant
                    self.saves_tree.insert(
                        "",
                        "end",
                        iid=nom_joueur_actuel,  # Utiliser le nom du joueur comme ID
                        values=(nom_joueur_actuel, date_save, iteration)
                    )

                except Exception as e:
                    print(f"Erreur pour afficher la sauvegarde: {e}")

            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de lister les sauvegardes:\n{e}")

        def load_selected(event=None):
            sel = self.saves_tree.selection()
            if not sel:
                return

            # sel[0] contient maintenant le NOM DU JOUEUR (l'iid du Treeview)
            nom_joueur = sel[0]

            try:
                # Nettoyer les actions en attente
                self.parent.actions_requises = []

                # CHARGER LA SAUVEGARDE AVEC LE NOM DU JOUEUR
                success = self.parent.charger(nom_joueur)

                if not success:
                    messagebox.showerror("Erreur", f"Impossible de charger la sauvegarde de '{nom_joueur}'")

            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger la sauvegarde:\n{e}")
                import traceback
                traceback.print_exc()

        def delete_selected():
            sel = self.saves_tree.selection()
            if not sel:
                return

            # sel[0] contient le nom du joueur
            nom_joueur = sel[0]

            if messagebox.askyesno("Supprimer", f"Supprimer la sauvegarde de '{nom_joueur}' ?"):
                try:
                    # APPELER LA MÉTHODE DE SUPPRESSION DU CONTRÔLEUR
                    success = self.parent.supprimer_sauvegarde(nom_joueur)

                    if success:
                        # Supprimer de l'affichage
                        self.saves_tree.delete(nom_joueur)
                        messagebox.showinfo("Succès", "Sauvegarde supprimée")
                    else:
                        messagebox.showerror("Erreur", "Impossible de supprimer la sauvegarde")
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de supprimer:\n{e}")

        # boutons d'action
        btn_frame = Frame(right_frame, bg="#2e1f1f")
        btn_frame.place(relx=0.5, rely=0.7, anchor="n")

        btn_load = Button(btn_frame, text="Charger", width=12, command=load_selected)
        btn_del = Button(btn_frame, text="Supprimer", width=12, command=delete_selected)
        btn_refresh = Button(btn_frame, text="Actualiser", width=12, command=populate_saves)

        btn_load.grid(row=0, column=0, padx=6, pady=8)
        btn_del.grid(row=0, column=1, padx=6, pady=8)
        btn_refresh.grid(row=0, column=2, padx=6, pady=8)

        # double-clic pour charger rapidement
        self.saves_tree.bind("<Double-1>", load_selected)

        # remplissage initial
        populate_saves()

        make_button(self.cadre_lobby_partie, "<- Retourner", "#4a1d1d", command=lambda: self.changer_cadre("mainlobby")).place(relx=0.95, rely=0.02, anchor="center")

        return self.cadre_lobby_partie

    # le login (ce qui 'login' à l'écran lors du démarrage)
    # sera le cadre visuel initial lors du lancement de l'application
    def creer_cadre_login(self):
        # === Cadre principal ===
        self.cadrelobby = Frame(self.cadreapp, bg="white", width=self.largeur, height=self.hauteur)
        self.cadrelobby.pack(fill=BOTH, expand=True)

        # === Deux sous-cadres (gauche = image / droite = login) ===
        self.frame_gauche = Frame(self.cadrelobby, bg="#cce6ff", width=800, height=800)
        self.frame_droite = Frame(self.cadrelobby, bg="white", width=200, height=800)

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
        self.label_invite.bind("<Button-1>", lambda e: self.connecter_invite())

        # on retourne ce cadre pour l'insérer dans le dictionnaires des cadres
        return self.cadrelobby

    def connecter_invite(self):
        """Connecte un utilisateur en tant qu'invité sans passer par la base de données"""
        # Définir le nom du joueur comme "invité"
        self.parent.nom_joueur_local = "invité"
        self.nom_joueur_local.set("invité")

        # Pas besoin de charger les données utilisateur depuis la base de données
        self.parent.user = None

        # Changer vers le lobby principal
        self.changer_cadre("mainlobby")
        self.root.attributes('-fullscreen', True)

        print("Connecté en tant qu'invité")
        
    def creer_top_escape(self):
        # le cadre escape, qui apparait en toplevel lorsque le joueur presse echap
        size_x = 480
        size_y = 600
        x = (self.screen_width - size_x) // 2
        y = (self.screen_height - size_y) // 2

        self.cadreescape = Toplevel(self.root)
        self.cadreescape.title("Menu Pause")
        self.cadreescape.geometry(f"{size_x}x{size_y}+{x}+{y}")
        self.cadreescape.withdraw()  # on le cache initialement

        # === Paramètres du fond ===
        bg_path = os.path.join(os.path.dirname(__file__), "images/scroll.jpg")
        self.tk_bg = ImageTk.PhotoImage(Image.open(bg_path).resize((size_x, size_y), Image.Resampling.LANCZOS))
        self.label_bg = Label(self.cadreescape, image=self.tk_bg)
        self.label_bg.place(x=0, y=0, relwidth=1, relheight=1)

        # === Création des boutons du menu pause ===
        def make_button_pause(text, command=None , padding=60):
            frame_width = 250
            frame = Frame(self.cadreescape, bg="#4a1d1d", width=frame_width, height=50, highlightthickness=2, highlightbackground="goldenrod2")
            frame.pack_propagate(False)
            frame.pack(pady=padding)

            # Texte du bouton
            label_text = Label(frame, text=text, font=("Times New Roman", 14, "bold"), bg="#4a1d1d", fg="#D4AF37")
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
            for widget in (frame, label_text):
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)

                # Bind du clic pour exécuter la commande
                widget.bind("<Button-1>", on_click)

            return frame

        # === Boutons spécifiques au menu Pause ===
        btnreprendre = make_button_pause("Reprendre", command=lambda: (self.reprendre_partie(),self.cadreescape.withdraw(), self.changer_topblack(None), self.changer_toplevel(None)))
        btnsave = make_button_pause("Sauvegarder",
                                    command=lambda: (
                                        self.changer_topblack(None),
                                        self.changer_toplevel(None),
                                        self.sauvegarder(),
                                        self.root.after(100, lambda: (
                                            self.changer_topblack("blackgame"),
                                            self.changer_toplevel("gameescape")
                                        ))
                                    ))
        btnquitter = make_button_pause("Quitter la partie", command=lambda: (self.changer_cadre("mainlobby"), self.arreter_boucle(), self.cadreescape.withdraw(), self.changer_topblack(None), self.changer_toplevel(None)))

        # === Affichage des boutons ===
        for btn in [btnreprendre, btnsave, btnquitter]:
            btn.pack(pady=5)

        return self.cadreescape

    def maj_message_victoire(self, nouveau_msg: str):
        if hasattr(self, "txt_victoire"):
            # Mettre à jour le contenu du widget Text correctement
            self.txt_victoire.config(state=NORMAL)
            self.txt_victoire.delete("1.0", END)
            self.txt_victoire.insert("1.0", str(nouveau_msg))
            # Ajuster la hauteur en fonction du contenu (approx. 40 chars/ligne déjà utilisé à la création)
            lines = int(self.txt_victoire.index('end-1c').split('.')[0])
            new_height = min(10, max(3, lines))
            self.txt_victoire.config(height=new_height)
            self.txt_victoire.config(state=DISABLED)
            self.txt_victoire.update_idletasks()


    def creer_top_gagner(self):
        # toplevel pour l'écran "gagner" (noms de variables distincts pour éviter les collisions)
        size_x = 480
        size_y = 600
        x = (self.screen_width - size_x) // 2
        y = (self.screen_height - size_y) // 2

        self.top_gagner = Toplevel(self.root)
        self.top_gagner.title("Victoire")
        self.top_gagner.geometry(f"{size_x}x{size_y}+{x}+{y}")
        self.top_gagner.withdraw()  # caché initialement

        # fond spécifique (variables distinctes)
        bg_path_gagner = os.path.join(os.path.dirname(__file__), "images/scroll.jpg")
        self.tk_bg_gagner = ImageTk.PhotoImage(Image.open(bg_path_gagner).resize((size_x, size_y), Image.Resampling.LANCZOS))
        self.label_bg_gagner = Label(self.top_gagner, image=self.tk_bg_gagner)
        self.label_bg_gagner.place(x=0, y=0, relwidth=1, relheight=1)

        # Titre centré pour l'écran de victoire
        self.lbl_victoire_title = Label(
            self.top_gagner,
            text="Parte finie !",
            font=("Times New Roman", 42, "bold"),
            bg="#4a1d1d",
            fg="#D4AF37"
        )
        # placer en haut, centré
        self.lbl_victoire_title.pack(pady=10)

        # utiliser le message de victoire fourni par le parent (fallback si absent)
        msg = getattr(self.parent, "victoire_msg", "Partie finie !")

        # multi-line, auto-sizing message box (adapts to message length)
        msg_str = str(msg)

        self.txt_victoire = Text(
            self.top_gagner,
            wrap=WORD,
            font=("Times New Roman", 18, "bold"),
            bg="#4a1d1d",
            fg="#D4AF37",
            bd=0,
            height=400,
            width=50
        )
        self.txt_victoire.insert("1.0", msg_str)
        self.txt_victoire.config(state=DISABLED)
        self.txt_victoire.pack(fill=BOTH , padx=20, pady=20)

        # helper local pour créer des boutons stylés dans ce toplevel
        def make_button_gagner(text, command=None, padding=60):
            frame_w = 250
            f = Frame(self.top_gagner, bg="#4a1d1d", width=frame_w, height=50, highlightthickness=2, highlightbackground="goldenrod2")
            f.pack_propagate(False)
            f.pack(pady=padding)

            lbl = Label(f, text=text, font=("Times New Roman", 14, "bold"), bg="#4a1d1d", fg="#D4AF37")
            lbl.pack(side=TOP, fill=BOTH, expand=True)

            def _on_enter(e):
                f.config(bg="#7a3c3c")
                lbl.config(bg="#7a3c3c")

            def _on_leave(e):
                f.config(bg="#4a1d1d")
                lbl.config(bg="#4a1d1d")

            def _on_click(e):
                if command:
                    command()

            for w in (f, lbl):
                w.bind("<Enter>", _on_enter)
                w.bind("<Leave>", _on_leave)
                w.bind("<Button-1>", _on_click)

            return f

        # Boutons spécifiques à l'écran "gagner"
        btn_quitter_gagner = make_button_gagner(
            "Quitter la partie",
            command=lambda: (
                self.changer_cadre("mainlobby"),
                self.arreter_boucle(),
                self.top_gagner.withdraw(),
                self.changer_topblack(None),
                self.changer_toplevel(None)
            )
        )

        # affichage (le helper a déjà packé les frames, on peut ajuster marge si besoin)
        btn_quitter_gagner.pack(pady=5)

        return self.top_gagner

    def creer_top_option(self):
        # cadre d'options (toplevel distinct pour éviter les collisions de noms)
        opt_size_x = 480
        opt_size_y = 600
        opt_x = (self.screen_width - opt_size_x) // 2
        opt_y = (self.screen_height - opt_size_y) // 2

        self.top_option = Toplevel(self.root)
        self.top_option.title("Options")
        self.top_option.geometry(f"{opt_size_x}x{opt_size_y}+{opt_x}+{opt_y}")
        self.top_option.withdraw()  # caché initialement

        # fond spécifique pour la fenêtre d'options
        opt_bg_path = os.path.join(os.path.dirname(__file__), "images/scroll.jpg")
        self.opt_tk_bg = ImageTk.PhotoImage(Image.open(opt_bg_path).resize((opt_size_x, opt_size_y), Image.Resampling.LANCZOS))
        self.opt_label_bg = Label(self.top_option, image=self.opt_tk_bg)
        self.opt_label_bg.place(x=0, y=0, relwidth=1, relheight=1)

        # création d'un helper de bouton local à cette toplevel (noms locaux pour éviter recouvrement)
        def make_option_button(text, command=None, padding=60):
            frame_w = 250
            frame = Frame(self.top_option, bg="#4a1d1d", width=frame_w, height=50, highlightthickness=2, highlightbackground="goldenrod2")
            frame.pack_propagate(False)
            frame.pack(pady=padding)

            lbl = Label(frame, text=text, font=("Times New Roman", 14, "bold"), bg="#4a1d1d", fg="#D4AF37")
            lbl.pack(side=TOP, fill=BOTH, expand=True)

            def _on_enter(e):
                frame.config(bg="#7a3c3c")
                lbl.config(bg="#7a3c3c")
            def _on_leave(e):
                frame.config(bg="#4a1d1d")
                lbl.config(bg="#4a1d1d")
            def _on_click(e):
                if command:
                    command()

            for w in (frame, lbl):
                w.bind("<Enter>", _on_enter)
                w.bind("<Leave>", _on_leave)
                w.bind("<Button-1>", _on_click)

            return frame

        # boutons pour la fenêtre d'options
        opt_btn_resume = make_option_button(
            "Reprendre",
            command=lambda: (self.top_option.withdraw(), self.changer_topblack(None), self.changer_toplevel(None))
        )

        # affichage (empilement) des boutons
        opt_btn_resume.pack(pady=5)

        # --- Section : changer la seed de génération ---
        # Sauvegarde de la seed originale si possible
        self._option_original_seed = getattr(self.parent, "default_seed", None)

        seed_frame = Frame(self.top_option, bg="goldenrod2")
        seed_frame.pack(pady=10)

        Label(seed_frame, text="Seed de génération :", font=("Arial", 12, "bold"), bg="#4a1d1d", fg="#D4AF37").pack(pady=(8,4))

        self.seed_var = StringVar()
        if self._option_original_seed is not None:
            self.seed_var.set(str(self._option_original_seed))
        else:
            self.seed_var.set("")

        seed_entry = Entry(seed_frame, textvariable=self.seed_var, width=20, font=("Arial", 12))
        seed_entry.pack(pady=4)

        # callbacks apply / reset
        def apply_seed():
            val = self.seed_var.get().strip()
            if val == "":
                messagebox.showerror("Erreur", "Veuillez entrer une valeur pour la seed.")
                return
            try:
                seed = int(val)
            except Exception:
                messagebox.showerror("Erreur", "La seed doit être un entier.")
                return

            # preferer une méthode publique si elle existe
            if hasattr(self.parent, "set_seed") and callable(self.parent.set_seed):
                try:
                    self.parent.set_seed(seed)
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible d'appliquer la seed:\n{e}")
                    return
            else:
                setattr(self.parent, "seed", seed)

            messagebox.showinfo("Ok", f"Seed définie à {seed}")

        def reset_seed_to_default():
            default = getattr(self.parent, "default_seed", self._option_original_seed)
            if default is None:
                messagebox.showinfo("Info", "Aucune seed par défaut disponible.")
                return

            if hasattr(self.parent, "set_seed") and callable(self.parent.set_seed):
                try:
                    self.parent.set_seed(default)
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de réinitialiser la seed:\n{e}")
                    return
            else:
                setattr(self.parent, "seed", default)

            self.seed_var.set(str(default))


            messagebox.showinfo("Ok", "Seed réinitialisée à la valeur par défaut.")

        # bouton apply / reset
        btns_frame = Frame(seed_frame, bg="goldenrod2")
        btns_frame.pack(pady=8)

        apply_btn = Button(btns_frame, text="Appliquer", command=apply_seed, width=12)
        reset_btn = Button(btns_frame, text="Réinitialiser (défaut)", command=reset_seed_to_default, width=18)

        apply_btn.grid(row=0, column=0, padx=6)
        reset_btn.grid(row=0, column=1, padx=6)

        return self.top_option


    def mettre_en_pause_partie(self):
        """Met le jeu en pause via le contrôleur"""
        if hasattr(self.parent, 'mettre_en_pause'):
            self.parent.mettre_en_pause()
            print("Interface : Jeu mis en pause")

    def reprendre_partie(self):
        """Reprend le jeu via le contrôleur"""
        if hasattr(self.parent, 'reprendre_jeu'):
            self.parent.reprendre_jeu()
            print("Interface : Jeu repris")
    def arreter_boucle(self):
        self.parent.arreter_boucle_jeu()

        if hasattr(self, 'canevas'):
            self.canevas.delete("ALL")
        # Vider aussi les actions locales
        if hasattr(self, 'action'):
            self.action.persochoisi = []
            self.action.ciblechoisi = None
            self.action.prochaineaction = None
            self.action.position = []
        #Va mettre self.partie = None
        self.parent.detruire_partie()



    def creer_top_user(self):
        # le cadre escape, qui apparait en toplevel lorsque le joueur presse echap
        self.top = Toplevel(self.root)
        self.top.title("Menu Pause")
        self.top.geometry("300x200")
        self.top.withdraw()  # on le cache initialement

        # boutons du menu pause
        btnreprendre = Button(self.top, text="Reprendre", command=self.top.withdraw)
        btnreprendre.pack(pady=10)

        btnaide = Button(self.top, text="Tab user")
        btnaide.pack(pady=10)

        return self.top
    
    def creer_topblack(self):

        # le cadre escape, qui apparait en toplevel lorsque le joueur presse echap
        self.topblack_win = Toplevel(self.root , background="black")
        self.topblack_win.title("black")
        self.topblack_win.overrideredirect(True)  # enlever bar du haut

        self.topblack_win.configure(bg='black')
        self.topblack_win.withdraw()  # on le cache initialement
        self.topblack_win.attributes('-alpha', 0.5)  # noir plus pale
        self.topblack_win.lift()  #  dessus de la page

        return self.topblack_win

    def enregistrer(self, username,password):
        condition = self.parent.enregistrerUser(username, password)
        return condition

    def enregistrer_et_changer(self):
        message = self.enregistrer(self.entree_nom.get(), self.entree_mdp.get())
        if  message == True:
            self.nom_joueur_local.set(self.entree_nom.get())
            #self.parent.nom_joueur_local = {self.entree_nom.get()}
            self.user = self.parent.user
            self.changer_cadre("mainlobby")
            self.root.attributes('-fullscreen', True)
        if message == "Vide":
            messagebox.showerror("Erreur", "Veuillez à ne pas laisser les champs vide.")
        if message == False:
            # Affiche ton message d'erreur (à adapter selon ton interface)
            messagebox.showerror("Erreur", "L'utilisateur existe déjà")

    def login(self, username,password):
        condition = self.parent.loginUser(username, password)
        return condition

    def login_et_changer(self):
        message = self.login(self.entree_nom.get(), self.entree_mdp.get())
        print(f"Type: {type(self.entree_nom)}, Valeur: {self.entree_nom.get()}")
        if message == True:
            self.nom_joueur_local.set(self.entree_nom.get())
            #self.parent.nom_joueur_local = self.entree_nom.get()
            self.user = self.parent.user
            self.changer_cadre("mainlobby")
            self.root.attributes('-fullscreen', True)
        if message == "Vide":
            messagebox.showerror("Erreur", "Veuillez à ne pas laisser les champs vide.")
        if message == False:
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
                      xscrollcommand=self.scrollH.set, highlightthickness=0)
        # Keep scrollbars functional but make them invisible (hidden)
        self.scrollV.config(command=self.canevas.yview, width=0, troughcolor=self.canevas['bg'], bd=0, highlightthickness=0)
        self.scrollH.config(command=self.canevas.xview, width=0, troughcolor=self.canevas['bg'], bd=0, highlightthickness=0)
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

        # minicarte
        # minicarte : placer en bas à gauche du cadre de jeu (au-dessus du canevas)
        self.minicarte = Canvas(self.cadrecanevas, width=self.tailleminicarte, height=self.tailleminicarte,
                    bg="tan1", highlightthickness=0, borderwidth=2)
        # placer ancré en bas-gauche avec une petite marge (anchor 'sw' = south-west)
        self.minicarte.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor='se')
        self.minicarte.bind("<Button-1>", self.deplacer_carte)

        self.connecter_event()

    def creer_HUD(self):
        self.cadrejeuinfo = Frame(self.cadrecanevas, bg="goldenrod3")
        # des etiquettes d'info
        self.infohud = {"Nourriture": None,
                        "Bois": None,
                        "Roche": None,
                        "Aureus": None}

        # fonction interne uniquement pour reproduire chaque item d'info
        def creer_champ_interne(listechamp):
            titre = Champ(self.cadrejeuinfo, text=i, bg="red", fg="black" )
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
        fontinfo = ("arial", 25, "bold")
        champmsg = Label(self.cadrejeuinfo, text="", font = fontinfo , bg="#4a1d1d", fg="#D4AF37" , highlightthickness=2, highlightbackground="goldenrod2")
        champmsg.pack(side=LEFT)

        self.infohud["msggeneral"] = [champmsg]

        self.cadrejeuinfo.place(relx=0.0, rely=0.0)

    def sauvegarder(self):
        self.parent.sauvegarde()

    def charger(self):
        nom_joueur = self.parent.nom_joueur_local
        #Avec le nom du joueur
        self.parent.charger(nom_joueur)

    def creer_cadre_jeu_action(self):
        # Crée un cadre pour afficher le texte d'aide/contextuel au-dessus du panneau d'action
        overlay_width_action = self.screen_width // 6
        overlay_height = self.screen_height // 4

        # ============================
        #  TEXTE CONTEXTUEL (au-dessus du panneau action)
        # ============================
        self.cadre_action_text = Frame(
            self.cadrecanevas,
            bg="#222",
            width=overlay_width_action,
            bd=2,
            relief="ridge"
        )
        self.cadre_action_text.place(
            relx=0.01, rely=1 - (overlay_height / self.screen_height) - 0.02,
            anchor="sw"
        )

        # Widget Text dynamique qui s'étend verticalement selon le texte
        self.action_text_var = StringVar()
        self.action_text_widget = Text(
            self.cadre_action_text,
            bg="#222",
            fg="white",
            font=("Arial", 24 , "bold"),
            wrap="word",
            width=overlay_width_action // 10,  # largeur similaire à avant
            height=2,  # hauteur initiale
            relief="flat"
        )
        self.action_text_widget.pack(fill=BOTH, expand=True, padx=8, pady=10)
        self.action_text_widget.config(state=DISABLED)

        def update_action_text(text):
            self.action_text_widget.config(state=NORMAL)
            self.action_text_widget.delete("1.0", END)
            self.action_text_widget.insert("1.0", text)
            self.action_text_widget.config(state=DISABLED)
            # Ajuste la hauteur selon le contenu
            lines = int(self.action_text_widget.index('end-1c').split('.')[0])
            self.action_text_widget.config(height=max(2, lines))
            self.cadre_action_text.update_idletasks()

        self.update_action_text = update_action_text

        # ============================
        #  Cadre condition
        # ============================
        overlay_width_victoire = self.screen_width // 6

        self.cadre_condition = Frame(
            self.cadrecanevas,
            bg="#222",
            width=overlay_width_victoire,
            bd=2,
            relief="ridge"
        )


        self.cadre_condition.place(
            relx=1 - (overlay_width_victoire / self.screen_width) - 0.15,
            rely=0.01,
            anchor="nw"
        )

        # Widget Text dynamique qui s'étend verticalement selon le texte
        # Récupère la condition de victoire depuis le parent si disponible,
        # sinon on utilise une valeur par défaut.
        self.conditions_victoire = getattr(self.parent, "conditions_victoire", {
            "bois": 220,
            "aureus": 200,
            "nourriture": 200,
            "roche": 200
        })

        self.condition_widget = Text(
            self.cadre_condition,
            bg="#222",
            fg="white",
            font=("Arial", 24, "bold"),
            wrap="word",
            width=overlay_width_action // 10,  # largeur similaire à avant
            height=2,  # hauteur initiale, ajustée ensuite
            relief="flat"
        )
        self.condition_widget.pack(fill=BOTH, expand=True, padx=8, pady=10)

        def _format_conditions(d):
            if isinstance(d, dict):
                return "\n".join(f"{k.capitalize()} : {v}" for k, v in d.items())
            return str(d)

        def update_conditions_victoire_display():
            # récupère la valeur la plus à jour depuis le parent si elle existe
            latest = getattr(self.parent, "conditions_victoire", None)
            if latest is not None:
                self.conditions_victoire = latest

            # calcule ce qu'il manque au joueur courant (si disponible)
            def _compute_missing():
                missing = {}
                nom = getattr(self.parent, "nom_joueur_local", None)
                if not nom:
                    return missing
                modele = getattr(self, "modele", None)
                if not modele:
                    return missing
                joueur = modele.joueurs.get(nom)
                if not joueur:
                    return missing
                ressources_raw = getattr(joueur, "ressources", {}) or {}
                # Normaliser les clés pour accepter variantes (ex: "arbre" -> "bois", "or"/"gold" -> "aureus", etc.)
                ressources = {}
                synonymes = {
                    "bois": {"bois", "arbre", "wood"},
                    "nourriture": {"nourriture", "food", "baie", "berries", "berry"},
                    "roche": {"roche", "stone", "pierre"},
                    "aureus": {"aureus", "or", "gold"}
                }
                for k, v in ressources_raw.items():
                    kl = str(k).lower()
                    placed = False
                    for canon, forms in synonymes.items():
                        if kl in forms or kl == canon:
                            try:
                                ressources[canon] = int(v)
                            except Exception:
                                ressources[canon] = v
                            placed = True
                            break
                    if not placed:
                        # garder les autres clés en minuscules
                        try:
                            ressources[kl] = int(v)
                        except Exception:
                            ressources[kl] = v

                conds = self.conditions_victoire if isinstance(self.conditions_victoire, dict) else {}
                for k, req in conds.items():
                    try:
                        need = int(req)
                    except Exception:
                        # ignorer valeurs non numériques
                        continue
                    key_lower = k.lower()
                    cur = int(ressources.get(key_lower, ressources.get(k, 0) or 0))
                    missing_amt = max(0, need - cur)
                    # n'ajouter que si réellement manquant (pour afficher "Bois : 20" quand il manque 20)
                    if missing_amt > 0:
                        missing[key_lower] = missing_amt

                return missing

            missing = _compute_missing()

            # met à jour le widget de condition
            self.condition_widget.config(state=NORMAL)
            self.condition_widget.delete("1.0", END)
            self.condition_widget.insert("1.0", "Conditions de Victoire:\n")
            self.condition_widget.insert("2.0", _format_conditions(self.conditions_victoire))

            # si on a des informations sur ce qui manque, les afficher
            if missing:
                self.condition_widget.insert(END, "\n\nManquant pour atteindre la condition :\n")
                for k, v in missing.items():
                    self.condition_widget.insert(END, f"- {k.capitalize()} : {v}\n")

                all_met = all(val == 0 for val in missing.values())
                status = "Conditions atteintes !" if all_met else "Encore des ressources nécessaires."
                self.condition_widget.insert(END, f"\nStatut : {status}\n")

            # ajuster la hauteur selon le contenu (limiter entre 2 et 12 lignes)
            try:
                lines = int(self.condition_widget.index('end-1c').split('.')[0])
                self.condition_widget.config(height=max(2, min(12, lines)))
            except Exception:
                pass

            self.condition_widget.config(state=DISABLED)
            self.cadre_condition.update_idletasks()

        # Exposition d'une méthode utile pour rafraîchir l'affichage depuis l'extérieur
        self.update_conditions_victoire_display = update_conditions_victoire_display

        # texte initial demandé
        update_conditions_victoire_display()



    
        # ============================
        #  PANNEAU D'ACTION (gauche)
        # ============================
        self.cadreaction = Frame(
            self.cadrecanevas,
            bg="#2e2e2e",
            width=overlay_width_action,
            height=overlay_height,
            bd=2,
            relief="ridge"
        )
        self.cadreaction.place(
            relx=0.01, rely=0.99,
            anchor="sw"
        )

        self.canevasaction = Canvas(
            self.cadreaction,
            width=overlay_width_action,
            height=overlay_height,
            bg="#3d3d3d",
            highlightthickness=0
        )
        self.canevasaction.pack(fill="both", expand=True)

        # ============================
        #  PANNEAU INFO (collé à droite)
        # ============================
        overlay_width_info = self.screen_width // 4

        self.cadre_info = Frame(
            self.cadrecanevas,
            bg="#2e2e2e",
            width=overlay_width_info,
            height=overlay_height,
            bd=2,
            relief="ridge"
        )
        # Position juste collé à droite du panneau action
        self.cadre_info.place(
            x=overlay_width_action + 40,
            rely=0.99,
            anchor="sw"
        )

        self.canevasinfo = Canvas(
            self.cadre_info,
            width=overlay_width_info,
            height=overlay_height,
            bg="#3d3d3d",
            highlightthickness=0
        )
        self.canevasinfo.pack(fill="both", expand=True)

        # ============================
        #  INTERACTION : survol des boutons/action
        # ============================
        self.canevasaction.bind("<Leave>", lambda e: self.update_action_text(""))

        # Pour afficher un texte par défaut au démarrage
        self.update_action_text("Survolez une action pour voir son description.")

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
        # clic gauche : déplacement si sélection, sinon reset action
        self.canevas.bind("<Button-1>", self.clic_jeu)
        self.canevas.bind("<Button-3>", self.construire_batiment)
        # faire une multiselection
        self.canevas.bind("<Shift-Button-1>", self.debuter_selection)
        self.canevas.bind("<Shift-B1-Motion>", self.afficher_selection)
        self.canevas.bind("<Shift-ButtonRelease-1>", self.terminer_selection)

        self.canevas.bind("<Button-1>", self.annuler_action)
        self.canevas.tag_bind("fond", "<Button-1>", self.forcer_deselection)

        self.canevas.bind("<Button-2>", self.indiquer_position)

        self.canevas.bind("<MouseWheel>", self.OnMouseWheel)
        self.canevas.bind("<Control-MouseWheel>", self.OnCtrlMouseWheel)
        self.canevas.bind("<ButtonPress-1>", self.start_drag)
        self.canevas.bind("<B1-Motion>", self.do_drag)

        # soit aux dessins, en vertu de leur tag (propriétés des objets dessinés)
        # ALL va réagir à n'importe quel dessin
        # sinon on spécifie un tag particulier, exemple avec divers tag, attaché par divers événements
        self.canevas.tag_bind("batiment", "<Button-1>", self.handle_batiment_click)

        self.canevas.tag_bind("perso", "<Button-1>", self.ajouter_selection)
        self.canevas.tag_bind("arbre", "<Button-1>", self.ramasser_ressource)
        self.canevas.tag_bind("aureus", "<Button-1>", self.ramasser_ressource)
        self.canevas.tag_bind("roche", "<Button-1>", self.ramasser_ressource)
        self.canevas.tag_bind("baie", "<Button-1>", self.ramasser_ressource)
        self.canevas.tag_bind("eau", "<Button-1>", self.ramasser_ressource)
        self.canevas.tag_bind("daim", "<Button-1>", self.chasser_ressource)

        self.canevas.tag_bind("ours", "<Button-1>", self.chasser_ressource)

        # Hover/leave for each tag to show contextual info
        def show_tag_info(event, tag_type):
            txt = ""
            if tag_type == "arbre":
                txt = "Cliquez sur un ouvrier pour ramasser du bois de cet arbre."
            elif tag_type == "aureus":
                txt = "Cliquez sur un ouvrier pour ramasser de l'or (Aureus)."
            elif tag_type == "roche":
                txt = "Cliquez sur un ouvrier pour ramasser de la pierre."
            elif tag_type == "baie":
                txt = "Cliquez sur un ouvrier pour ramasser de la nourriture (baies)."
            elif tag_type == "eau":
                txt = "Cliquez sur un ouvrier pour ramasser de la nourriture."
            elif tag_type == "daim":
                txt = "Cliquez sur un ouvrier pour chasser ce daim."
            elif tag_type == "ours":
                txt = "Cliquez sur un ouvrier pour chasser cet ours."
            elif tag_type == "perso":
                txt = "Personnage\nCliquez pour sélectionner"

            self.update_action_text(txt)

        def clear_tag_info(event):
            self.update_action_text("")
        
        for tag in ["arbre", "aureus", "roche", "baie", "eau", "daim", "perso", "ours"]:
            self.canevas.tag_bind(tag, "<Enter>", lambda e, t=tag: show_tag_info(e, t))
            self.canevas.tag_bind(tag, "<Leave>", clear_tag_info)


    def OnMouseWheel(self, evt):
        print(evt.keysym)
        rep = self.scrollV.get()[0]
        if evt.delta < 0:
            rep = rep + 0.02
        else:
            rep = rep - 0.02
        self.canevas.yview_moveto(rep)
        self.update_minimap_viewport()


    def OnCtrlMouseWheel(self, evt):
        print("IN X")
        rep = self.scrollH.get()[0]
        if evt.delta < 0:
            rep = rep + 0.02
        else:
            rep = rep - 0.02
        self.canevas.xview_moveto(rep)
        self.update_minimap_viewport()


    def start_drag(self, event):
        # start canvas panning
        self.canevas.scan_mark(event.x, event.y)
        # update minimap viewport immediately (in case nothing moves yet)
        self.update_minimap_viewport()

    def do_drag(self, event):
        # perform canvas panning
        self.canevas.scan_dragto(event.x, event.y, gain=1)
        # update the rectangle on the minimap that shows the visible area
        self.update_minimap_viewport()

    def update_minimap_viewport(self):

        x_left_frac, x_right_frac = self.canevas.xview()
        y_top_frac, y_bottom_frac = self.canevas.yview()

        x_left_frac = max(0.0, min(1.0, x_left_frac))
        x_right_frac = max(0.0, min(1.0, x_right_frac))
        y_top_frac = max(0.0, min(1.0, y_top_frac))
        y_bottom_frac = max(0.0, min(1.0, y_bottom_frac))

        w = self.tailleminicarte
        h = self.tailleminicarte
        x1 = int(x_left_frac * w)
        x2 = int(x_right_frac * w)
        y1 = int(y_top_frac * h)
        y2 = int(y_bottom_frac * h)

        self.minicarte.delete("viewport")
        self.minicarte.create_rectangle(x1, y1, x2, y2, outline="red", width=3, tags=("viewport",))



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

    def initialiser_avec_modele(self, chargement=False):

        self.canevas.delete("ALL")  # Supprime TOUS les dessins
        self.minicarte.delete("ALL")
        # --- Initialiser conteneur image pour la minimap ---
        self.minicarte_img = self.minicarte.create_image(
            0, 0,
            anchor="nw",
            image=None
        )

        if hasattr(self, 'action'):
            self.action.persochoisi = []
            self.action.ciblechoisi = None
            self.action.prochaineaction = None
        # on reassigne le nom final localement pour eviter
        # de toujours le requerir du parent
        self.nom_joueur_local = self.parent.nom_joueur_local
        # on ajuste la taille du canevas de jeu
        self.canevas.config(scrollregion=(0, 0, self.modele.aireX, self.modele.aireY))
        self.canevasaction.delete("nom")
        self.canevasaction.create_text(100, 30, text=self.nom_joueur_local, font=("arial", 18, "bold"), anchor=S,
                                       tags=("nom"))


        self.canevas.create_rectangle(0, 0, self.modele.aireX, self.modele.aireY,
                                      fill="", outline="",
                                      tags=("fond", "arriere_plan"))
        self.canevas.tag_lower("fond")


        # on cree les cadres affichant les items d'actions du joueur
        # cadre apparaissant si on selectionne un ouvrier
        coul = self.modele.joueurs[self.parent.nom_joueur_local].couleur
        self.cadrejeuinfo.config(bg=coul[1])
        self.creer_aide()
        self.creer_cadre_ouvrier(coul[0] + "_", ["maison", "caserne", "abri", "usineballiste","moulin"])
        self.creer_chatter()
        # on affiche les maisons, point de depart des divers joueurs


        self.afficher_depart(chargement)
        #Fog
        self.fog_overlay = FogOverlay(
            self.canevas,
            self.modele.fog,
            self.modele.taillecase
        )
        self.minimap_renderer = MiniMapRenderer(self.modele, self.tailleminicarte)
        self.minicarte.itemconfigure(self.minicarte_img, image=self.minimap_renderer.tk)
        self.root.update()
        # self.centrer_maison()

    def creer_cadre_ouvrier(self, coul, artefacts):
        # Cadre principal qui contiendra le canvas scrollable
        self.cadreouvrier = Frame(self.canevasaction, bg="goldenrod3", bd=2, relief="ridge")

        # Canvas pour le scroll - IMPORTANT: définir une taille minimale
        self.canvas_ouvrier = Canvas(
            self.cadreouvrier,
            bg="goldenrod3",
            highlightthickness=0,
            width=200,  # Largeur minimale
            height=200  # Hauteur minimale
        )

        # Scrollbar verticale
        self.scrollbar_ouvrier = Scrollbar(
            self.cadreouvrier,
            orient=VERTICAL,
            command=self.canvas_ouvrier.yview
        )
        self.canvas_ouvrier.configure(yscrollcommand=self.scrollbar_ouvrier.set)

        # Frame intérieur qui contiendra les boutons
        self.frame_interieur_ouvrier = Frame(self.canvas_ouvrier, bg="goldenrod3")

        # Placement du canvas et de la scrollbar
        self.canvas_ouvrier.pack(side=LEFT, fill=BOTH, expand=True)
        self.scrollbar_ouvrier.pack(side=RIGHT, fill=Y)

        # Créer une fenêtre dans le canvas pour le frame intérieur
        self.canvas_window_ouvrier = self.canvas_ouvrier.create_window(
            0, 0,
            window=self.frame_interieur_ouvrier,
            anchor=NW
        )

        font = ("arial", 16, "bold")  # Police légèrement réduite pour mieux rentrer
        cols = 2

        img_width = 70
        img_height = 70

        for idx, i in enumerate(artefacts):
            vals = self.parent.trouver_valeurs()
            prix = vals.get(i, {})
            prix_texte = "\n".join(f"{k.capitalize()}: {v}" for k, v in prix.items()) if prix else ""

            row = idx // cols
            col = idx % cols

            cell = Frame(self.frame_interieur_ouvrier, bg="goldenrod3", bd=2, relief="solid")
            cell.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

            img_key = coul + i
            try:
                pil_img = Image.open(os.path.join(os.path.dirname(__file__), "images", img_key + ".png"))
                pil_img = pil_img.resize((img_width, img_height), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(pil_img)
            except Exception:
                tk_img = self.images.get(img_key)

            if tk_img:
                img_label = Label(cell, image=tk_img, bg="goldenrod3")
                img_label.image = tk_img  # Garder une référence
                img_label.grid(row=0, column=0, pady=(2, 2), sticky="ew")

            btn = Button(cell, text=i, bg="goldenrod3", font=font, anchor="center")
            btn.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
            btn.bind("<Button>", self.batir_artefact)

            def on_enter(e, artefact=i, prix_texte=prix_texte):
                txt = f"{artefact}\n{prix_texte}" if prix_texte else artefact
                self.update_action_text(txt)

            def on_leave(e):
                self.update_action_text("")

            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

        # Configuration des colonnes pour qu'elles s'étendent uniformément
        for c in range(cols):
            self.frame_interieur_ouvrier.grid_columnconfigure(c, weight=1)

        self.frame_interieur_ouvrier.update_idletasks()

        # Configurer la région scrollable
        def update_scrollregion(event=None):
            self.canvas_ouvrier.configure(scrollregion=self.canvas_ouvrier.bbox("all"))

        def on_canvas_configure(event):
            # Ajuster la largeur du frame intérieur à celle du canvas
            canvas_width = event.width
            self.canvas_ouvrier.itemconfig(self.canvas_window_ouvrier, width=canvas_width)

        self.frame_interieur_ouvrier.bind("<Configure>", update_scrollregion)
        self.canvas_ouvrier.bind("<Configure>", on_canvas_configure)

        # Appeler une première fois pour initialiser
        self.cadreouvrier.after(100, update_scrollregion)

        # Permettre le scroll avec la molette de la souris
        def on_mousewheel(event):
            self.canvas_ouvrier.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # Activer/désactiver le scroll selon la position de la souris
        def bind_mousewheel(event):
            self.canvas_ouvrier.bind_all("<MouseWheel>", on_mousewheel)

        def unbind_mousewheel(event):
            self.canvas_ouvrier.unbind_all("<MouseWheel>")

        self.cadreouvrier.bind("<Enter>", bind_mousewheel)
        self.cadreouvrier.bind("<Leave>", unbind_mousewheel)

    def handle_batiment_click(self, event):
        tags = self.canevas.gettags(CURRENT)
        if not tags:
            return

        owner = tags[1] if len(tags) > 1 else ""

        # If we have selected units and this is an enemy building, issue an attack before showing info
        if self.action.persochoisi and owner and owner != self.parent.nom_joueur_local:
            self.action.ciblechoisi = tags
            self.action.attaquer()

        self.show_batiment_info(event)

    def show_batiment_info(self, event):



        tags = self.canevas.gettags(CURRENT)
        if not tags:
            return

        owner = tags[1] if len(tags) > 1 else ""
        bat_id = tags[2] if len(tags) > 2 else ""
        montype = tags[4] if len(tags) > 4 else ""

        bat = None
        try:
            if owner in self.modele.joueurs:
                for ttype, d in self.modele.joueurs[owner].batiments.items():
                    if bat_id in d:
                        bat = d[bat_id]
                        break
        except Exception:
            bat = None

        try:
            if hasattr(self, "cadrebatimentinfo") and self.cadrebatimentinfo:
                self.cadrebatimentinfo.destroy()
        except Exception:
            pass

        # create a frame that will fill the entire canevasaction area
        self.cadrebatimentinfo = Frame(self.canevasinfo, bg="lightyellow", bd=2, relief="ridge")
        self.canevasinfo.update_idletasks()
        cw = max(1, int(self.canevasinfo.winfo_width()))
        ch = max(1, int(self.canevasinfo.winfo_height()))
        if cw < 10:
            cw = max(200, self.screen_width // 6)
        if ch < 10:
            ch = max(120, self.screen_height // 8)
        # reduce a little to account for padding/borders
        self.cadrebatimentinfo.configure(width=cw - 8, height=ch - 8)
        # prevent children from resizing the frame so it keeps the intended size
        self.cadrebatimentinfo.pack_propagate(False)
        # pack so the frame is ready if used directly, content labels will expand horizontally
        self.cadrebatimentinfo.pack(fill=BOTH, expand=True, padx=6, pady=6)

        Label(self.cadrebatimentinfo, text=f"{montype.capitalize()}", bg="lightyellow", font=("Arial", 30, "bold")).pack(anchor="w", fill=X, pady=4, padx=6)
        Label(self.cadrebatimentinfo, text=f"Propriétaire : {owner or 'N/A'}", bg="lightyellow" , font=("Arial", 24, "bold")).pack(anchor="w", fill=X, padx=6 , pady=(0,20))

        fontInfo = ("Arial", 20, "normal")
        if bat is not None:
            info_lines = []
            if hasattr(bat, "etat"):
                info_lines.append(f"État : {getattr(bat, 'etat')}")
            if hasattr(bat, "niveau"):
                info_lines.append(f"Niveau : {getattr(bat, 'niveau')}")
            if hasattr(bat, "pv"):
                info_lines.append(f"PV : {getattr(bat, 'pv')}")
            if hasattr(bat, "x") and hasattr(bat, "y"):
                info_lines.append(f"Position : ({getattr(bat, 'x')}, {getattr(bat, 'y')})")

            if info_lines:
                for l in info_lines:
                    Label(self.cadrebatimentinfo, text=l, bg="lightyellow" , font=fontInfo).pack(anchor="w", padx=6)
            else:
                Label(self.cadrebatimentinfo, text="Aucune donnée objet disponible", bg="lightyellow").pack(anchor="w", padx=6, pady=4)
        else:
            Label(self.cadrebatimentinfo, text="Aucune donnée objet disponible", bg="lightyellow").pack(anchor="w", padx=6, pady=4)

        # cadre pour les boutons : Créer unité, Améliorer, Supprimer
        btn_frame = Frame(self.cadrebatimentinfo, bg="lightyellow")
        btn_frame.pack(fill=X, pady=8, padx=6)

        # mapping simple: type de bâtiment -> type d'unité à créer
        type_unit_map = {
            "maison": "ouvrier",
            "caserne": "soldat",
            "abri": "druide",
            "usineballiste": "ballista"
        }

        def create_unit(unit_type):
            if owner != self.parent.nom_joueur_local or not unit_type:
                return
            if bat is not None and hasattr(bat, "x") and hasattr(bat, "y"):
                pos = (getattr(bat, "x"), getattr(bat, "y"))
            else:
                cx = int(self.canevas.canvasx(self.canevas.winfo_width() // 2))
                cy = int(self.canevas.canvasy(self.canevas.winfo_height() // 2))
                pos = (cx, cy)

            action = [self.parent.nom_joueur_local, "creerperso", [unit_type, montype, bat_id, pos]]
            try:
                self.parent.actions_requises.append(action)
            except Exception:
                self.parent.actions_requises = [action]

        def upgrade_batiment():
            pass


        def delete_batiment():
            pass

        # déterminer si ce type de bâtiment permet de créer une unité
        unit_type = type_unit_map.get(montype)
        if unit_type:
            btn_text = f"Créer {unit_type.capitalize()}"
            state_create = NORMAL if owner == self.parent.nom_joueur_local else DISABLED
            try:
                couts_persos = self.parent.trouver_couts_persos()
            except Exception:
                couts_persos = {}
            prix_unite = couts_persos.get(unit_type, {})
            prix_unite_texte = "\n".join(f"{k.capitalize()}: {v}" for k, v in prix_unite.items()) if prix_unite else ""
        else:
            btn_text = "Aucune unité disponible"
            state_create = DISABLED
            prix_unite_texte = ""

        # Use grid for equal spacing and expansion
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)

        create_btn = Button(
            btn_frame,
            text=btn_text,
            command=(lambda t=unit_type: create_unit(t) if t else None),
            state=state_create,
            bg="#d9edf7",
            fg="black",
            font=("Arial", 18, "bold"),
            height=4
        )
        create_btn.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        def on_enter_create(e, texte=prix_unite_texte, nom=unit_type):
            if not nom:
                return
            txt = f"{nom}\n{texte}" if texte else nom
            self.update_action_text(txt)

        def on_leave_create(e):
            self.update_action_text("")

        create_btn.bind("<Enter>", on_enter_create)
        create_btn.bind("<Leave>", on_leave_create)

        # Upgrade button (only for owner and if an ID exists)
        state_upgrade = DISABLED #NORMAL if owner == self.parent.nom_joueur_local and bat_id else
        upgrade_btn = Button(
            btn_frame,
            text="Améliorer",
            command=upgrade_batiment,
            state=state_upgrade,
            bg="#60b140",
            fg="black",
            font=("Arial", 18, "bold"),
            height=4
        )
        upgrade_btn.grid(row=0, column=1, padx=8, sticky="ew")

        # Delete button (only for owner and if an ID exists)
        state_delete = DISABLED #NORMAL if owner == self.parent.nom_joueur_local and bat_id else
        delete_btn = Button(
            btn_frame,
            text="Supprimer",
            command=delete_batiment,
            state=state_delete,
            bg="#C31A1A",
            fg="black",
            font=("Arial", 18, "bold"),
            height=4
        )
        delete_btn.grid(row=0, column=2, padx=(8, 0), sticky="ew")

        # remplacer le contenu de la zone d'actions par ce cadre
        self.canevasinfo.delete("ALL")
        self.canevasinfo.create_window(10, 10, anchor=NW, window=self.cadrebatimentinfo)
        

    ##FONCTIONS D'AFFICHAGES##################################
    def afficher_depart(self, chargement=False):
        self.canevas.delete("statique")
        self.canevas.delete("mobile")
        self.canevas.delete("biotope")
        self.canevas.delete("batiment")
        self.canevas.delete("fog")

        elements_eau_pure = ['eaugrand', 'eaugrand1', 'eaugrand2', 'eaugrand3']

        if chargement:
            # Afficher l'eau depuis self.modele.biotopes
            if "eau" in self.modele.biotopes:
                for id_bio, bio in self.modele.biotopes["eau"].items():
                    if bio.img in elements_eau_pure:
                        tag_layer = "eau_layer"  # Eau pure = tout en bas
                    else:
                        tag_layer = "decoration_eau_layer"  # Décorations = au-dessus de l'eau

                    self.canevas.create_image(bio.x, bio.y, image=self.images[bio.img], anchor=S,
                                              tags=("statique", "", bio.id, "biotope", bio.montype, tag_layer))
        else:
            # Afficher l'eau depuis listebiotopes (nouveau jeu)
            for i in self.modele.listebiotopes:
                if i.montype == "eau":
                    if i.img in elements_eau_pure:
                        tag_layer = "eau_layer"  # Eau pure = tout en bas
                    else:
                        tag_layer = "decoration_eau_layer"  # Décorations = au-dessus de l'eau

                    self.canevas.create_image(i.x, i.y, image=self.images[i.img], anchor=S,
                                              tags=("statique", "", i.id, "biotope", i.montype, tag_layer))

        # Réorganiser les couches seulement si elles existent
        if self.canevas.find_withtag("eau_layer"):
            self.canevas.tag_lower("eau_layer")
        if self.canevas.find_withtag("decoration_eau_layer") and self.canevas.find_withtag("eau_layer"):
            self.canevas.tag_raise("decoration_eau_layer", "eau_layer")

        # Afficher les biotopes (arbres, roches, etc.)
        if chargement:
            # Lors d'un chargement, on récupère les biotopes depuis self.modele.biotopes
            for type_bio in self.modele.biotopes:
                # Sauter l'eau car déjà affichée
                if type_bio == "eau":
                    continue
                for id_bio, bio in self.modele.biotopes[type_bio].items():
                    # Les daims sont mobiles, les autres sont statiques
                    if bio.montype == "daim" or bio.montype == "ours":
                        self.canevas.create_image(bio.x, bio.y, image=self.images[bio.img], anchor=S,
                                                  tags=("mobile", "", bio.id, "biotope", bio.montype, ""))
                    else:
                        self.canevas.create_image(bio.x, bio.y, image=self.images[bio.img], anchor=S,
                                                  tags=("statique", "", bio.id, "biotope", bio.montype, ""))
        else:
            # Nouveau jeu : afficher depuis listebiotopes
            self.modele.listebiotopes.sort(key=lambda c: c.y)
            self.modele.listebiotopes.sort(key=lambda c: c.y)
        for i in self.modele.listebiotopes:
            if i.montype == "eau":
                continue

            if i.montype == "daim" or i.montype == "ours":
                self.canevas.create_image(i.x, i.y, image=self.images[i.img], anchor=S,
                                        tags=("mobile", "", i.id, "biotope", i.montype, ""))
            else:
                self.canevas.create_image(i.x, i.y, image=self.images[i.img], anchor=S,
                                        tags=("statique", "", i.id, "biotope", i.montype, ""))

        self.modele.listebiotopes = []  # Réinitialise la liste après affichage

        # Affichage de la minicarte
        # minitaillecase = int(self.tailleminicarte / self.modele.taillecarte)
        # couleurs = {0: "",
        #             "arbre": "light green",
        #             "eau": "light blue",
        #             "aureus": "tan",
        #             "roche": "gray30",
        #             "marais": "orange"}

        # for i, t in enumerate(self.modele.regions):
        #     if t != "plaine":
        #         for j, c in enumerate(self.modele.regions[t]):
        #             for cle, k in self.modele.regions[t][c].dicocases.items():
        #                 y1 = k.y * minitaillecase
        #                 y2 = y1 + minitaillecase
        #                 x1 = k.x * minitaillecase
        #                 x2 = x1 + minitaillecase
        #                 self.minicarte.create_rectangle(x1, y1, x2, y2, outline="",
        #                                                 fill=couleurs[k.parent.montype])

        # # Affichage des bâtiments sur l'aire de jeu et sur la minicarte
        # px = int(self.tailleminicarte / self.modele.aireX)
        # py = int(self.tailleminicarte / self.modele.aireY)

        # Afficher tous les bâtiments (pour nouveau jeu ET chargement)
        for j in self.modele.joueurs.keys():
            for type_bat in self.modele.joueurs[j].batiments:
                for id_bat, bat in self.modele.joueurs[j].batiments[type_bat].items():
                    coul = self.modele.joueurs[j].couleur[0]
                    # Utiliser l'image appropriée selon le type de bâtiment
                    if hasattr(bat, 'image'):
                        img_key = bat.image
                    else:
                        img_key = coul + "_" + bat.montype

                    self.canevas.create_image(bat.x, bat.y, image=self.images[img_key], anchor=S,
                                              tags=("statique", j, bat.id, "batiment", bat.montype, ""))

                    # # Afficher sur minicarte
                    # coul_mini = self.modele.joueurs[j].couleur[1]
                    # x1 = int((bat.x / self.modele.aireX) * self.tailleminicarte)
                    # y1 = int((bat.y / self.modele.aireY) * self.tailleminicarte)
                    # self.minicarte.create_rectangle(x1 - 2, y1 - 2, x1 + 2, y1 + 2, fill=coul_mini,
                    #                                 tags=(j, bat.id, "artefact", bat.montype))

        self.fusionner_eau_adjacente()

    def fusionner_eau_adjacente(self):
        """
        Fusionne toutes les cases d'eau adjacentes en groupes
        et crée une seule grande image pour chaque groupe
        """
        if "eau" not in self.modele.biotopes:
            print("Aucun biotope d'eau trouvé")
            return

        # TROUVER LA VRAIE TAILLE DE CASE
        # Option 1 : Si votre modèle a une taille de case définie
        if hasattr(self.modele, 'taillecase'):
            taille_case = self.modele.taillecase
        else:
            # Option 2 : Calculer à partir de la grille
            taille_case = self.modele.aireX // self.modele.taillecarte

        print(f"📏 Taille de case détectée : {taille_case}px")

        # Identifier les cases d'eau pure
        elements_eau_pure = ['eaugrand', 'eaugrand1', 'eaugrand2', 'eaugrand3']
        cases_eau = {}

        # Collecter toutes les cases d'eau avec leur position en cases de grille
        for id_bio, bio in self.modele.biotopes["eau"].items():
            if bio.img in elements_eau_pure:
                case_x = bio.x // taille_case
                case_y = bio.y // taille_case
                cases_eau[(case_x, case_y)] = bio

        print(f"💧 {len(cases_eau)} cases d'eau pure trouvées")

        if len(cases_eau) == 0:
            print("⚠️ Aucune case d'eau pure à fusionner")
            return

        # Regrouper les cases adjacentes
        visited = set()
        groupes_eau = []

        def trouver_groupe(start_x, start_y):
            """Trouve toutes les cases adjacentes à partir d'une case de départ"""
            groupe = []
            stack = [(start_x, start_y)]

            while stack:
                x, y = stack.pop()
                if (x, y) in visited or (x, y) not in cases_eau:
                    continue

                visited.add((x, y))
                groupe.append((x, y))

                # Vérifier les 4 directions (haut, bas, gauche, droite)
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    voisin = (x + dx, y + dy)
                    if voisin in cases_eau and voisin not in visited:
                        stack.append(voisin)

            return groupe

        # Créer les groupes
        for case_pos in cases_eau.keys():
            if case_pos not in visited:
                groupe = trouver_groupe(case_pos[0], case_pos[1])
                if groupe:
                    groupes_eau.append(groupe)

        print(f"{len(groupes_eau)} groupes d'eau trouvés")

        # Créer une grande image pour chaque groupe
        for idx, groupe in enumerate(groupes_eau):
            print(f"\nGroupe {idx}: {len(groupe)} cases")

            if len(groupe) == 1:
                print(f"  ⏩ Groupe trop petit, ignoré")
                continue

            # Calculer les dimensions du groupe
            min_x = min(pos[0] for pos in groupe)
            max_x = max(pos[0] for pos in groupe)
            min_y = min(pos[1] for pos in groupe)
            max_y = max(pos[1] for pos in groupe)

            largeur_groupe = (max_x - min_x + 1) * taille_case
            hauteur_groupe = (max_y - min_y + 1) * taille_case

            print(f" Dimensions: {largeur_groupe}x{hauteur_groupe}px")

            # Créer une grande image transparente
            grande_image = Image.new('RGBA', (largeur_groupe, hauteur_groupe), (0, 0, 0, 0))

            # Copier chaque case d'eau dans la grande image
            for case_x, case_y in groupe:
                bio = cases_eau[(case_x, case_y)]

                #TROUVER L'IMAGE - ADAPTER SELON VOTRE STRUCTURE
                # Essayer plusieurs chemins possibles
                chemins_possibles = [
                    os.path.join(os.path.dirname(__file__), f"images/eau/{bio.img}.png"),
                    os.path.join(os.path.dirname(__file__), f"images/{bio.img}.png"),
                    os.path.join(os.path.dirname(__file__), "images", "eau", f"{bio.img}.png"),
                ]

                case_img = None
                for chemin in chemins_possibles:
                    if os.path.exists(chemin):
                        try:
                            case_img = Image.open(chemin).convert('RGBA')
                            break
                        except Exception as e:
                            print(f" Erreur lors du chargement de {chemin}: {e}")

                if case_img is None:
                    print(f" Image introuvable pour {bio.img}")
                    # Créer une image bleue de remplacement
                    case_img = Image.new('RGBA', (taille_case, taille_case), (70, 130, 180, 255))
                else:
                    case_img = case_img.resize((taille_case, taille_case), Image.Resampling.LANCZOS)

                # Calculer la position dans la grande image
                pos_x = (case_x - min_x) * taille_case
                pos_y = (case_y - min_y) * taille_case

                # Coller l'image
                grande_image.paste(case_img, (pos_x, pos_y), case_img)

            # Convertir en PhotoImage pour Tkinter
            photo_grande = ImageTk.PhotoImage(grande_image)

            # Stocker l'image
            self.images[f"eau_fusionnee_{idx}"] = photo_grande

            # Supprimer les anciennes cases individuelles du canvas
            for case_x, case_y in groupe:
                bio = cases_eau[(case_x, case_y)]
                self.canevas.delete(bio.id)

            # Afficher la grande image fusionnée
            pos_centre_x = (min_x * taille_case) + (largeur_groupe // 2)
            pos_centre_y = (min_y * taille_case) + (hauteur_groupe // 2)

            print(f" Placée à ({pos_centre_x}, {pos_centre_y})")

            self.canevas.create_image(
                pos_centre_x, pos_centre_y,
                image=self.images[f"eau_fusionnee_{idx}"],
                anchor=CENTER,
                tags=("statique", "", f"eau_groupe_{idx}", "biotope", "eau", "eau_layer")
            )

        # Forcer l'eau à rester en dessous
        self.canevas.tag_lower("eau_layer")
        print("\nFusion de l'eau terminée")

    def afficher_bio(self, bio):
        bio = self.canevas.create_image(bio.x, bio.y, image=self.images[bio.img],
                                  tags=("statique", "", bio.id, "biotope", bio.montype, ""))
        self.canevas.tag_lower(bio, "fog")

    def afficher_batiment(self, joueur, batiment):
        # Supprime les anciens dessins de ce bâtiment
        self.canevas.delete(batiment.id)

        img_key = batiment.image  # tu l’as sur tes objets

        obj_id = self.canevas.create_image(
            batiment.x,
            batiment.y,
            image=self.images[img_key],
            anchor=S,
            tags=("statique", joueur, batiment.id, "batiment", batiment.montype, "")
        )

        # On place le bâtiment sous le fog (là où les cases sont HIDDEN/KNOWN)
        self.canevas.tag_lower(obj_id, "fog")

        all_tags = ("statique", self.parent.nom_joueur_local, batiment.id, "batiment", batiment.montype,"")
        self.dessiner_barre_vie(batiment, all_tags)

        x0, y0, x2, y2 = self.canevas.bbox(obj_id)
        return [x0, y0, x2, y2]


    def dessiner_barre_vie(self, obj, tagged, offset_x=0, offset_y=-10, largeur=40):
        # offset_x added to shift the health bar horizontally
        life_ratio = getattr(obj, "mana", 0) / max(1, getattr(obj, "mana_max", 1))
        life_ratio = max(0.0, min(1.0, life_ratio))
        current_width = largeur * life_ratio
        color_liferange = "green" if life_ratio > 0.5 else "orange" if life_ratio > 0.2 else "red"

        x_center = obj.x + offset_x
        x_left = x_center - largeur / 2
        x_right = x_center + largeur / 2
        x_fill = x_left + current_width

        y_bottom = obj.y - offset_y
        y_top = y_bottom - 5

        # background bar (gray) then filled portion (colored)
        self.canevas.create_rectangle(x_left, y_top, x_right, y_bottom, fill="gray", tags=tagged, state="disabled")
        self.canevas.create_rectangle(x_left, y_top, x_fill, y_bottom, fill=color_liferange, tags=tagged, state="disabled")


    def afficher_jeu(self):

        # On efface tout ce qui est 'mobile' (un tag)
        self.canevas.delete("mobile")
        self.canevas.delete("batiment")
        self.canevas.delete("path")

        # on se debarrasse des choses mortes (disparues), le id est dans le tag du dessin
        for i in self.modele.ressourcemorte:
            self.canevas.delete(i.id)

        elements_eau_pure = ['eaugrand', 'eaugrand1', 'eaugrand2', 'eaugrand3']

#        for j in self.modele.biotopes["eau"].keys():
#            i = self.modele.biotopes["eau"][j]
#            if i.sprite:
#                tag_layer = "eau_layer"
#                self.canevas.create_image(i.x, i.y, image=self.gifs[i.sprite][i.spriteno],
#                                          tags=("mobile", "", i.id, "biotope", type(i).__name__, tag_layer))
#        #self.canevas.tag_lower("eau_layer")
#
#        for j in self.modele.biotopes["daim"].keys():
#            i = self.modele.biotopes["daim"][j]
#            if i.etat == "mort":
#                self.canevas.create_image(i.x, i.y, image=self.images["daimMORT"],
#                                          tags=("mobile", "", i.id, "biotope", i.montype, ""))
#            else:
#                self.canevas.create_image(i.x, i.y, image=self.images[i.img],
#                                          tags=("mobile", "", i.id, "biotope", i.montype, ""))

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
                if self.modele.case_fog(s.x, s.y) != FogState.VISIBLE:
                    continue
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
                    if self.modele.case_fog(i.x, i.y) != FogState.VISIBLE:
                        continue
                    img_key = i.image if i.image in self.images else "mort"
                    tags = ["mobile", j, k, "perso", p]
                    if getattr(i, "etat", "vivant") != "vivant":
                        tags.append("mort")
                    self.canevas.create_image(i.x, i.y, anchor=S, image=self.images.get(img_key, self.images["mort"]),
                                              tags=tuple(tags))

                    if getattr(i, "etat", "vivant") == "vivant" and k in self.action.persochoisi:
                        all_tags=("mobile", j, p, "perso", type(i).__name__, "persochoisi")
                        self.dessiner_barre_vie(i, all_tags)

                    # dessiner javelots des unitÉs À projectiles
                    if getattr(self.modele.joueurs[j].persos[p][k], "javelots", None):
                        for b in self.modele.joueurs[j].persos[p][k].javelots:
                            self.canevas.create_image(
                                b.x,
                                b.y,
                                image=self.images.get(b.image, self.images.get("mort")),
                                tags=("mobile", j, b.id, "", type(b).__name__, ""))

        # ajuster les choses vivantes dependantes de la partie (mais pas des joueurs)
        for j in self.modele.biotopes["daim"].keys():
            i = self.modele.biotopes["daim"][j]
            if self.modele.case_fog(i.x, i.y) != FogState.VISIBLE:
                continue
            if i.etat == "mort":
                self.canevas.create_image(i.x, i.y, image=self.images["daimMORT"],
                                          tags=("mobile", "", i.id, "biotope", i.montype, ""))
                # tags=("",i.id,"artefact","daim","mobile"))

            else:
                self.canevas.create_image(i.x, i.y, image=self.images[i.img],
                                          tags=("mobile", "", i.id, "biotope", i.montype, ""))
                # tags=("",i.id,"artefact","daim","mobile"))
        for j in self.modele.biotopes["ours"].keys():
            i = self.modele.biotopes["ours"][j]
            if self.modele.case_fog(i.x, i.y) != FogState.VISIBLE:
                continue
            if i.etat == "mort":
                self.canevas.create_image(i.x, i.y, image=self.images["oursMORT"],
                                          tags=("mobile", "", i.id, "biotope", i.montype, ""))
                # tags=("",i.id,"artefact","daim","mobile"))

            else:
                self.canevas.create_image(i.x, i.y, image=self.images[i.img],
                                          tags=("mobile", "", i.id, "biotope", i.montype, ""))
                # tags=("",i.id,"artefact","daim","mobile"))
        # ajuster les choses vivantes dependantes de la partie (mais pas des joueurs)
        for j in self.modele.biotopes["eau"].keys():
            i = self.modele.biotopes["eau"][j]
            if self.modele.case_fog(i.x, i.y) != FogState.VISIBLE:
                continue
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

        self.afficher_batiment_visible()

        # FOG
        self.fog_overlay.update()
        self.minimap_renderer.update()
        self.minicarte.itemconfigure(self.minicarte_img, image=self.minimap_renderer.tk)
        
    






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

        self.update_minimap_viewport()

    def afficher_batiment_visible(self):
        for j, jdata in self.modele.joueurs.items():
            for type_bat, dico_bats in jdata.batiments.items():
                # on laisse 'siteconstruction' géré plus haut dans la fonction
                if type_bat == "siteconstruction":
                    continue

                for bat in dico_bats.values():
                    if j == self.parent.nom_joueur_local:
                        self.afficher_batiment(j, bat)
                    else:
                        state = self.modele.case_fog(bat.x, bat.y)
                        if state == FogState.VISIBLE:
                            self.afficher_batiment(j, bat)
        # Effacer anciens fantômes
        self.canevas.delete("batiment_memory")

        # Afficher les bâtiments connus
        for memo in self.modele.fog_memory.iter_known():
            img = self.images.get(memo.image_key)
            if not img:
                continue

            obj = self.canevas.create_image(
                memo.x, memo.y,
                anchor=S,
                image=img,
                tags=("statique", memo.joueur, memo.id,
                    "batiment", memo.type, "batiment_memory")
            )

            self.canevas.tag_lower(obj, "fog")



    ##### ACTIONS DU JOUEUR #######################################################################

    def annuler_action(self, evt):
        mestags = self.canevas.gettags(CURRENT)

        should_deselect = False
        if not mestags:
            should_deselect = True

        elif mestags:
            if len(mestags) < 5 or mestags[4] == "":
                should_deselect = True
            #if self.action.btnactif:
            #    self.action.btnactif.config(bg="SystemButtonFace")
            #self.action = Action(self)

        if should_deselect:
            if self.action.widgetsactifs:
                if isinstance(self.action.widgetsactifs, list):
                    for widget_id in self.action.widgetsactifs:
                        self.canevasaction.delete(widget_id)
                else:
                    self.canevasaction.delete(self.action.widgetsactifs)

            if self.action.btnactif:
                self.action.btnactif.config(bg="SystemButtonFace")
            self.action = Action(self)

    def clic_jeu(self, evt):
        # Déplacement: toujours prendre les coordonnées du clic, même sur une tuile eau/bois/etc.
        x, y = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
        if self.action.persochoisi:
            self.action.position = [x, y]
            self.action.deplacer()
        else:
            # si aucune sélection, on nettoie l'action courante
            self.annuler_action(evt)

    def fermer_chat(self):
        self.textchat = None
        self.fenchat.destroy()

    def ajouter_selection(self, evt):
        mestags = self.canevas.gettags(CURRENT)
        if not mestags or "mort" in mestags:
            return
        if self.parent.nom_joueur_local == mestags[1]:
            if "ouvrier" == mestags[4]:
                self.action.persochoisi.append(mestags[2])
                self.action.afficher_commande_perso()
            else:
                self.action.persochoisi.append(mestags[2])
        elif self.action.persochoisi != []:
            self.action.ciblechoisi = mestags
            mestags
            self.action.attaquer()

    def forcer_deselection(self, evt):
        print("forcer_deselection appelé - Clic sur le fond")
        if self.action.widgetsactifs:
            if isinstance(self.action.widgetsactifs, list):
                for widget_id in self.action.widgetsactifs:
                    self.canevasaction.delete(widget_id)
            else:
                self.canevasaction.delete(self.action.widgetsactifs)

        if self.action.btnactif:
            self.action.btnactif.config(bg="SystemButtonFace")
        self.action = Action(self)
        print("Désélection forcée terminée")  # DEBUG


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
                tags = self.canevas.gettags(i)
                if self.parent.nom_joueur_local not in tags or "mort" in tags:
                    continue
                self.action.persochoisi.append(tags[2])

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
        if tag[1] == "" and self.action.persochoisi and (tag[4] == "daim" or tag[4] == "ours"):
            self.action.chasser_ressource(tag)
        else:
            print(tag[3])

    def indiquer_position(self, evt):
        tag = self.canevas.gettags(CURRENT)
        #if not tag:
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

        self.update_minimap_viewport()

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
        #if not mestags:
        pos = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
        self.action.construire_batiment(pos)

    def creer_entite(self, evt):
        x, y = evt.x, evt.y
        mestags = self.canevas.gettags(CURRENT)
        if self.parent.nom_joueur_local in mestags and mestags[1] == self.nom_joueur_local:
            if "batiment" in mestags:
                action = None
                if "maison" in mestags:
                    pos = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
                    action = [self.parent.nom_joueur_local, "creerperso", ["ouvrier", mestags[4], mestags[2], pos]]
                elif "caserne" in mestags:
                    pos = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
                    action = [self.parent.nom_joueur_local, "creerperso", ["soldat", mestags[4], mestags[2], pos]]
                elif "abri" in mestags:
                    pos = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
                    action = [self.parent.nom_joueur_local, "creerperso", ["druide", mestags[4], mestags[2], pos]]
                elif "usineballiste" in mestags:
                    pos = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
                    action = [self.parent.nom_joueur_local, "creerperso", ["ballista", mestags[4], mestags[2], pos]]
                if action:
                    self.parent.actions_requises.append(action)
            else:
                return
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
            sorte = self.ciblechoisi[4]
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
        """
        Construit un bâtiment à la position donnée.
        VERSION CORRIGÉE : Vérifie que btnactif et prochaineaction existent
        """
        # Vérifier qu'un bâtiment a été sélectionné pour construction
        if self.btnactif is None or self.prochaineaction is None:
            print("Aucun bâtiment sélectionné pour la construction")
            return

        # Vérifier qu'un ouvrier est sélectionné
        if not self.persochoisi:
            print("Aucun ouvrier sélectionné pour construire")
            return

        # Réinitialiser le bouton
        self.btnactif.config(bg="SystemButtonFace")
        self.btnactif = None

        # Créer l'action de construction
        action = [self.parent.nom_joueur_local, "construirebatiment", [self.persochoisi, self.prochaineaction, pos]]
        self.parent.parent.actions_requises.append(action)

        # Réinitialiser la prochaine action
        self.prochaineaction = None

    def afficher_commande_perso(self):
        self.parent.root.update_idletasks()

        # NE PAS FAIRE pack_forget sur les enfants !

        self.parent.canevasaction.update_idletasks()

        try:
            if self.widgetsactifs:
                self.parent.canevasaction.delete(self.widgetsactifs)
        except Exception:
            pass

        largeur = self.parent.canevasaction.winfo_width()
        hauteur = self.parent.canevasaction.winfo_height()

        if largeur < 10:
            largeur = 250
        if hauteur < 10:
            hauteur = 200

        self.widgetsactifs = self.parent.canevasaction.create_window(
            0, 0,
            window=self.parent.cadreouvrier,
            anchor=NW,
            width=largeur,
            height=hauteur
        )

        self.parent.root.after(50, lambda: self.parent.canvas_ouvrier.configure(
            scrollregion=self.parent.canvas_ouvrier.bbox("all")
        ))

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
        self.config(font=("arial", 25, "bold"))
        self.config(bg="goldenrod3")
        self.config(highlightthickness=2, highlightbackground="goldenrod2")

# a enlever test only
if __name__ == '__main__':
    print("Bienvenue au RTS")
    c = m.Controleur()
    # print("FIN DE PROGRAMME")
