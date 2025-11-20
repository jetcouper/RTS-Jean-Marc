from enum import IntEnum
import tkinter as tk

class FogState(IntEnum):
    HIDDEN = 0   # jamais vu
    KNOWN = 1    # déjà vu, mais pas actuellement dans le champ de vision
    VISIBLE = 2  # dans le champ de vision actuel

class FogModel:
    def __init__(self, largeur_cases, hauteur_cases):
        self.largeur = largeur_cases
        self.hauteur = hauteur_cases
        self.map = [
            [FogState.HIDDEN for _ in range(largeur_cases)]
            for _ in range(hauteur_cases)
        ]
        # pour optimiser les mises à jour côté vue
        self._last_map = [
            [None for _ in range(largeur_cases)]
            for _ in range(hauteur_cases)
        ]


class FogOverlay:
    """
    Gère le dessin du fog sur un Canvas Tkinter.
    On utilise exactement la même grille que Partie.fog.map.
    """
    def __init__(self, canevas: tk.Canvas, fog_model: FogModel, taillecase: int):
        self.canevas = canevas
        self.fog_model = fog_model
        self.taillecase = taillecase

        largeur = fog_model.largeur   # taillecarte
        hauteur = fog_model.hauteur

        # Un id de rectangle par case (y, x)
        self._rects = [
            [None for _ in range(largeur)]
            for _ in range(hauteur)
        ]

        self._init_rects()

    def _init_rects(self):
        """
        Crée une fois tous les rectangles de fog sur la carte.
        Initialement tout est HIDDEN (noir plein).
        """
        tc = self.taillecase
        for y in range(self.fog_model.hauteur):
            for x in range(self.fog_model.largeur):
                x1 = x * tc
                y1 = y * tc
                x2 = x1 + tc
                y2 = y1 + tc
                rid = self.canevas.create_rectangle(
                    x1, y1, x2, y2,
                    fill="black",
                    outline="",
                    tags=("fog",),
                    state="disabled"  # important : laisse passer les clics
                )
                self._rects[y][x] = rid
                # on initialise l'état caché dans _last_map
                self.fog_model._last_map[y][x] = FogState.HIDDEN

    def update(self):
        """
        Synchronise l'affichage avec fog_model.map.
        Ne modifie que les cases dont l'état a changé.
        """
        fog_map = self.fog_model.map
        last = self.fog_model._last_map

        for y in range(self.fog_model.hauteur):
            for x in range(self.fog_model.largeur):
                state = fog_map[y][x]
                if state is last[y][x]:
                    continue  # rien n'a changé

                last[y][x] = state
                rid = self._rects[y][x]

                if state == FogState.VISIBLE:
                    # complètement transparent: on cache le rectangle
                    self.canevas.itemconfigure(
                        rid,
                        state="hidden"
                    )
                elif state == FogState.KNOWN:
                    # brume légère : on voit la map figée
                    self.canevas.itemconfigure(
                        rid,
                        state="disabled",
                        fill="black",
                        stipple="gray50"  # motif pour simuler de la transparence
                    )
                else:  # HIDDEN
                    # totalement noir
                    self.canevas.itemconfigure(
                        rid,
                        state="disabled",
                        fill="black",
                        stipple=""        # plein
                    )



