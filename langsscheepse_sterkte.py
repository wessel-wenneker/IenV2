# -*- coding: utf-8 -*-
"""Berekeningen en grafieken voor de langsscheepse sterkte."""

from __future__ import annotations

from dataclasses import dataclass
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.integrate import cumulative_trapezoid, trapezoid
from scipy.interpolate import CubicSpline, interp1d

from lees_bestanden import DataLoader, leesAntwoordenblad


ZWAARTEKRACHT = 9.81
TOELAATBARE_SPANNING_MPA = 355
ELASTICITEITSMODULUS = 205e9


@dataclass
class EvenwichtsResultaat:
    """Resultaten van de tankverdeling voor verticaal evenwicht."""

    nodig_volume_tank1: float
    nodig_volume_tank2: float
    nodig_volume_tank3: float
    nodig_percentage_tank1: float
    nodig_percentage_tank2: float
    nodig_percentage_tank3: float
    restant_volume: float


@dataclass
class SterkteBrondata:
    """Alle brondata die nodig zijn voor de sterkteberekening."""

    df_buoyant_csa: pd.DataFrame
    df_shell_csa: pd.DataFrame
    df_tank1_csa: pd.DataFrame
    df_tank2_csa: pd.DataFrame
    df_tank3_csa: pd.DataFrame
    df_hull: pd.DataFrame
    df_bhd: pd.DataFrame
    df_tank1_volume: pd.DataFrame
    df_tank2_volume: pd.DataFrame
    df_tank3_volume: pd.DataFrame
    antwoordenblad: dict


@dataclass
class SterkteResultaat:
    """Vat alle grafieklijnen en kengetallen van de sterkte samen."""

    x_fijn: np.ndarray
    verdeelde_belasting_kn_m: np.ndarray
    dwarskrachtlijn_mn: np.ndarray
    momentlijn_mnm: np.ndarray
    traagheidsmoment_lijn: np.ndarray
    buigstijfheid_lijn: np.ndarray
    gereduceerd_moment_lijn: np.ndarray
    sigma_bodem_mpa: np.ndarray
    sigma_dek_mpa: np.ndarray
    hoekverdraaiing_lijn: np.ndarray
    doorbuiging_lijn: np.ndarray
    q_evenwicht: float
    restant_volume: float
    krachtrestant_kn: float
    momentrestant_mnm: float
    max_sigma_bodem_mpa: float
    max_sigma_dek_mpa: float
    toelaatbare_spanning_mpa: float
    max_doorbuiging_mm: float
    max_moment_nm: float
    locatie_max_moment_m: float
    locatie_max_doorbuiging_m: float


def plotLijn(
    x_waarden: np.ndarray,
    y_waarden: np.ndarray,
    x_label: str = "x",
    y_label: str = "y",
    titel: str = "",
    raster: bool = False,
    save_pad=None,
) -> None:
    """Toont of slaat een enkele lijnplot op."""
    plt.figure()
    plt.plot(x_waarden, y_waarden, "k")
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(titel)
    if raster:
        plt.grid()
    if save_pad is not None:
        plt.savefig(save_pad, dpi=150, bbox_inches="tight")
        plt.close()
    else:
        plt.show()


def interpoleerLijn(x_oud: np.ndarray, y_oud: np.ndarray, x_nieuw: np.ndarray) -> np.ndarray:
    """Interpoleert een lijn op een nieuwe x-verdeling."""
    interpolatie = interp1d(x_oud, y_oud)
    binnen_bereik = (x_nieuw >= x_oud[0]) & (x_nieuw <= x_oud[-1])
    begrensde_x = np.clip(x_nieuw, x_oud[0], x_oud[-1])
    return np.where(binnen_bereik, interpolatie(begrensde_x), 0)


