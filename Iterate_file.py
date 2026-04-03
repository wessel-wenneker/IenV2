from pathlib import Path
import numpy as np
import os

from main import main, run, toonStabiliteitsSamenvatting, toonSterkteSamenvatting,  schrijfOutputAntwoordenblad
from langsscheepse_sterkte import toonSterkteGrafieken

from input_file import SOORT

dikte = np.arange(0.001,0.025,0.001) #huiddikte array
i = 1 #tank3 start value
tank3 = np.arange(i,101,1) #tank3 initial array

for d in dikte:
    if main(SOORT,d,i)[1].max_sigma_bodem_mpa > main(SOORT,d,i)[1].toelaatbare_spanning_mpa or main(SOORT,d,i)[1].max_sigma_dek_mpa > main(SOORT,d,i)[1].toelaatbare_spanning_mpa:
        continue
    for i in tank3:
        if main(SOORT,d,i)[0]["tank1_percentage"] < 0 or main(SOORT,d,i)[0]["tank1_percentage"] > 100 or main(SOORT,d,i)[0]["tank2_percentage"] < 0 or main(SOORT,d,i)[0]["tank2_percentage"] > 100 or main(SOORT,d,i)[0]["gm"] < 0:
            continue
        print(round(d,5), i)
        if not os.path.exists(f'output/{round(d,5)},{i}'):
            os.makedirs(f'output/{round(d,5)},{i}')
        toonStabiliteitsSamenvatting(main(SOORT,d,i)[2])
        toonSterkteSamenvatting(main(SOORT,d,i)[1])
        schrijfOutputAntwoordenblad(main(SOORT,d,i)[2], main(SOORT,d,i)[1],Path(__file__).resolve().parent / f"output/{round(d,5)},{i}")
        toonSterkteGrafieken(main(SOORT,d,i)[1], save_map=Path(__file__).resolve().parent / f"output/{round(d,5)},{i}")
        