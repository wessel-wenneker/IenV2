# -*- coding: utf-8 -*-
"""
Created on Tue Mar  3 17:44:48 2026

@author: ellin
"""

from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import json

@dataclass
class ShipInputs:
    """
    Container (dataclass) waarin alle ingelezen data en enkele 'ready-to-use' velden
    bij elkaar worden gebracht. De Ship class hoeft zo niet overal losse variabelen/dicts/dfs te beheren, 
    alles komt uit één object: inputs.df_hull, inputs.df_tank1, inputs.buoyant_volume_m3, etc.
    """
    file: list[int]
    json_main: dict
    json_tank: dict
    df_hull: pd.DataFrame
    df_BHD: pd.DataFrame
    df_tank1: pd.DataFrame
    df_tank1_wp: pd.DataFrame
    df_tank2: pd.DataFrame
    df_tank2_wp: pd.DataFrame
    df_tank3: pd.DataFrame
    df_tank3_wp: pd.DataFrame

    # handige “ready-to-use” velden:
    buoyant_volume_m3: float
    COB_m: list[float]   # [lcg, tcg, vcg]
    H_m: float
    T_moulded_m: float

class DataLoader:
    """
   DataLoader is verantwoordelijk voor:
   - opbouwen van paden naar bestanden op basis van stem + tag
   - inlezen van JSON bestanden
   - inlezen van CSV bestanden (met opschonen van kolomnamen)
   - bundelen van alle ingelezen data in een ShipInputs object
   """
    def __init__(self, file, base_dir="data"):
        """
       file : list[int]
           Bijvoorbeeld [98, 1, 0] -> Gr98_V1.0
       base_dir : str
           Map waar de data-bestanden staan.
       """
        self.file = file
        self.base = Path(base_dir)                                  #omzetten base_dir naar een Path-object
        self.group, self.vmax, self.vmin = file                     #splitsen file in groep, versie en subversie
        self.tag = f"Gr{self.group}_V{self.vmax}.{self.vmin}"       #bouwen van de 'tag' die in elke bestandsnaam zit

    def path(self, stem: str, ext: str):
        """
        Bouwt het volledige pad naar een bestand.
        stem : str
            Het vaste beginstuk van de bestandsnaam.
            Voorbeeld: "MainShipParticulars", "Tank1_Diagram_Volume"
        ext : str
            De extensie zonder punt: "json" of "csv"
        Returns:
        Path
            Bijvoorbeeld:
            data/MainShipParticulars_Gr98_V1.0.json
        """
        return self.base / f"{stem}_{self.tag}.{ext}"

    def read_json(self, stem):
        """
        Leest een JSON-bestand in als Python dict.
        stem : str
            Basisnaam van het bestand (zonder extensie)
        Returns:
        Inhoud van de JSON als dictionary.
        """
        with open(self.path(stem, "json"), "r", encoding="utf-8") as f:  #'r'--> read
            return json.load(f)

    def read_csv(self, stem, skiprows=1):
        """
        Leest een csv-bestand in als pandas DataFrame.
        Het pad wordt automatisch opgebouwd op basis van een basisdirectory (hier: 'data'), de huige file-configuratie en de gegeven stem.
        """
        df = pd.read_csv(self.path(stem, "csv"), skiprows=skiprows, skipinitialspace=True, delimiter=',')
        df.columns = df.columns.str.strip()     #spaties kolomnamen verwijderen
        return df

    def load_inputs(self) -> ShipInputs:
        """
        Laadt alle benodigde bestanden in en bundelt deze in één ShipInputs-object.
        """
        json_main = self.read_json("MainShipParticulars")
        json_tank = self.read_json("TankData")
        df_hull = self.read_csv("HullAreaData", skiprows=1)
        df_BHD  = self.read_csv("TankBHD_Data", skiprows=1)
        df_tank1 = self.read_csv("Tank1_Diagram_Volume", skiprows=1)
        df_tank1_wp = self.read_csv("Tank1_Diagram_Waterplane", skiprows=1)
        df_tank2 = self.read_csv("Tank2_Diagram_Volume", skiprows=1)
        df_tank2_wp = self.read_csv("Tank2_Diagram_Waterplane", skiprows=1)
        df_tank3 = self.read_csv("Tank3_Diagram_Volume", skiprows=1)
        df_tank3_wp = self.read_csv("Tank3_Diagram_Waterplane", skiprows=1)
        
        buoyant_volume = float(json_main["VOLUME RELATED DATA (MOULDED)"]["Buoyant_Volume_m3"])
        COB = json_main["VOLUME RELATED DATA (MOULDED)"]["COB_m"]
        H_m = float(json_main["MAIN DIMENSIONS"]["H_m"])
        T_m = float(json_main["DRAUGHT DATA"]["T_moulded_m"])

        return ShipInputs(
            file=self.file,
            json_main=json_main,
            json_tank=json_tank,
            df_hull=df_hull,
            df_BHD=df_BHD,
            df_tank1=df_tank1,
            df_tank1_wp=df_tank1_wp,
            buoyant_volume_m3=buoyant_volume,
            COB_m=COB,
            H_m=H_m,
            T_moulded_m=T_m,
            df_tank2=df_tank2,
            df_tank2_wp=df_tank2_wp,
            df_tank3=df_tank3,
            df_tank3_wp=df_tank3_wp
        )
    
    def read_main_values(self):
        """
        Leest het JSON-bestand met hoofdgegevens van het schip
        en geeft alleen relevante waarden voor de class terug.
        """
        d = self.read_json("MainShipParticulars")
        main = d["MAIN DIMENSIONS"]
        vol  = d["VOLUME RELATED DATA (MOULDED)"]
        uw   = d["DATA OF UNDERWATER AREAS (MOULDED)"]
        
        #Geef alleen maar relevante waarden terug in een compacte dictionary
        return {
            "LOA": float(main["Loa_m"]),
            "B": float(main["B_m"]),
            "H": float(main["H_m"]),
            "LPP": float(main["Lpp_m"]),
            "COB": vol["COB_m"],
            "COV": vol["COV_Total_m"],
            "buoyant_volume": float(vol["Buoyant_Volume_m3"]),
            "I_wp": uw["Inertia_WPA_around_COF_m4"],
        }

    def read_all_tanks(self):
        """
        Leest de volume- en waterplane-tabellen van alle drie de tanks.
        """
        tanks = {}

        for i in [1, 2, 3]:
            df_vol = self.read_csv(f"Tank{i}_Diagram_Volume", skiprows=1)
            df_wp  = self.read_csv(f"Tank{i}_Diagram_Waterplane", skiprows=1)

            tanks[f"tank{i}"] = {
                "volume": df_vol,
                "wp": df_wp
            }

        return tanks