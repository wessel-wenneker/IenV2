# -*- coding: utf-8 -*-
"""Klassen die de scheepsconfiguratie en het evenwicht beschrijven."""

from __future__ import annotations

from scipy.interpolate import CubicSpline

from lees_bestanden import DataLoader
from schip_functies import Tank, berekenDeklast, berekenPlaten, berekenZcg, voegMatricesSamen


class Schip:
    """Basisklasse voor de massa- en stabiliteitsgegevens van een schip."""

    def __init__(
        self,
        bestandscode: list[int],
        kraan_positie,
        giek_lengte,
        tp_positie,
        tp_aantal: int,
        hull_thickness,
        bhd_thickness: float,
        tank3_initial: float,
        zwenk_hoek: float,
        giek_hoek: float,
        tp_massa: float = 230000,
        water_dichtheid: float = 1025,
        materiaal_dichtheid: float = 7850,
        massa_factor: float = 2.1,
    ):
        """Initialiseert alle gegevens die nodig zijn voor massa en stabiliteit."""
        self.bestandscode = bestandscode
        self.data_lader = DataLoader(bestandscode)
        self.kraan_positie = kraan_positie
        self.giek_lengte = giek_lengte
        self.tp_positie = tp_positie
        self.tp_aantal = tp_aantal
        self.hull_thickness = hull_thickness
        self.bhd_thickness = bhd_thickness
        self.tank3_initial = tank3_initial
        self.zwenk_hoek = zwenk_hoek
        self.giek_hoek = giek_hoek
        self.tp_massa = tp_massa
        self.water_dichtheid = water_dichtheid
        self.materiaal_dichtheid = materiaal_dichtheid
        self.massa_factor = massa_factor
        self._leesHoofdgegevens()
        self._initialiseerTanks()
        self._berekenDroogschip()
        self._berekenTankvullingen()
        self._stelScheepsgegevensSamen()

    def _leesHoofdgegevens(self) -> None:
        """Leest de hoofdgegevens van het schip in."""
        waarden = self.data_lader.leesHoofdwaarden()
        self.loa = waarden["loa"]
        self.breedte = waarden["breedte"]
        self.hoogte = waarden["hoogte"]
        self.lpp = waarden["lpp"]
        self.cob = waarden["cob"]
        self.cov = waarden["cov"]
        self.drijfvolume = waarden["drijfvolume"]
        self.inertie_watervlak = waarden["inertie_watervlak"]
        self.df_hull = self.data_lader.leesCsv("HullAreaData", skiprows=1)
        self.df_bhd = self.data_lader.leesCsv("TankBHD_Data", skiprows=1)

    def _initialiseerTanks(self) -> None:
        """Leest de tanktabellen in en zet de beginvulling van tank 3."""
        tank_tabellen = self.data_lader.leesAlleTanks()
        self.tank1 = Tank(
            tank_tabellen["tank1"]["volume"],
            tank_tabellen["tank1"]["watervlak"],
            self.water_dichtheid,
            self.drijfvolume,
            self.cov,
        )
        self.tank2 = Tank(
            tank_tabellen["tank2"]["volume"],
            tank_tabellen["tank2"]["watervlak"],
            self.water_dichtheid,
            self.drijfvolume,
            self.cov,
        )
        self.tank3 = Tank(
            tank_tabellen["tank3"]["volume"],
            tank_tabellen["tank3"]["watervlak"],
            self.water_dichtheid,
            self.drijfvolume,
            self.cov,
        )
        self.tank3.zetVullingspercentage(self.tank3_initial)

    def _berekenDroogschip(self) -> None:
        """Berekent de droge massa's en momenten van dek en platen."""
        self.deklast_data = berekenDeklast(
            kraan_positie=self.kraan_positie,
            tp_positie=self.tp_positie,
            tp_massa=self.tp_massa,
            tp_aantal=self.tp_aantal,
            giek_lengte=self.giek_lengte,
            giek_hoek=self.giek_hoek,
            zwenk_hoek=self.zwenk_hoek,
        )
        self.platen_data = berekenPlaten(
            df_hull=self.df_hull,
            df_bhd=self.df_bhd,
            hull_thickness=self.hull_thickness,
            bhd_thickness=self.bhd_thickness,
            material_density=self.materiaal_dichtheid,
            mass_factor=self.massa_factor,
        )
        self.droge_data = voegMatricesSamen(self.deklast_data, self.platen_data)
        self.langsscheeps_moment_droog = self.droge_data[0] * (self.droge_data[1] - self.cov[0])
        self.dwarsmoment_droog = self.droge_data[0] * self.droge_data[2]
        self.droge_massa = float(self.droge_data[0].sum())
        self.droog_l_m = float(self.langsscheeps_moment_droog.sum())
        self.droog_t_m = float(self.dwarsmoment_droog.sum())

    def _berekenTankvullingen(self) -> None:
        """Berekent de evenwichtsvullingen voor de ballasttanks."""
        self.initieel_t_m = self.droog_t_m + self.tank3.exact_dwarsmoment
        self.tank1_dwarsmoment = -self.initieel_t_m
        spline_tank1 = CubicSpline(self.tank1.dwarsmoment, self.tank1.percentage)
        self.tank1_percentage = float(spline_tank1(self.tank1_dwarsmoment))
        self.tank1.zetVullingspercentage(self.tank1_percentage)
        self.drijvende_massa = self.drijfvolume * self.water_dichtheid
        totale_massa = self.droge_massa + self.tank1.exact_massa + self.tank3.exact_massa
        self.tank2_massa = self.drijvende_massa - totale_massa
        spline_tank2 = CubicSpline(self.tank2.massa, self.tank2.percentage)
        self.tank2_percentage = float(spline_tank2(self.tank2_massa))
        self.tank2.zetVullingspercentage(self.tank2_percentage)
        self.drijvend_l_m = self.drijvende_massa * (self.cov[0] - self.cob[0])
        self.initieel_l_m = self.droog_l_m + self.drijvend_l_m
        self.initieel_l_m += self.tank1.exact_langsscheeps_moment + self.tank3.exact_langsscheeps_moment
        self.tank2_langsscheeps_moment = -self.initieel_l_m
        self.tank2_lcg = float((self.tank2_langsscheeps_moment / self.tank2_massa) + self.cov[0])

    def _stelScheepsgegevensSamen(self) -> None:
        """Voegt tank- en droge data samen en berekent de GM."""
        self.tank_data = [
            [self.tank1.exact_massa, self.tank2.exact_massa, self.tank3.exact_massa],
            [self.tank1.exact_lcg, self.tank2.exact_lcg, self.tank3.exact_lcg],
            [self.tank1.exact_tcg, self.tank2.exact_tcg, self.tank3.exact_tcg],
            [self.tank1.exact_vcg, self.tank2.exact_vcg, self.tank3.exact_vcg],
        ]
        self.scheeps_data = voegMatricesSamen(self.droge_data, self.tank_data)
        self.kb = self.cob[2]
        self.kg = berekenZcg(self.scheeps_data[0], self.scheeps_data[3])
        self.bm = self.inertie_watervlak[0] / self.drijfvolume
        self.bm -= self.tank1.exact_gg + self.tank2.exact_gg + self.tank3.exact_gg
        self.gm = self.kb - self.kg + self.bm

    def geefSamenvatting(self) -> dict[str, float]:
        """Geeft de belangrijkste stabiliteitsuitkomsten terug."""
        return {
            "tank1_percentage": self.tank1_percentage,
            "tank2_percentage": self.tank2_percentage,
            "tank2_lcg": self.tank2_lcg,
            "gm": self.gm,
        }


