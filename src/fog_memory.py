from dataclasses import dataclass
from typing import Dict
from vue.fog import FogState


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
        for jouer_adverse, jdata in self.partie.joueurs.items():
            if jouer_adverse == joueur_local:
                continue

            for type_bat, dico in jdata.batiments.items():
                for bat in dico.values():

                    # → Ignorer les chantiers ou tout objet incomplet
                    if not hasattr(bat, "montype") or not hasattr(bat, "image"):
                        continue

                    fog_state = self.partie.case_fog(bat.x, bat.y)

                    if fog_state == FogState.VISIBLE:
                        img_key = bat.image
                        self.batiments[bat.id] = MemoBatiment(
                            id=bat.id,
                            joueur=jouer_adverse,
                            type=bat.montype,
                            image_key=img_key,
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
