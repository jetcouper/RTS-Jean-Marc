from tkinter import *

class Cadre_test(Frame):
    def __init__(self,vue):
        Frame.__init__(self,vue.root)
        self.nom="JMD"
        self.vue=vue
        self.scrollVaide=Scrollbar(self,orient=VERTICAL)
        self.textaide=Text(self,width=50,height=10,
                            yscrollcommand = self.scrollVaide.set )
        self.scrollVaide.config(command = self.textaide.yview)
        self.textaide.pack(side=LEFT)
        self.scrollVaide.pack(side=LEFT,expand=1, fill=Y)
        montexte=""" je suis celui qui est!
        
        DAns le temps je f^s autre"""
        self.textaide.insert(END, montexte)
        self.textaide.config(state=DISABLED)