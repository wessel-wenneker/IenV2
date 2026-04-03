# -*- coding: utf-8 -*-
"""Hoofdfunctie van het project."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import numpy as np

from langsscheepse_sterkte import ZWAARTEKRACHT, berekenLangsscheepseSterkte, toonSterkteGrafieken
from lees_bestanden import leesAntwoordenblad
from schip_klassen import TransportSchip, KraanSchip, Alleskunner

from input_file import BESTANDSCODE, KRAAN_POSITIE, GIEK_LENGTE, GIEK_HOEK, ZWENK_HOEK, TP_POSITIE, TP_AANTAL

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


def schrijfOutputAntwoordenblad(schip, resultaat,output_map) -> None:
    """Vult het antwoordenblad in met berekende waarden en schrijft het naar output."""
    template = leesAntwoordenblad(BESTANDSCODE)

    template["Stabiliteit"]["GM_aanvangsstabiliteit #[m]"] = round(schip.gm, 4)

    deplacement_n = schip.drijvende_massa * ZWAARTEKRACHT
    lcg_actueel = float(np.sum(schip.scheeps_data[0] * schip.scheeps_data[1]) / np.sum(schip.scheeps_data[0]))
    template["Neerwaartse_krachten"]["Deplacement #[N]"] = round(deplacement_n, 2)
    template["Neerwaartse_krachten"]["LCG #[m]"] = round(lcg_actueel, 4)
    template["Neerwaartse_krachten"]["TCG #[m]"] = 0
    template["Neerwaartse_krachten"]["VCG #[m]"] = round(float(schip.kg), 4)

    template["Opwaartse_krachten"]["Buoyancy #[N]"] = round(deplacement_n, 2)
    template["Opwaartse_krachten"]["LCB #[m]"] = round(schip.cob[0], 4)
    template["Opwaartse_krachten"]["TCB #[m]"] = round(schip.cob[1], 4)
    template["Opwaartse_krachten"]["VCB #[m]"] = round(schip.kb, 4)

    totale_massa = schip.droge_massa + schip.tank1.exact_massa + schip.tank2.exact_massa + schip.tank3.exact_massa
    afwijking_kracht = round((totale_massa - schip.drijvende_massa) * ZWAARTEKRACHT, 2)
    afwijking_moment = round((
        schip.droog_l_m + schip.drijvend_l_m
        + float(schip.tank1.exact_langsscheeps_moment)
        + float(schip.tank2.exact_langsscheeps_moment)
        + float(schip.tank3.exact_langsscheeps_moment)
    ) * ZWAARTEKRACHT, 2)
    template["Evenwichtsafwijkingen"]["Afwijking_verticaal_krachtevenwicht #[N]"] = afwijking_kracht
    template["Evenwichtsafwijkingen"]["Afwijking_longitudinaal_momentevenwicht #[Nm]"] = afwijking_moment
    afwijking_dwars = round((
        float(np.sum(schip.dwarsmoment_droog))
        + float(schip.tank1.exact_dwarsmoment)
        + float(schip.tank2.exact_dwarsmoment)
        + float(schip.tank3.exact_dwarsmoment)
    ) * ZWAARTEKRACHT, 2)
    template["Evenwichtsafwijkingen"]["Afwijking_transversaal_momentevenwicht #[Nm]"] = afwijking_dwars

    template["Sterkte_vanaf_deelopdracht_9"]["Maximaal_moment #[Nm]"] = round(abs(resultaat.max_moment_nm), 2)
    template["Sterkte_vanaf_deelopdracht_9"]["Locatie_max_moment_vanaf_achterloodlijn #[m]"] = round(resultaat.locatie_max_moment_m, 2)
    template["Sterkte_vanaf_deelopdracht_9"]["Maximale_doorbuiging #[m]"] = round(resultaat.max_doorbuiging_mm / 1000, 5)
    template["Sterkte_vanaf_deelopdracht_9"]["Locatie_max_doorbuiging_vanaf_achterloodlijn #[m]"] = round(resultaat.locatie_max_doorbuiging_m, 2)

    output_pad = output_map / "antwoordenblad.json"
    with output_pad.open("w", encoding="utf-8") as bestand:
        json.dump(template, bestand, indent=4, ensure_ascii=False)


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
    resultaat = berekenLangsscheepseSterkte(BESTANDSCODE, schip, dikte,TP_AANTAL,KRAAN_POSITIE,GIEK_LENGTE,GIEK_HOEK,ZWENK_HOEK)
    samenvatting = schip.geefSamenvatting()
    return samenvatting, resultaat, schip


def run(soort, huiddikte, tank3_vulling):
    _,resultaat, schip = main(soort, huiddikte, tank3_vulling)
    toonStabiliteitsSamenvatting(schip)
    toonSterkteSamenvatting(resultaat)
    schrijfOutputAntwoordenblad(schip, resultaat,Path(__file__).resolve().parent / "output")
    toonSterkteGrafieken(resultaat, save_map=Path(__file__).resolve().parent / "output")