def leesSterkteBrondata(bestandscode: list[int]) -> SterkteBrondata:
    """Leest alle CSV- en JSON-bronbestanden voor de sterkte in."""
    data_lader = DataLoader(bestandscode)
    standaard_data = data_lader.laadInputs()
    return SterkteBrondata(
        df_buoyant_csa=data_lader.leesAangepasteCsv("Buoyant_CSA"),
        df_shell_csa=data_lader.leesCsv("Shell_CSA", skiprows=1),
        df_tank1_csa=data_lader.leesCsv("Tank1_CSA", skiprows=1),
        df_tank2_csa=data_lader.leesCsv("Tank2_CSA", skiprows=1),
        df_tank3_csa=data_lader.leesCsv("Tank3_CSA", skiprows=1),
        df_hull=data_lader.leesCsv("HullAreaData", skiprows=1),
        df_bhd=data_lader.leesCsv("TankBHD_Data", skiprows=1),
        df_tank1_volume=standaard_data.df_tank1,
        df_tank2_volume=standaard_data.df_tank2,
        df_tank3_volume=standaard_data.df_tank3,
        antwoordenblad=leesAntwoordenblad(bestandscode),
    )


def voegHalveCirkelLastToe(
    belasting_lijn: np.ndarray,
    x_fijn: np.ndarray,
    x_midden: float,
    straal: float,
    gewicht: float,
) -> None:
    """Voegt een vereenvoudigde halve-cirkel-last toe aan de belastingslijn."""
    x_min_index = np.searchsorted(x_fijn, x_midden - straal)
    x_max_index = np.searchsorted(x_fijn, x_midden + straal)
    hoogte = gewicht / straal / np.pi * 2
    boog = np.linspace(-1, 1, len(belasting_lijn[x_min_index:x_max_index]))
    belasting_lijn[x_min_index:x_max_index] += hoogte * np.sin(np.arccos(boog))


def bepaalTankEvenwicht(
    q_evenwicht: float,
    df_tank1_volume: pd.DataFrame,
    df_tank2_volume: pd.DataFrame,
    df_tank3_volume: pd.DataFrame,
    initieel_volume_tank1: float,
    initieel_volume_tank2: float,
    initieel_volume_tank3: float,
    water_dichtheid: float,
) -> EvenwichtsResultaat:
    """Bepaalt de benodigde tankvulling om de verticale krachten te balanceren."""
    wijziging_volume_tanks = -q_evenwicht / (ZWAARTEKRACHT * water_dichtheid)
    tank1_volumes = df_tank1_volume["Tankvolume [m3]"].to_numpy()
    tank2_volumes = df_tank2_volume["Tankvolume [m3]"].to_numpy()
    tank3_volumes = df_tank3_volume["Tankvolume [m3]"].to_numpy()
    tank1_percentages = df_tank1_volume["Tankfilling [% of h_tank]"].to_numpy()
    tank2_percentages = df_tank2_volume["Tankfilling [% of h_tank]"].to_numpy()
    tank3_percentages = df_tank3_volume["Tankfilling [% of h_tank]"].to_numpy()
    min_volume_tank2 = CubicSpline(tank2_percentages, tank2_volumes)(20)
    wijziging_tank2 = np.clip(
        wijziging_volume_tanks,
        min_volume_tank2 - initieel_volume_tank2,
        tank2_volumes[-1] - initieel_volume_tank2,
    )
    restant_wijziging = wijziging_volume_tanks - wijziging_tank2
    max_wijziging_tank13 = min(tank1_volumes[-1] - initieel_volume_tank1, tank3_volumes[-1] - initieel_volume_tank3)
    min_wijziging_tank13 = max(-initieel_volume_tank1, -initieel_volume_tank3)
    wijziging_tank13 = np.clip(restant_wijziging / 2, min_wijziging_tank13, max_wijziging_tank13)
    nodig_volume_tank1 = initieel_volume_tank1 + wijziging_tank13
    nodig_volume_tank2 = initieel_volume_tank2 + wijziging_tank2
    nodig_volume_tank3 = initieel_volume_tank3 + wijziging_tank13
    return EvenwichtsResultaat(
        nodig_volume_tank1=float(nodig_volume_tank1),
        nodig_volume_tank2=float(nodig_volume_tank2),
        nodig_volume_tank3=float(nodig_volume_tank3),
        nodig_percentage_tank1=float(CubicSpline(tank1_volumes, tank1_percentages)(nodig_volume_tank1)),
        nodig_percentage_tank2=float(CubicSpline(tank2_volumes, tank2_percentages)(nodig_volume_tank2)),
        nodig_percentage_tank3=float(CubicSpline(tank3_volumes, tank3_percentages)(nodig_volume_tank3)),
        restant_volume=float(restant_wijziging - 2 * wijziging_tank13),
    )


