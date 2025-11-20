# modele/fog_memory.py

from dataclasses import dataclass
from typing import Dict
from vue.fog import FogState  # ou modèle.fog si tu veux déplacer FogModel ici


@dataclass
class MemoBatiment:
    id: str
    joueur: str
    type: str
    image_key: str
    x: int
    y: int


class FogMemory:
    """Bâtiments ennemis déjà révélés au moins une fois."""

    def __init__(self, partie):
        self.partie = partie
        self.batiments: Dict[str, MemoBatiment] = {}

    def memoriser_visible(self, joueur_local: str):
        """Appelée à chaque frame après màj du fog."""
        for joueur, jdata in self.partie.joueurs.items():
            # if joueur == joueur_local:
            #     continue

            for dico in jdata.batiments.values():
                for bat in dico.values():
                    state = self.partie.case_fog(bat.x, bat.y)

                    if state == FogState.VISIBLE:
                        # déterminer image_key
                        key = bat.image if hasattr(bat, "image") \
                              else f"{self.partie.joueurs[joueur].couleur[0]}_{bat.montype}"

                        self.batiments[bat.id] = MemoBatiment(
                            id=bat.id,
                            joueur=joueur,
                            type=bat.montype,
                            image_key=key,
                            x=bat.x,
                            y=bat.y
                        )

    def iter_known(self):
        """Retourne les bâtiments mémorisés dont l'emplacement est actuellement FogState.KNOWN"""
        for memo in self.batiments.values():
            if self.partie.case_fog(memo.x, memo.y) == FogState.KNOWN:
                yield memo

    def oublier(self, id_bat):
        """Si un bâtiment est détruit."""
        self.batiments.pop(id_bat, None)
