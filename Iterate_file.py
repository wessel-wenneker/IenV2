from pathlib import Path
import numpy as np
import os

from main import main, run, toonStabiliteitsSamenvatting, toonSterkteSamenvatting,  schrijfOutputAntwoordenblad
from langsscheepse_sterkte import toonSterkteGrafieken

from input_file import SOORT, BESTANDSCODE

dikte = np.arange(0.008,0.025,0.001) #huiddikte array
i = 1 #tank3 start value
tank3 = np.arange(i,100,1) #tank3 initial array

for d in dikte:
    if main(SOORT,d,i)[1].max_sigma_bodem_mpa > main(SOORT,d,i)[1].toelaatbare_spanning_mpa or main(SOORT,d,i)[1].max_sigma_dek_mpa > main(SOORT,d,i)[1].toelaatbare_spanning_mpa:
        continue
    for i in tank3:
        if main(SOORT,d,i)[0]["tank1_percentage"] < 0 or main(SOORT,d,i)[0]["tank1_percentage"] > 100 or main(SOORT,d,i)[0]["tank2_percentage"] < 0 or main(SOORT,d,i)[0]["tank2_percentage"] > 100 or main(SOORT,d,i)[0]["gm"] < 1:
            continue
        print(round(1000*d), i)
        if not os.path.exists(f'output/{BESTANDSCODE[0]},{BESTANDSCODE[1]},{BESTANDSCODE[2]}/{round(1000*d)},{i}'):
            os.makedirs(f'output/{BESTANDSCODE[0]},{BESTANDSCODE[1]},{BESTANDSCODE[2]}/{round(1000*d)},{i}')
        toonStabiliteitsSamenvatting(main(SOORT,d,i)[2])
        toonSterkteSamenvatting(main(SOORT,d,i)[1])
        schrijfOutputAntwoordenblad(main(SOORT,d,i)[2], main(SOORT,d,i)[1],Path(__file__).resolve().parent / f"output/{BESTANDSCODE[0]},{BESTANDSCODE[1]},{BESTANDSCODE[2]}/{round(1000*d)},{i}")
        toonSterkteGrafieken(main(SOORT,d,i)[1], save_map=Path(__file__).resolve().parent / f"output/{BESTANDSCODE[0]},{BESTANDSCODE[1]},{BESTANDSCODE[2]}/{round(1000*d)},{i}")
        os.path.join(f'output/{BESTANDSCODE[0]},{BESTANDSCODE[1]},{BESTANDSCODE[2]}/{round(1000*d)},{i}', 'info.txt')
        with open(f'output/{BESTANDSCODE[0]},{BESTANDSCODE[1]},{BESTANDSCODE[2]}/{round(1000*d)},{i}/info.txt', "w") as f:
            f.write(f'{round(1000*d)} {i}\n')
            f.write(f'tank1 percentage: {main(SOORT,d,i)[0]["tank1_percentage"]:.1f} %\n')
            f.write(f'tank2 percentage: {main(SOORT,d,i)[0]["tank2_percentage"]:.1f} %\n')
            f.write(f'tank2 lcg: {main(SOORT,d,i)[0]["tank2_lcg"]:.1f} m\n')
            f.write(f'gm: {main(SOORT,d,i)[0]["gm"]:.2f} m\n')
            f.write('\n')
            f.write(f"Max buigspanning bodem: {main(SOORT,d,i)[1].max_sigma_bodem_mpa:.1f} MPa\n")
            f.write(f"Max buigspanning dek: {main(SOORT,d,i)[1].max_sigma_dek_mpa:.1f} MPa\n")
            f.write(f"Toelaatbare spanning: {main(SOORT,d,i)[1].toelaatbare_spanning_mpa} MPa\n")
            f.write(f"Max doorbuiging: {main(SOORT,d,i)[1].max_doorbuiging_mm:.1f} mm\n")
        