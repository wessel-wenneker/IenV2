# -*- coding: utf-8 -*-
"""Losse hulpfuncties voor massa-, zwaartepunt- en tankberekeningen."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import CubicSpline


class Tank:
    """Bewaart alle tankgegevens en rekent een gekozen vulling uit."""

    def __init__(
        self,
        df_volume,
        df_watervlak,
        water_dichtheid: float,
        drijfvolume: float,
        cov: list[float],
    ):
        """Zet de tanktabellen om naar arrays die direct gebruikt kunnen worden."""
        self.volume_data = df_volume.copy()
        self.watervlak_data = df_watervlak.copy()
        self.volume_data.columns = self.volume_data.columns.str.strip()
        self.watervlak_data.columns = self.watervlak_data.columns.str.strip()
        self._leesVolumeData(water_dichtheid, cov)
        self._leesWatervlakData(drijfvolume)

    def _leesVolumeData(self, water_dichtheid: float, cov: list[float]) -> None:
        """Vult alle volume-afhankelijke arrays van de tank."""
        self.meter = self.volume_data["Tankfilling [m]"].to_numpy()
        self.percentage = self.volume_data["Tankfilling [% of h_tank]"].to_numpy()
        self.volume = self.volume_data["Tankvolume [m3]"].to_numpy()
        self.lcg = self.volume_data["lcg [m]"].to_numpy()
        self.tcg = self.volume_data["tcg [m]"].to_numpy()
        self.vcg = self.volume_data["vcg [m]"].to_numpy()
        self.massa = self.volume * water_dichtheid
        self.langsscheeps_moment = self.massa * (self.lcg - cov[0])
        self.dwarsmoment = self.massa * self.tcg
        self.volume_data["massa [kg]"] = self.massa
        self.volume_data["langsscheeps_moment [kgm]"] = self.langsscheeps_moment
        self.volume_data["dwarsmoment [kgm]"] = self.dwarsmoment

    def _leesWatervlakData(self, drijfvolume: float) -> None:
        """Vult alle watervlak-afhankelijke arrays van de tank."""
        self.ix = self.watervlak_data["Inertia_x [m4]"].to_numpy()
        self.gg = self.ix / drijfvolume
        self.watervlak_data["gg [m]"] = self.gg

    def zetVullingspercentage(self, percentage: float) -> None:
        """Slaat alle exacte waarden op voor een gegeven vullingspercentage."""
        self.exact_langsscheeps_moment = CubicSpline(self.percentage, self.langsscheeps_moment)(percentage)
        self.exact_dwarsmoment = CubicSpline(self.percentage, self.dwarsmoment)(percentage)
        self.exact_lcg = CubicSpline(self.percentage, self.lcg)(percentage)
        self.exact_tcg = CubicSpline(self.percentage, self.tcg)(percentage)
        self.exact_vcg = CubicSpline(self.percentage, self.vcg)(percentage)
        self.exact_massa = CubicSpline(self.percentage, self.massa)(percentage)
        self.exact_ix = CubicSpline(self.percentage, self.ix)(percentage)
        self.exact_gg = CubicSpline(self.percentage, self.gg)(percentage)


def maakLegeLastMatrix() -> np.ndarray:
    """Maakt een lege 4x0 matrix voor massa en zwaartepunten."""
    return np.empty((4, 0))


def berekenTpLast(tp_positie=None, tp_massa: float = 0, tp_aantal: int = 0) -> np.ndarray:
    """Berekent de totale massa en zwaartepunten van de transition pieces."""
    if tp_positie is None or tp_aantal == 0:
        return maakLegeLastMatrix()
    cargo_massa = tp_aantal * tp_massa
    return np.array(
        [
            [cargo_massa],
            [tp_positie[0]],
            [tp_positie[1]],
            [tp_positie[2]],
        ],
        dtype=float,
    )


def berekenKraanlast(
    kraan_positie=None,
    giek_lengte: float | None = None,
    tp_massa: float = 0,
    giek_hoek: float = 0,
    zwenk_hoek: float = 0,
) -> np.ndarray:
    """Berekent de kraanhuis-, giek- en haaklast als afzonderlijke punten."""
    if kraan_positie is None or giek_lengte is None:
        return maakLegeLastMatrix()
    giek_hoek_rad = math.radians(giek_hoek)
    zwenk_hoek_rad = math.radians(zwenk_hoek)
    kraan_swl = tp_massa / 0.94
    kraanhuis_massa = 0.34 * kraan_swl
    giek_massa = 0.17 * kraan_swl
    last_massa = kraan_swl
    kraanhuis_lcg, kraanhuis_tcg, kraanhuis_vcg = kraan_positie
    giek_lcg = kraanhuis_lcg + (giek_lengte / 2) * math.cos(giek_hoek_rad) * math.cos(zwenk_hoek_rad)
    giek_tcg = kraanhuis_tcg + (giek_lengte / 2) * math.cos(giek_hoek_rad) * math.sin(zwenk_hoek_rad)
    giek_vcg = kraanhuis_vcg + (giek_lengte / 2) * math.sin(giek_hoek_rad)
    last_lcg = kraanhuis_lcg + giek_lengte * math.cos(giek_hoek_rad) * math.cos(zwenk_hoek_rad)
    last_tcg = kraanhuis_tcg + giek_lengte * math.cos(giek_hoek_rad) * math.sin(zwenk_hoek_rad)
    last_vcg = kraanhuis_vcg + giek_lengte * math.sin(giek_hoek_rad)
    return np.array(
        [
            [kraanhuis_massa, giek_massa, last_massa],
            [kraanhuis_lcg, giek_lcg, last_lcg],
            [kraanhuis_tcg, giek_tcg, last_tcg],
            [kraanhuis_vcg, giek_vcg, last_vcg],
        ],
        dtype=float,
    )


def voegMatricesSamen(eerste_matrix: np.ndarray, tweede_matrix: np.ndarray) -> np.ndarray:
    """Voegt twee 4-rijige matrices samen."""
    samengevoegde_rijen = []
    for eerste_rij, tweede_rij in zip(eerste_matrix, tweede_matrix):
        samengevoegde_rijen.append(
            np.concatenate((np.asarray(eerste_rij, dtype=float), np.asarray(tweede_rij, dtype=float)))
        )
    return np.vstack(samengevoegde_rijen)


def berekenDeklast(
    kraan_positie=None,
    tp_positie=None,
    tp_massa: float = 0,
    tp_aantal: int = 0,
    giek_lengte: float | None = None,
    giek_hoek: float = 0,
    zwenk_hoek: float = 0,
) -> np.ndarray:
    """Berekent alle puntlasten die op het dek staan."""
    tp_last = berekenTpLast(tp_positie=tp_positie, tp_massa=tp_massa, tp_aantal=tp_aantal)
    kraan_last = berekenKraanlast(
        kraan_positie=kraan_positie,
        giek_lengte=giek_lengte,
        tp_massa=tp_massa,
        giek_hoek=giek_hoek,
        zwenk_hoek=zwenk_hoek,
    )
    return voegMatricesSamen(kraan_last, tp_last)


def berekenPlaten(
    df_hull,
    df_bhd,
    hull_thickness: np.ndarray,
    bhd_thickness: float,
    material_density: float,
    mass_factor: float,
) -> np.ndarray:
    """Berekent massa en zwaartepunten van rompplaten en schotten."""
    area_hull = df_hull["Area [m2]"].to_numpy()
    lcg_hull = df_hull["lca [m]"].to_numpy()
    tcg_hull = df_hull["tca [m]"].to_numpy()
    vcg_hull = df_hull["vca [m]"].to_numpy()
    massa_hull = area_hull * hull_thickness * material_density * mass_factor
    area_bhd = df_bhd["BHD Area [m2]"].to_numpy()
    lcg_bhd = df_bhd["lcg [m]"].to_numpy()
    tcg_bhd = df_bhd["tcg [m]"].to_numpy()
    vcg_bhd = df_bhd["vcg [m]"].to_numpy()
    massa_bhd = area_bhd * bhd_thickness * material_density * mass_factor
    return np.array(
        [
            np.append(massa_hull, massa_bhd),
            np.append(lcg_hull, lcg_bhd),
            np.append(tcg_hull, tcg_bhd),
            np.append(vcg_hull, vcg_bhd),
        ]
    )


def berekenWeerstand(df_resistance, ontwerp_snelheid: float, toon_plot: bool = False) -> float:
    """Berekent de weerstand bij een ontwerpsnelheid en toont optioneel een plot."""
    snelheid = df_resistance["V [kn]"].to_numpy()[:11]
    weerstand = df_resistance["Rtot [N]"].to_numpy()[:11] / 1000
    ontwerp_weerstand = CubicSpline(snelheid, weerstand)(ontwerp_snelheid)
    if toon_plot:
        plt.plot(snelheid, weerstand, "b")
        plt.title("weerstand")
        plt.xlabel("snelheid [kn]")
        plt.ylabel("weerstand [kN]")
        plt.show()
    return ontwerp_weerstand


def berekenZcg(massa_lijst: np.ndarray, zcg_lijst: np.ndarray) -> float:
    """Berekent het zwaartepunt van een samengestelde massa."""
    moment = np.sum(massa_lijst * zcg_lijst)
    kracht = np.sum(massa_lijst)
    return float(moment / kracht)