def voegSpiegelEnSchottenToe(
    totale_neerwaartse_belasting: np.ndarray,
    x_fijn: np.ndarray,
    brondata: SterkteBrondata,
    schip,
) -> None:
    """Voegt spiegel- en schotgewichten toe aan de belastingslijn."""
    x_spiegel = brondata.df_hull["lca [m]"].iloc[0]
    gewicht_spiegel = brondata.df_hull["Area [m2]"].iloc[0] * 0.010 * schip.materiaal_dichtheid * schip.massa_factor * ZWAARTEKRACHT
    index_spiegel = np.searchsorted(x_fijn, x_spiegel + 0.5)
    totale_neerwaartse_belasting[1:index_spiegel] += gewicht_spiegel / (x_fijn[index_spiegel - 1] - x_fijn[1])
    for _, schot in brondata.df_bhd.iterrows():
        x_min_index = np.searchsorted(x_fijn, schot["x_min [m]"])
        x_max_index = np.searchsorted(x_fijn, schot["x_max [m]"])
        gewicht_schot = schot["BHD Area [m2]"] * 0.010 * schip.materiaal_dichtheid * schip.massa_factor * ZWAARTEKRACHT
        totale_neerwaartse_belasting[x_min_index:x_max_index] += gewicht_schot / (schot["x_max [m]"] - schot["x_min [m]"])


def voegDekladingToe(
    totale_neerwaartse_belasting: np.ndarray,
    x_fijn: np.ndarray,
    antwoordenblad: dict,
    schip,
) -> None:
    """Voegt transition pieces en eventueel een kraanlast toe."""
    sleutel_lijst = list(antwoordenblad["Lading_locaties"].keys())
    for index in range(antwoordenblad["Deklast_transition_pieces"]["Aantal_transition_pieces #[-]"]):
        x_tp = antwoordenblad["Lading_locaties"][sleutel_lijst[index]]["LCG #[m]"]
        voegHalveCirkelLastToe(totale_neerwaartse_belasting, x_fijn, x_tp, 4, 230000 * ZWAARTEKRACHT)
    if schip.kraan_positie is not None:
        x_kraan = antwoordenblad["Zwaartepunten_kraanlast"]["LCG_kraanhuis #[m]"]
        voegHalveCirkelLastToe(totale_neerwaartse_belasting, x_fijn, x_kraan, 1, 230000 * ZWAARTEKRACHT)


def bouwBasisBelasting(brondata: SterkteBrondata, schip) -> dict:
    """Bouwt de eerste neerwaartse en opwaartse belastingverdelingen op."""
    shell = brondata.df_shell_csa
    x_fijn = np.linspace(shell["X [m]"].to_numpy()[0], shell["X [m]"].to_numpy()[-1], 10000)
    shell_thickness_mm = brondata.antwoordenblad["Constructie"]["Huid_en_dek_dikte #[mm]"]
    huid_belasting = interpoleerLijn(
        shell["X [m]"].to_numpy(),
        shell["CROSS SECTION AREA OF SHELL PLATING [m2]"].to_numpy(),
        x_fijn,
    )
    neerwaartse_huid = huid_belasting * schip.materiaal_dichtheid * schip.massa_factor * shell_thickness_mm * ZWAARTEKRACHT
    neerwaartse_tank1 = interpoleerLijn(brondata.df_tank1_csa["x_in_m"].to_numpy(), brondata.df_tank1_csa["crossarea_in_m2"].to_numpy(), x_fijn) * schip.water_dichtheid * ZWAARTEKRACHT
    neerwaartse_tank2 = interpoleerLijn(brondata.df_tank2_csa["x_in_m"].to_numpy(), brondata.df_tank2_csa["crossarea_in_m2"].to_numpy(), x_fijn) * schip.water_dichtheid * ZWAARTEKRACHT
    neerwaartse_tank3 = interpoleerLijn(brondata.df_tank3_csa["x_in_m"].to_numpy(), brondata.df_tank3_csa["crossarea_in_m2"].to_numpy(), x_fijn) * schip.water_dichtheid * ZWAARTEKRACHT
    totale_neerwaartse_belasting = neerwaartse_huid + neerwaartse_tank1 + neerwaartse_tank2 + neerwaartse_tank3
    voegSpiegelEnSchottenToe(totale_neerwaartse_belasting, x_fijn, brondata, schip)
    voegDekladingToe(totale_neerwaartse_belasting, x_fijn, brondata.antwoordenblad, schip)
    opwaartse_belasting_fijn = np.interp(
        x_fijn,
        brondata.df_buoyant_csa["x_in_m"].to_numpy(),
        schip.water_dichtheid * ZWAARTEKRACHT * -brondata.df_buoyant_csa["crossarea_in_m2"].to_numpy(),
    )
    return {
        "x_fijn": x_fijn,
        "neerwaartse_huid": neerwaartse_huid,
        "neerwaartse_tank1": neerwaartse_tank1,
        "neerwaartse_tank2": neerwaartse_tank2,
        "neerwaartse_tank3": neerwaartse_tank3,
        "totale_neerwaartse_belasting": totale_neerwaartse_belasting,
        "opwaartse_belasting_fijn": opwaartse_belasting_fijn,
    }


