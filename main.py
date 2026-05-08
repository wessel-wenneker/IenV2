# -*- coding: utf-8 -*-
"""Hoofdfunctie van het project."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import numpy as np

from langsscheepse_sterkte import ZWAARTEKRACHT, berekenLangsscheepseSterkte, toonSterkteGrafieken
from schip_klassen import TransportSchip, KraanSchip, Alleskunner

from input_file import BESTANDSCODE, KRAAN_POSITIE, GIEK_LENGTE, GIEK_HOEK, ZWENK_HOEK, TP_POSITIE, TP_SPOSITIE, TP_AANTAL

MASSA_FACTOR = 2.1
MATERIAAL_DICHTHEID = 7850
WATER_DICHTHEID = 1025
TP_MASSA = 230000

def toonStabiliteitsSamenvatting(schip) -> None:
    """Print de belangrijkste stabiliteitsuitkomsten buiten de klassen."""
    samenvatting = schip.geefSamenvatting()
    print(f'tank1 percentage: {samenvatting["tank1_percentage"]:.1f} %')
    print(f'tank2 percentage: {samenvatting["tank2_percentage"]:.1f} %')
    print(f'tank2 lcg: {samenvatting["tank2_lcg"]:.1f} m')
    print(f'gm: {samenvatting["gm"]:.2f} m')
    print()


def toonSterkteSamenvatting(resultaat) -> None:
    """Print de belangrijkste sterkte-uitkomsten buiten de rekendelen."""
    print(f"Max buigspanning bodem: {resultaat.max_sigma_bodem_mpa:.1f} MPa")
    print(f"Max buigspanning dek: {resultaat.max_sigma_dek_mpa:.1f} MPa")
    print(f"Toelaatbare spanning: {resultaat.toelaatbare_spanning_mpa} MPa")
    print(f"Max doorbuiging: {resultaat.max_doorbuiging_mm:.1f} mm")
    print()
    print()

def main(soort, dikte, tank3) -> None:
    """Voert de volledige standaardberekening uit."""
    TANK3_INITIEEL = tank3
    HUIDDIKTE = np.array([0.010, dikte, dikte])
    BHD_DIKTE = 0.010
    if soort == 'transportschip':
        schip = TransportSchip(
                bestandscode=BESTANDSCODE,
                tp_positie=TP_POSITIE,
                tp_massa=TP_MASSA,
                tp_aantal=TP_AANTAL,
                hull_thickness=HUIDDIKTE,
                bhd_thickness=BHD_DIKTE,
                tank3_initial=TANK3_INITIEEL,
                zwenk_hoek=ZWENK_HOEK,
                giek_hoek=GIEK_HOEK,
                water_dichtheid=WATER_DICHTHEID,
                materiaal_dichtheid=MATERIAAL_DICHTHEID,
                massa_factor=MASSA_FACTOR)
    elif soort == 'kraanschip':
        schip = KraanSchip(
                bestandscode=BESTANDSCODE,
                kraan_positie=KRAAN_POSITIE,
                hull_thickness=HUIDDIKTE,
                bhd_thickness=BHD_DIKTE,
                tank3_initial=TANK3_INITIEEL,
                zwenk_hoek=ZWENK_HOEK,
                giek_hoek=GIEK_HOEK,
                giek_lengte=GIEK_LENGTE,
                water_dichtheid=WATER_DICHTHEID,
                materiaal_dichtheid=MATERIAAL_DICHTHEID,
                massa_factor=MASSA_FACTOR)
    else:
        schip = Alleskunner(
                bestandscode=BESTANDSCODE,
                kraan_positie=KRAAN_POSITIE,
                tp_positie=TP_POSITIE,
                tp_massa=TP_MASSA,
                tp_aantal=TP_AANTAL,
                hull_thickness=HUIDDIKTE,
                bhd_thickness=BHD_DIKTE,
                tank3_initial=TANK3_INITIEEL,
                zwenk_hoek=ZWENK_HOEK,
                giek_hoek=GIEK_HOEK,
                giek_lengte=GIEK_LENGTE,
                water_dichtheid=WATER_DICHTHEID,
                materiaal_dichtheid=MATERIAAL_DICHTHEID,
                massa_factor=MASSA_FACTOR)
    resultaat = berekenLangsscheepseSterkte(BESTANDSCODE, schip, dikte,TP_SPOSITIE,TP_AANTAL,KRAAN_POSITIE,GIEK_LENGTE,GIEK_HOEK,ZWENK_HOEK)
    samenvatting = schip.geefSamenvatting()
    return samenvatting, resultaat, schip


def run(soort, huiddikte, tank3_vulling):
    _,resultaat, schip = main(soort, huiddikte, tank3_vulling)
    toonStabiliteitsSamenvatting(schip)
    toonSterkteSamenvatting(resultaat)
    toonSterkteGrafieken(resultaat, save_map=Path(__file__).resolve().parent / "output")