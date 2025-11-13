# minimap.py optimisé
import numpy as np
from PIL import Image, ImageTk
from vue.fog import FogState

MINI_COLORS = {
    "plaine": (60, 180, 60),
    "arbre": (20, 120, 20),
    "eau": (40, 80, 200),
    "roche": (120, 120, 120),
    "marais": (100, 150, 100),
    "aureus": (200, 180, 60)
}

class MiniMapRenderer:
    def __init__(self, modele, taille):
        self.modele = modele
        self.taille = taille
        self.case = taille // modele.taillecarte

        # 1) Base map calculée 1 seule fois
        self.base = self._compute_base_map()

        # 2) Fog buffer (np array RGBA)
        self.fog = np.zeros((taille, taille, 4), dtype=np.uint8)

        # Tk image
        self.tk = None

        # Premier rendu fog
        self.update_fog()

    def _compute_base_map(self):
        """Construit une fois pour toutes la minimap sans fog."""
        tc = self.case
        taille = self.taille
        arr = np.zeros((taille, taille, 3), dtype=np.uint8)

        for y in range(self.modele.taillecarte):
            for x in range(self.modele.taillecarte):
                col = MINI_COLORS.get(self.modele.cartecase[y][x].montype, (60, 180, 60))
                arr[y*tc:(y+1)*tc, x*tc:(x+1)*tc] = col

        return arr

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

                self.fog[y*tc:(y+1)*tc, x*tc:(x+1)*tc, :] = (0, 0, 0, alpha)

        # composition : base RGB + fog RGBA
        base_rgba = np.concatenate([
            self.base,
            np.full((self.taille, self.taille, 1), 255, dtype=np.uint8)
        ], axis=2)

        combined = base_rgba.copy()
        alpha = self.fog[..., 3:4] / 255.0
        combined[..., :3] = (1 - alpha) * combined[..., :3]

        im = Image.fromarray(combined.astype(np.uint8), "RGBA")
        self.tk = ImageTk.PhotoImage(im)
