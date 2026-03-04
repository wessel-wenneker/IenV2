# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 15:40:46 2026

@author: ellin
"""
import json
import matplotlib.pyplot as plt
import numpy as np

def score(eigenschappen1, eigenschappen2):
   
   punten_boot1 = np.zeros(len(eigenschappen))
   punten_boot2 = np.zeros(len(eigenschappen))
 
   for i in range(len(eigenschappen)-1):
    
        if eigenschappen1[i] > eigenschappen2[i]:
            punten_boot1[i]=10 
            punten_boot2[i]=6
        else: 
            punten_boot2[i]=10 
            punten_boot1[i]=6
            
   punten_boot1[-1] = sum(punten_boot1[:-1])
   punten_boot2[-1] = sum(punten_boot2[:-1])
    
   return punten_boot1, punten_boot2
    

data1 = json.load(open("Antwoordenblad_Gr98_V1.0.json"))
data2 = json.load(open("Antwoordenblad_Gr98V2.0.json"))

scheeps_weerstand1 = data1["Weerstand_Holtrop_Mennen"]["Totale_weerstand_bij_14_kn #[kN]"]
ladings_gewicht1 = data1["Deklast_transition_pieces"]["Aantal_transition_pieces #[-]"] * data1["Deklast_transition_pieces"]["Gewicht_per_transition_piece #[N]"]
leeg_scheepsgewicht1 = data1["Neerwaartse_krachten"]["Deplacement #[N]"]
Kraan_last1 = data1[ "Kraan_beladingsconditie"]["SWLmax_kraan #[N]"]
eigenschappen1 = [scheeps_weerstand1, ladings_gewicht1, leeg_scheepsgewicht1, Kraan_last1]

scheeps_weerstand2 = data2["Weerstand_Holtrop_Mennen"]["Totale_weerstand_bij_14_kn #[kN]"]
ladings_gewicht2 = data2["Deklast_transition_pieces"]["Aantal_transition_pieces #[-]"] * data1["Deklast_transition_pieces"]["Gewicht_per_transition_piece #[N]"]
leeg_scheepsgewicht2 = data2["Neerwaartse_krachten"]["Deplacement #[N]"]
Kraan_last2 = data2[ "Kraan_beladingsconditie"]["SWLmax_kraan #[N]"]
eigenschappen2 = [scheeps_weerstand2, ladings_gewicht2, leeg_scheepsgewicht2, Kraan_last2]

eigenschappen = ["scheepsweerstand", "Ladinggewicht", "leeg scheepsgewicht", "Kraanlast", "Totaal"]

#punten arrays vullen
punten_boot1, punten_boot2 = score(eigenschappen1, eigenschappen2)



fig, ax = plt.subplots(1, 5, figsize=(20, 5))

x = [0,1]  # twee boten
n = len(eigenschappen)

for i in range(n):
    waarden = [punten_boot1[i], punten_boot2[i]]
    ax[i].bar(x, waarden, color=["darkblue","orange"])
    ax[i].set_title(eigenschappen[i])
    ax[i].set_xticks(x)
    ax[i].set_xticklabels(["Alleskunner 1", "Alleskunner 2"])
    ax[i].grid(axis="y", linestyle="--")

ax[0].set_ylabel("Punten")
plt.tight_layout()
plt.show()

