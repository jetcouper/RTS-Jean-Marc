## - Encoding: UTF-8 -*-

from tkinter import PhotoImage
import os,os.path
from pathlib import Path

# Dossier "images" = aux côtés de ce fichier, peu importe l'IDE ou le CWD
IMAGES_DIR = Path(__file__).resolve().parent / "images"

images={}
def charger_images(chemin=None):
    if chemin==None:
        chemin = os.path.join(os.path.dirname(__file__), "images")

    for i in os.listdir(chemin):
        che=chemin+"\\"+i
        if os.path.isdir(che):
            charger_images(che)
        else:
            nom, ext=os.path.splitext(os.path.basename(i))
            if ".png"==ext:
                    images[nom]=PhotoImage(file=che)
    return images

def charger_gifs():
    gifs = {}
    lesgifs = ["poissons.gif", "marche.gif"]

    base = os.path.join(os.path.dirname(__file__), "images", "GIFS")

    for nom in lesgifs:
        listeimages = []
        testverite = 1
        noindex = 0
        while testverite:
            try:
                img = PhotoImage(file=os.path.join(base, nom), format="gif -index " + str(noindex))
                listeimages.append(img)
                noindex += 1
            except Exception:
                gifs[nom[:-4]] = listeimages
                testverite = 0
    return gifs


if __name__ == '__main__':
    images=charger_images()

    for i in images.keys():
            print(i,images[i])