class Alleskunner(Schip):
    """Schiptype waarbij alle optionele lasten tegelijk aanwezig zijn."""

    def __init__(self, **kwargs):
        """Geeft alle parameters direct door aan de basisklasse."""
        super().__init__(**kwargs)


class TransportSchip(Schip):
    """Schiptype zonder kraan, maar met transition pieces op dek."""

    def __init__(self, bestandscode: list[int], tp_positie, tp_massa: float, tp_aantal: int, **kwargs):
        """Initialiseert een transportschip zonder kraanlasten."""
        super().__init__(
            bestandscode=bestandscode,
            tp_positie=tp_positie,
            tp_massa=tp_massa,
            tp_aantal=tp_aantal,
            kraan_positie=None,
            giek_lengte=None,
            **kwargs,
        )


class KraanSchip(Schip):
    """Schiptype met kraan en zonder transition pieces op dek."""

    def __init__(
        self,
        bestandscode: list[int],
        kraan_positie,
        giek_lengte: float,
        zwenk_hoek: float,
        giek_hoek: float,
        **kwargs,
    ):
        """Initialiseert een kraanschip zonder transition pieces."""
        super().__init__(
            bestandscode=bestandscode,
            tp_positie=None,
            tp_massa=0,
            tp_aantal=0,
            kraan_positie=kraan_positie,
            giek_lengte=giek_lengte,
            zwenk_hoek=zwenk_hoek,
            giek_hoek=giek_hoek,
            **kwargs,
        )