def bouwGebalanceerdeBelasting(
    brondata: SterkteBrondata,
    schip,
    basis_belasting: dict,
    evenwicht: EvenwichtsResultaat,
) -> np.ndarray:
    """Past de tankbelastingen aan op basis van het berekende evenwicht."""
    initieel_volume_tank1 = trapezoid(brondata.df_tank1_csa["crossarea_in_m2"].to_numpy(), brondata.df_tank1_csa["x_in_m"].to_numpy())
    initieel_volume_tank2 = trapezoid(brondata.df_tank2_csa["crossarea_in_m2"].to_numpy(), brondata.df_tank2_csa["x_in_m"].to_numpy())
    initieel_volume_tank3 = trapezoid(brondata.df_tank3_csa["crossarea_in_m2"].to_numpy(), brondata.df_tank3_csa["x_in_m"].to_numpy())
    factor_tank1 = evenwicht.nodig_volume_tank1 / initieel_volume_tank1 if initieel_volume_tank1 != 0 else 1
    factor_tank2 = evenwicht.nodig_volume_tank2 / initieel_volume_tank2 if initieel_volume_tank2 != 0 else 1
    factor_tank3 = evenwicht.nodig_volume_tank3 / initieel_volume_tank3 if initieel_volume_tank3 != 0 else 1
    totale_neerwaartse_belasting = basis_belasting["neerwaartse_huid"].copy()
    voegSpiegelEnSchottenToe(totale_neerwaartse_belasting, basis_belasting["x_fijn"], brondata, schip)
    totale_neerwaartse_belasting += basis_belasting["neerwaartse_tank1"] * factor_tank1
    totale_neerwaartse_belasting += basis_belasting["neerwaartse_tank2"] * factor_tank2
    totale_neerwaartse_belasting += basis_belasting["neerwaartse_tank3"] * factor_tank3
    voegDekladingToe(totale_neerwaartse_belasting, basis_belasting["x_fijn"], brondata.antwoordenblad, schip)
    return totale_neerwaartse_belasting


def berekenMomentlijn(
    antwoordenblad: dict,
    schip,
    x_fijn: np.ndarray,
    dwarskrachtlijn: np.ndarray,
) -> np.ndarray:
    """Integreert de dwarskrachtlijn en voegt optioneel een kraanmoment toe."""
    momentlijn = cumulative_trapezoid(dwarskrachtlijn, x_fijn, initial=0)
    if schip.kraan_positie is None:
        return momentlijn
    x_kraan = antwoordenblad["Zwaartepunten_kraanlast"]["LCG_kraanhuis #[m]"]
    giek_lengte = antwoordenblad["Kraan_beladingsconditie"]["Kraanboom_lengte #[m]"]
    giek_hoek = math.radians(antwoordenblad["Kraan_beladingsconditie"]["Giekhoek #[graden]"])
    zwenk_hoek = math.radians(antwoordenblad["Kraan_beladingsconditie"]["Zwenkhoek #[graden]"])
    x_last = x_kraan + giek_lengte * math.cos(giek_hoek) * math.cos(zwenk_hoek)
    kraanmoment = 230000 * ZWAARTEKRACHT * (x_last - x_kraan)
    if abs(kraanmoment) > 1e3:
        kraan_index = np.searchsorted(x_fijn, x_kraan)
        momentlijn[kraan_index:] += kraanmoment
    return momentlijn


