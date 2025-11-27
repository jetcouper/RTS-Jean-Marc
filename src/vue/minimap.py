# minimap.py — version optimisée et vectorisée 100%
import numpy as np
from PIL import Image, ImageTk
from vue.fog import FogState

# Couleurs minimap du terrain
MINI_COLORS = {
    "plaine": (60, 180, 60),
    "arbre": (20, 120, 20),
    "eau": (40, 80, 200),
    "roche": (120, 120, 120),
    "marais": (100, 150, 100),
    "aureus": (200, 180, 60)
}
UNIT_SIZE: int = 5
BUILDING_SIZE: int = 5


class MiniMapRenderer:
    def __init__(self, modele, taille):
        self.modele = modele
        self.taille = taille
        self.case = taille // modele.taillecarte

        # Base map fixe
        self.base = self._compute_base_map()

        # Fog + objets
        self.fog = np.zeros((taille, taille, 4), dtype=np.uint8)
        self.objects = np.zeros((taille, taille, 4), dtype=np.uint8)

        # Pré-calc couleurs joueurs
        self._compute_player_colors()


        # Générer masques pixel-art
        (self.unit_center_mask,
         self.unit_stroke_mask) = self._make_circle_mask(UNIT_SIZE)

        (self.build_center_mask,
         self.build_stroke_mask) = self._make_square_mask(BUILDING_SIZE)

        (self.mem_center_mask,
         self.mem_stroke_mask) = self._make_square_mask(BUILDING_SIZE)

        self.tk = None
        self.update()

    # ---------------------------------------------------------
    #  PRE-CALCULS
    # ---------------------------------------------------------

    def _compute_player_colors(self):
        """Convertit les couleurs Tk en RGB 0–255."""
        import matplotlib.colors as mcolors
        self.player_colors = {}
        for j, data in self.modele.joueurs.items():
            rgb = mcolors.to_rgb(data.couleur[1])
            self.player_colors[j] = tuple(int(c * 255) for c in rgb)

    def _compute_base_map(self):
        tc = self.case
        arr = np.zeros((self.taille, self.taille, 3), dtype=np.uint8)

        for y in range(self.modele.taillecarte):
            for x in range(self.modele.taillecarte):
                col = MINI_COLORS.get(self.modele.cartecase[y][x].montype,
                                      (60, 180, 60))
                arr[y*tc:(y+1)*tc, x*tc:(x+1)*tc] = col

        return arr

    # ---------------------------------------------------------
    #  CREATION DE MASQUES (carré & cercle pixel-art)
    # ---------------------------------------------------------

    def _make_square_mask(self, size: int):
        r = size // 2
        yy, xx = np.mgrid[-r:r+1, -r:r+1]

        stroke = (np.abs(xx) == r) | (np.abs(yy) == r)
        center = ~stroke
        return center, stroke

    def _make_circle_mask(self, size: int):
        r = size // 2
        yy, xx = np.mgrid[-r:r+1, -r:r+1]

        dist2 = xx*xx + yy*yy

        center = dist2 <= (r-1)*(r-1)
        stroke = (dist2 <= r*r) & ~center
        return center, stroke

    # ---------------------------------------------------------
    #  BLIT D'UNE FORME SUR LA MINI-MAP
    # ---------------------------------------------------------

    def _blit_shape(self, cx, cy, color_rgb, center_mask, stroke_mask,
                    stroke_rgb=(20, 20, 20)):
        """Dessine une forme avec masques booléens."""
        h, w = center_mask.shape
        r_y = h // 2
        r_x = w // 2

        y0 = max(0, cy - r_y)
        y1 = min(self.taille, cy + r_y + 1)
        x0 = max(0, cx - r_x)
        x1 = min(self.taille, cx + r_x + 1)

        if y0 >= y1 or x0 >= x1:
            return

        my0 = y0 - (cy - r_y)
        my1 = my0 + (y1 - y0)
        mx0 = x0 - (cx - r_x)
        mx1 = mx0 + (x1 - x0)

        cm = center_mask[my0:my1, mx0:mx1]
        sm = stroke_mask[my0:my1, mx0:mx1]
        sub = self.objects[y0:y1, x0:x1]

        if cm.any():
            sub[cm] = (*color_rgb, 255)

        if sm.any():
            sub[sm] = (*stroke_rgb, 255)

    # ---------------------------------------------------------
    #  HELPER: Vérification des limites de la grille fog
    # ---------------------------------------------------------

    def _is_case_in_bounds(self, case_x, case_y):
        """Vérifie si les coordonnées de case sont dans les limites de la grille."""
        return (0 <= case_x < self.modele.taillecarte and
                0 <= case_y < self.modele.taillecarte)

    # ---------------------------------------------------------
    #  UPDATE : FOG + OBJECTS + COMPOSE
    # ---------------------------------------------------------

    def update(self):
        self.update_fog()
        self.update_objects()
        self._compose()

    # Fog overlay PIL
    def update_fog(self):
        fogmap = self.modele.fog.map
        tc = self.case

        for y in range(self.modele.taillecarte):
            for x in range(self.modele.taillecarte):
                s = fogmap[y][x]

                if s == FogState.VISIBLE:
                    alpha = 0
                elif s == FogState.KNOWN:
                    alpha = 140
                else:
                    alpha = 255

                self.fog[y*tc:(y+1)*tc, x*tc:(x+1)*tc] = (0, 0, 0, alpha)

    # -------- VECTORISÉ (aucune boucle pixel) --------
    def update_objects(self):
        modele = self.modele
        fog = modele.fog.map

        self.objects[:] = 0  # reset

        taille = self.taille
        tc = modele.taillecase
        sx = taille / modele.aireX
        sy = taille / modele.aireY

        players = self.player_colors

        # --- UNITÉS VISIBLES ---
        for joueur, jdata in modele.joueurs.items():
            color = players.get(joueur)
            if color is None:
                continue

            for persos in jdata.persos.values():
                for p in persos.values():

                    case_x = int(p.x // tc)
                    case_y = int(p.y // tc)

                    # ✅ Vérification des limites avant d'accéder à fog
                    if not self._is_case_in_bounds(case_x, case_y):
                        continue

                    if fog[case_y][case_x] != FogState.VISIBLE:
                        continue

                    cx = int(p.x * sx)
                    cy = int(p.y * sy)

                    if 0 <= cx < taille and 0 <= cy < taille:
                        self._blit_shape(
                            cx, cy,
                            color,
                            self.unit_center_mask,
                            self.unit_stroke_mask
                        )

        # --- BÂTIMENTS VISIBLES ---
        for joueur, jdata in modele.joueurs.items():
            color = players.get(joueur)
            if color is None:
                continue

            for type_b, bats in jdata.batiments.items():
                if type_b == "siteconstruction":
                    continue

                for b in bats.values():

                    case_x = int(b.x // tc)
                    case_y = int(b.y // tc)

                    # ✅ Vérification des limites avant d'accéder à fog
                    if not self._is_case_in_bounds(case_x, case_y):
                        continue

                    if fog[case_y][case_x] != FogState.VISIBLE:
                        continue

                    cx = int(b.x * sx)
                    cy = int(b.y * sy)

                    if 0 <= cx < taille and 0 <= cy < taille:
                        self._blit_shape(
                            cx, cy,
                            color,
                            self.build_center_mask,
                            self.build_stroke_mask
                        )

        # --- BÂTIMENTS MEMORISES (KNOWN) ---
        for memo in modele.fog_memory.iter_known():
            # ✅ Vérification que le joueur existe dans player_colors
            color = players.get(memo.joueur)
            if color is None:
                continue

            case_x = int(memo.x // tc)
            case_y = int(memo.y // tc)

            # ✅ Vérification des limites avant d'accéder à fog
            if not self._is_case_in_bounds(case_x, case_y):
                continue

            if fog[case_y][case_x] != FogState.KNOWN:
                continue

            cx = int(memo.x * sx)
            cy = int(memo.y * sy)

            if 0 <= cx < taille and 0 <= cy < taille:
                self._blit_shape(
                    cx, cy,
                    color,
                    self.mem_center_mask,
                    self.mem_stroke_mask
                )

    # ---------------------------------------------------------
    #  COMPOSITION FINALE
    # ---------------------------------------------------------

    def _compose(self):
        base_rgba = np.concatenate(
            (self.base, np.full((self.taille, self.taille, 1), 255, dtype=np.uint8)),
            axis=2
        )

        fog_alpha = self.fog[..., 3:4] / 255.0
        combined = base_rgba.copy()
        combined[..., :3] = (1 - fog_alpha) * combined[..., :3]

        obj_alpha = self.objects[..., 3:4] / 255.0
        combined[..., :3] = (
            obj_alpha * self.objects[..., :3] +
            (1 - obj_alpha) * combined[..., :3]
        )

        im = Image.fromarray(combined.astype(np.uint8), "RGBA")
        self.tk = ImageTk.PhotoImage(im)