# -*- coding: utf-8 -*-
"""Inleesfuncties voor de scheepsdata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import pandas as pd


BASIS_DATA_MAP = Path(__file__).resolve().parent / "Data"


@dataclass
class SchipInputData:
    """Bundelt alle standaard invoerbestanden in een object."""

    bestandscode: list[int]
    hoofd_json: dict
    tank_json: dict
    df_hull: pd.DataFrame
    df_bhd: pd.DataFrame
    df_tank1: pd.DataFrame
    df_tank1_wp: pd.DataFrame
    df_tank2: pd.DataFrame
    df_tank2_wp: pd.DataFrame
    df_tank3: pd.DataFrame
    df_tank3_wp: pd.DataFrame
    df_resistance: pd.DataFrame
    drijfvolume_m3: float
    cob_m: list[float]
    hoogte_m: float
    t_moulded_m: float


class DataLoader:
    """Leest JSON- en CSV-bestanden in op basis van groep en versie."""

    def __init__(self, bestandscode: list[int], basis_map: Path | str = BASIS_DATA_MAP):
        """Slaat de bestandscode en basis-map op voor later gebruik."""
        self.bestandscode = bestandscode
        self.basis_map = Path(basis_map)
        self.groep, self.versie, self.subversie = bestandscode
        self.tag = f"Gr{self.groep}_V{self.versie}.{self.subversie}"

    def maakPad(self, stam: str, extensie: str) -> Path:
        """Bouwt het standaard pad voor een bestand op."""
        return self.basis_map / f"{stam}_{self.tag}.{extensie}"

    def leesJson(self, stam: str) -> dict:
        """Leest een JSON-bestand in en geeft een dictionary terug."""
        pad = self.maakPad(stam, "json")
        with pad.open("r", encoding="utf-8") as bestand:
            return json.load(bestand)

    def leesCsv(self, stam: str, skiprows: int = 1) -> pd.DataFrame:
        """Leest een CSV-bestand in en ruimt de kolomnamen op."""
        data_frame = pd.read_csv(
            self.maakPad(stam, "csv"),
            skiprows=skiprows,
            skipinitialspace=True,
            delimiter=",",
        )
        data_frame.columns = data_frame.columns.str.strip()
        return data_frame

    def laadInputs(self) -> SchipInputData:
        """Leest alle standaard invoerbestanden in en bundelt ze."""
        hoofd_json = self.leesJson("MainShipParticulars")
        tank_json = self.leesJson("TankData")
        df_hull = self.leesCsv("HullAreaData", skiprows=1)
        df_bhd = self.leesCsv("TankBHD_Data", skiprows=1)
        df_tank1 = self.leesCsv("Tank1_Diagram_Volume", skiprows=1)
        df_tank1_wp = self.leesCsv("Tank1_Diagram_Waterplane", skiprows=1)
        df_tank2 = self.leesCsv("Tank2_Diagram_Volume", skiprows=1)
        df_tank2_wp = self.leesCsv("Tank2_Diagram_Waterplane", skiprows=1)
        df_tank3 = self.leesCsv("Tank3_Diagram_Volume", skiprows=1)
        df_tank3_wp = self.leesCsv("Tank3_Diagram_Waterplane", skiprows=1)
        df_resistance = self.leesCsv("ResistanceData", skiprows=5)
        volume_data = hoofd_json["VOLUME RELATED DATA (MOULDED)"]
        return SchipInputData(
            bestandscode=self.bestandscode,
            hoofd_json=hoofd_json,
            tank_json=tank_json,
            df_hull=df_hull,
            df_bhd=df_bhd,
            df_tank1=df_tank1,
            df_tank1_wp=df_tank1_wp,
            df_tank2=df_tank2,
            df_tank2_wp=df_tank2_wp,
            df_tank3=df_tank3,
            df_tank3_wp=df_tank3_wp,
            df_resistance=df_resistance,
            drijfvolume_m3=float(volume_data["Buoyant_Volume_m3"]),
            cob_m=volume_data["COB_m"],
            hoogte_m=float(hoofd_json["MAIN DIMENSIONS"]["H_m"]),
            t_moulded_m=float(hoofd_json["DRAUGHT DATA"]["T_moulded_m"]),
        )

    def leesHoofdwaarden(self) -> dict:
        """Leest alleen de hoofdwaarden die de Schip-klasse nodig heeft."""
        hoofd_json = self.leesJson("MainShipParticulars")
        hoofd_afmetingen = hoofd_json["MAIN DIMENSIONS"]
        volume_data = hoofd_json["VOLUME RELATED DATA (MOULDED)"]
        onderwater_data = hoofd_json["DATA OF UNDERWATER AREAS (MOULDED)"]
        return {
            "loa": float(hoofd_afmetingen["Loa_m"]),
            "breedte": float(hoofd_afmetingen["B_m"]),
            "hoogte": float(hoofd_afmetingen["H_m"]),
            "lpp": float(hoofd_afmetingen["Lpp_m"]),
            "cob": volume_data["COB_m"],
            "cov": volume_data["COV_Total_m"],
            "drijfvolume": float(volume_data["Buoyant_Volume_m3"]),
            "inertie_watervlak": onderwater_data["Inertia_WPA_around_COF_m4"],
        }

    def leesAlleTanks(self) -> dict[str, dict[str, pd.DataFrame]]:
        """Leest de volume- en waterlijngegevens van alle tanks in."""
        tanks: dict[str, dict[str, pd.DataFrame]] = {}
        for index in (1, 2, 3):
            tanks[f"tank{index}"] = {
                "volume": self.leesCsv(f"Tank{index}_Diagram_Volume", skiprows=1),
                "watervlak": self.leesCsv(f"Tank{index}_Diagram_Waterplane", skiprows=1),
            }
        return tanks

    def leesAangepasteCsv(self, stam: str, skiprows: int = 1) -> pd.DataFrame:
        """Leest een extra CSV-bestand in dat dezelfde naamstructuur gebruikt."""
        return self.leesCsv(stam, skiprows=skiprows)


def leesAntwoordenblad(
    bestandscode: list[int],
    basis_map: Path | str = BASIS_DATA_MAP,
) -> dict:
    """Leest het antwoordenblad van de opgegeven groep en versie in."""
    groep, versie, subversie = bestandscode
    pad = Path(basis_map) / f"Antwoordenblad_Gr{groep}V{versie}.{subversie}.json"
    with pad.open("r", encoding="utf-8") as bestand:
        return json.load(bestand)