def berekenSpanningsLijnen(
    brondata: SterkteBrondata,
    x_fijn: np.ndarray,
    momentlijn: np.ndarray,
) -> dict:
    """Berekent I(x), EI(x), sigma(x) en de afgeleide lijnen."""
    shell = brondata.df_shell_csa
    shell_thickness_mm = brondata.antwoordenblad["Constructie"]["Huid_en_dek_dikte #[mm]"]
    traagheidsmoment_lijn = interpoleerLijn(shell["X [m]"].to_numpy(), shell["INERTIA_Y[m4]"].to_numpy() * shell_thickness_mm, x_fijn)
    traagheidsmoment_lijn = np.maximum(traagheidsmoment_lijn, 0.01)
    buigstijfheid_lijn = ELASTICITEITSMODULUS * traagheidsmoment_lijn
    gereduceerd_moment_lijn = np.where(traagheidsmoment_lijn > 0, momentlijn / buigstijfheid_lijn, 0)
    neutrale_as = interpoleerLijn(shell["X [m]"].to_numpy(), shell["CENTROID_Z[m]"].to_numpy(), x_fijn)
    z_kiel = interpoleerLijn(shell["X [m]"].to_numpy(), shell["Z_Keel[m]"].to_numpy(), x_fijn)
    z_dek = interpoleerLijn(shell["X [m]"].to_numpy(), shell["Z_DECK[m]"].to_numpy(), x_fijn)
    sigma_bodem = np.where(traagheidsmoment_lijn > 0, momentlijn * (z_kiel - neutrale_as) / traagheidsmoment_lijn, 0)
    sigma_dek = np.where(traagheidsmoment_lijn > 0, momentlijn * (z_dek - neutrale_as) / traagheidsmoment_lijn, 0)
    geldig_masker = (x_fijn >= shell["X [m]"].to_numpy()[0]) & (x_fijn <= shell["X [m]"].to_numpy()[-2])
    gereduceerd_moment_lijn[~geldig_masker] = 0
    sigma_bodem[~geldig_masker] = 0
    sigma_dek[~geldig_masker] = 0
    return {
        "traagheidsmoment_lijn": traagheidsmoment_lijn,
        "buigstijfheid_lijn": buigstijfheid_lijn,
        "gereduceerd_moment_lijn": gereduceerd_moment_lijn,
        "sigma_bodem_mpa": sigma_bodem / 1e6,
        "sigma_dek_mpa": sigma_dek / 1e6,
    }


