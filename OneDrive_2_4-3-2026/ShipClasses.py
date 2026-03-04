# -*- coding: utf-8 -*-
"""
Created on Fri Feb 27 14:54:01 2026

@author: ellin
"""

from scipy.interpolate import interp1d, CubicSpline
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import random
import math
import os

from functions import Tank, deck, plates, ZCG, matrix_add
from read import DataLoader

class Ship:
    def __init__(self, file, crane_position, jib_length, TP_position, TP_amount, hull_thickness, BHD_thickness, tank3_initial, slewing_angle, jib_angle, TP_mass=230000, water_density=1025, material_density=7850, mass_factor=2.1):
        self.file = file
        self.loader = DataLoader(self.file, base_dir="data")
        self.crane_position = crane_position
        self.jib_length = jib_length
        self.TP_position = TP_position
        self.TP_amount = TP_amount
        self.hull_thickness = hull_thickness
        self.BHD_thickness = BHD_thickness
        self.tank3_initial = tank3_initial
        self.slewing_angle = slewing_angle
        self.jib_angle = jib_angle
        self.TP_mass = TP_mass
        self.water_density = water_density
        self.material_density = material_density
        self.mass_factor = mass_factor
        #main particulars
        self.main_data = self.loader.read_json("MainShipParticulars")

        #dimensions
        self.values = self.loader.read_main_values()
        self.LOA = self.values['LOA']
        self.width = self.values['B']
        self.height = self.values["H"]
        self.LPP = self.values['LPP']
        self.COB = self.values['COB']
        self.COV = self.values['COV']
        self.buoyant_volume = self.values['buoyant_volume']
        self.I = self.values['I_wp']
        
        self.tank1 = Tank(f'data/Tank1_Diagram_Volume_Gr{self.file[0]}_V{self.file[1]}.{self.file[2]}.csv', f'data/Tank1_Diagram_Waterplane_Gr{self.file[0]}_V{self.file[1]}.{self.file[2]}.csv',self.water_density,self.buoyant_volume,self.COV)
        self.tank2 = Tank(f'data/Tank2_Diagram_Volume_Gr{self.file[0]}_V{self.file[1]}.{self.file[2]}.csv', f'data/Tank2_Diagram_Waterplane_Gr{self.file[0]}_V{self.file[1]}.{self.file[2]}.csv',self.water_density,self.buoyant_volume,self.COV)
        self.tank3 = Tank(f'data/Tank3_Diagram_Volume_Gr{self.file[0]}_V{self.file[1]}.{self.file[2]}.csv', f'data/Tank3_Diagram_Waterplane_Gr{self.file[0]}_V{self.file[1]}.{self.file[2]}.csv',self.water_density,self.buoyant_volume,self.COV)
        self.tank3.percentage_filled(tank3_initial)
        
        #mass and COV calculations
        self.deck_data = deck(self.crane_position,self.TP_position,self.TP_mass,self.TP_amount,self.jib_length,self.jib_angle,self.slewing_angle)
        self.plates_data = plates(self.file,self.hull_thickness,self.BHD_thickness,self.material_density,self.mass_factor)
        self.dry_data = matrix_add(self.deck_data,self.plates_data)
        
        self.lM_dry = self.dry_data[0]*(self.dry_data[1]-self.COV[0])
        self.tM_dry = self.dry_data[0]*self.dry_data[2]
        self.dry_mass = sum(self.dry_data[0])
        self.dry_lM = sum(self.lM_dry)
        self.dry_tM = sum(self.tM_dry)
        
        #tank 1 percentage
        self.initial_tM = self.dry_tM+self.tank3.exact_tM
        self.tank1_tM = -self.initial_tM
        self.tank1_percentage = CubicSpline(self.tank1.tM, self.tank1.percentage)(self.tank1_tM)
        self.tank1.percentage_filled(self.tank1_percentage)
        
        #tank 2 percentage
        self.buoyant_mass = self.buoyant_volume*self.water_density
        self.tank2_mass = self.buoyant_mass-(self.dry_mass + self.tank1.exact_mass + self.tank3.exact_mass)
        self.tank2_percentage = CubicSpline(self.tank2.mass, self.tank2.percentage)(self.tank2_mass)
        self.tank2.percentage_filled(self.tank2_percentage)
        
        #tank 2 lcg
        self.buoyant_lM = self.buoyant_mass*(self.COV[0]-self.COB[0])
        self.initial_lM = self.dry_lM + self.buoyant_lM + self.tank1.exact_lM + self.tank3.exact_lM
        self.tank2_lM = -self.initial_lM
        self.tank2_lcg = (self.tank2_lM/self.tank2_mass)+self.COV[0]
        
        #tank arrays
        self.tank_data = [[self.tank1.exact_mass, self.tank2.exact_mass, self.tank3.exact_mass],
                          [self.tank1.exact_lcg, self.tank2.exact_lcg, self.tank3.exact_lcg],
                          [self.tank1.exact_tcg, self.tank2.exact_tcg, self.tank3.exact_tcg],
                          [self.tank1.exact_vcg, self.tank2.exact_vcg, self.tank3.exact_vcg]]
        
        #ship matrix
        self.ship_data = matrix_add(self.dry_data,self.tank_data)
        
        #KB & KG
        self.KB = self.COB[2]
        self.KG = ZCG(self.ship_data[0], self.ship_data[3])
        
        #GM
        self.BM = self.I[0]/self.buoyant_volume-(self.tank1.exact_GG + self.tank2.exact_GG + self.tank3.exact_GG)
        self.GM = self.KB - self.KG + self.BM
        
        print(self.tank1_percentage)
        print(self.tank2_percentage)
        print(self.tank2_lcg)
        print()
        print(self.GM)
        print()
        

#subclasses
class Alleskunner(Ship):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class TransportSchip(Ship):
    def __init__(self, file, TP_position, TP_mass, TP_amount, **kwargs):
        super().__init__(file=file, TP_position=TP_position, TP_mass=TP_mass, 
                         TP_amount=TP_amount, crane_position=None, 
                         jib_length=None, **kwargs)
        
class KraanSchip(Ship):
        def __init__(self, file, crane_position, jib_length, slewing_angle, jib_angle, **kwargs):
            super().__init__(file=file, TP_position=None, TP_mass=0, 
                             TP_amount=0, crane_position=crane_position, 
                             jib_length=jib_length, **kwargs)