def berekenDoorbuiging(
    x_fijn: np.ndarray,
    gereduceerd_moment_lijn: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Integreert de hoekverdraaiing en doorbuiging uit de kappa-lijn."""
    hoekverdraaiing_raw = cumulative_trapezoid(gereduceerd_moment_lijn, x_fijn, initial=0)
    correctie_constante = -trapezoid(hoekverdraaiing_raw, x_fijn) / (x_fijn[-1] - x_fijn[0])
    hoekverdraaiing_lijn = hoekverdraaiing_raw + correctie_constante
    doorbuiging_lijn = cumulative_trapezoid(hoekverdraaiing_lijn, x_fijn, initial=0)
    return hoekverdraaiing_lijn, doorbuiging_lijn


def berekenLangsscheepseSterkte(bestandscode: list[int], schip) -> SterkteResultaat:
    """Berekent alle lijnen en samenvattende waarden voor de langsscheepse sterkte."""
    brondata = leesSterkteBrondata(bestandscode)
    basis_belasting = bouwBasisBelasting(brondata, schip)
    q_evenwicht = trapezoid(basis_belasting["totale_neerwaartse_belasting"], basis_belasting["x_fijn"])
    q_evenwicht += trapezoid(basis_belasting["opwaartse_belasting_fijn"], basis_belasting["x_fijn"])
    evenwicht = bepaalTankEvenwicht(
        q_evenwicht=q_evenwicht,
        df_tank1_volume=brondata.df_tank1_volume,
        df_tank2_volume=brondata.df_tank2_volume,
        df_tank3_volume=brondata.df_tank3_volume,
        initieel_volume_tank1=trapezoid(brondata.df_tank1_csa["crossarea_in_m2"].to_numpy(), brondata.df_tank1_csa["x_in_m"].to_numpy()),
        initieel_volume_tank2=trapezoid(brondata.df_tank2_csa["crossarea_in_m2"].to_numpy(), brondata.df_tank2_csa["x_in_m"].to_numpy()),
        initieel_volume_tank3=trapezoid(brondata.df_tank3_csa["crossarea_in_m2"].to_numpy(), brondata.df_tank3_csa["x_in_m"].to_numpy()),
        water_dichtheid=schip.water_dichtheid,
    )
    neerwaartse_belasting = bouwGebalanceerdeBelasting(brondata, schip, basis_belasting, evenwicht)
    q_gebalanceerd = neerwaartse_belasting + basis_belasting["opwaartse_belasting_fijn"]
    dwarskrachtlijn = cumulative_trapezoid(q_gebalanceerd, basis_belasting["x_fijn"], initial=0)
    momentlijn = berekenMomentlijn(brondata.antwoordenblad, schip, basis_belasting["x_fijn"], dwarskrachtlijn)
    # Corrigeer de momentlijn: voor een vrij-vrij balk geldt M=0 aan beide uiteinden
    lineaire_correctie = momentlijn[-1] * (basis_belasting["x_fijn"] - basis_belasting["x_fijn"][0]) / (basis_belasting["x_fijn"][-1] - basis_belasting["x_fijn"][0])
    momentlijn = momentlijn - lineaire_correctie
    spannings_lijnen = berekenSpanningsLijnen(brondata, basis_belasting["x_fijn"], momentlijn)
    hoekverdraaiing_lijn, doorbuiging_lijn = berekenDoorbuiging(
        basis_belasting["x_fijn"],
        spannings_lijnen["gereduceerd_moment_lijn"],
    )
    scheepslengte = basis_belasting["x_fijn"][-1] - basis_belasting["x_fijn"][0]
    zoek_masker = (basis_belasting["x_fijn"] >= basis_belasting["x_fijn"][0] + 0.1 * scheepslengte)
    zoek_masker &= basis_belasting["x_fijn"] <= basis_belasting["x_fijn"][0] + 0.9 * scheepslengte
    abs_moment = np.abs(momentlijn)
    max_moment_idx = int(np.argmax(abs_moment))
    abs_doorbuiging = np.abs(doorbuiging_lijn)
    max_doorbuiging_idx = int(np.argmax(abs_doorbuiging))
    return SterkteResultaat(
        x_fijn=basis_belasting["x_fijn"],
        verdeelde_belasting_kn_m=q_gebalanceerd / 1000,
        dwarskrachtlijn_mn=dwarskrachtlijn / 1e6,
        momentlijn_mnm=momentlijn / 1e6,
        traagheidsmoment_lijn=spannings_lijnen["traagheidsmoment_lijn"],
        buigstijfheid_lijn=spannings_lijnen["buigstijfheid_lijn"],
        gereduceerd_moment_lijn=spannings_lijnen["gereduceerd_moment_lijn"],
        sigma_bodem_mpa=spannings_lijnen["sigma_bodem_mpa"],
        sigma_dek_mpa=spannings_lijnen["sigma_dek_mpa"],
        hoekverdraaiing_lijn=hoekverdraaiing_lijn,
        doorbuiging_lijn=doorbuiging_lijn,
        q_evenwicht=float(q_evenwicht),
        restant_volume=evenwicht.restant_volume,
        krachtrestant_kn=float(trapezoid(q_gebalanceerd, basis_belasting["x_fijn"]) / 1e3),
        momentrestant_mnm=float(trapezoid(q_gebalanceerd * basis_belasting["x_fijn"], basis_belasting["x_fijn"]) / 1e6),
        max_sigma_bodem_mpa=float(np.max(np.abs(spannings_lijnen["sigma_bodem_mpa"][zoek_masker]))),
        max_sigma_dek_mpa=float(np.max(np.abs(spannings_lijnen["sigma_dek_mpa"][zoek_masker]))),
        toelaatbare_spanning_mpa=TOELAATBARE_SPANNING_MPA,
        max_doorbuiging_mm=float(np.max(np.abs(doorbuiging_lijn[zoek_masker])) * 1000),
        max_moment_nm=float(momentlijn[max_moment_idx]),
        locatie_max_moment_m=float(basis_belasting["x_fijn"][max_moment_idx]),
        locatie_max_doorbuiging_m=float(basis_belasting["x_fijn"][max_doorbuiging_idx]),
    )


def toonSterkteGrafieken(resultaat: SterkteResultaat, save_map=None) -> None:
    """Toont of slaat alle grafieken op die bij de langsscheepse sterkte horen."""
    from pathlib import Path

    BESTANDSNAMEN = [
        "verdeelde_belasting",
        "dwarskrachtenlijn",
        "momentenlijn",
        "traagheidsmoment",
        "buigstijfheid",
        "gereduceerd_moment",
        "buigspanning",
        "hoekverdraaiing",
        "doorbuiging",
    ]

    def _save_pad(index: int):
        if save_map is None:
            return None
        return Path(save_map) / f"{BESTANDSNAMEN[index]}.png"

    plotLijn(
        resultaat.x_fijn,
        resultaat.verdeelde_belasting_kn_m,
        "Lengte [m]",
        "Verdeelde belasting q(x) [kN/m]",
        "Verdeelde belasting q(x)",
        save_pad=_save_pad(0),
    )
    plotLijn(
        resultaat.x_fijn,
        resultaat.dwarskrachtlijn_mn,
        "Lengte [m]",
        "Dwarskracht V(x) [MN]",
        "Dwarskrachtenlijn V(x)",
        raster=True,
        save_pad=_save_pad(1),
    )
    plotLijn(
        resultaat.x_fijn,
        resultaat.momentlijn_mnm,
        "Lengte [m]",
        "Buigend moment M(x) [MNm]",
        "Momentenlijn M(x)",
        raster=True,
        save_pad=_save_pad(2),
    )
    plotLijn(resultaat.x_fijn, resultaat.traagheidsmoment_lijn, "Lengte [m]", "Traagheidsmoment I(x) [m^4]", "Traagheidsmoment I(x)", save_pad=_save_pad(3))
    plotLijn(resultaat.x_fijn, resultaat.buigstijfheid_lijn, "Lengte [m]", "Buigstijfheid EI(x) [Nm^2]", "Buigstijfheid EI(x)", save_pad=_save_pad(4))
    plotLijn(resultaat.x_fijn, resultaat.gereduceerd_moment_lijn, "Lengte [m]", "Gereduceerd moment kappa(x) [1/m]", "Gereduceerd moment kappa(x)", save_pad=_save_pad(5))

    fig_sigma = plt.figure()
    plt.plot(resultaat.x_fijn, resultaat.sigma_bodem_mpa, "b", label="Bodem")
    plt.plot(resultaat.x_fijn, resultaat.sigma_dek_mpa, "r", label="Dek")
    plt.ylim(-800, 500)
    plt.axhline(TOELAATBARE_SPANNING_MPA, color="k", linestyle="--", label=f"sigma_y = {TOELAATBARE_SPANNING_MPA} MPa")
    plt.axhline(-TOELAATBARE_SPANNING_MPA, color="k", linestyle="--")
    plt.xlabel("Lengte [m]")
    plt.ylabel("Buigspanning [MPa]")
    plt.title("Buigspanning dek en bodem over scheepslengte")
    plt.legend()
    plt.grid()
    if _save_pad(6) is not None:
        plt.savefig(_save_pad(6), dpi=150, bbox_inches="tight")
        plt.close(fig_sigma)
    else:
        plt.show()

    plotLijn(resultaat.x_fijn, resultaat.hoekverdraaiing_lijn, "Lengte [m]", "Hoekverdraaiing theta(x) [rad]", "Hoekverdraaiing over scheepslengte", raster=True, save_pad=_save_pad(7))
    plotLijn(resultaat.x_fijn, resultaat.doorbuiging_lijn, "Lengte [m]", "Doorbuiging w(x) [m]", "Doorbuiging over scheepslengte", raster=True, save_pad=_save_pad(8))
