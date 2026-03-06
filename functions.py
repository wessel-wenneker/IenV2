# -*- coding: utf-8 -*-
"""
Created on Tue Mar  3 18:01:05 2026

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
from read import ShipInputs

class Tank:
    """
    Berekent alle benodigde waardes van een tank
    
    Parameters:
    df_volume (df): 
        tankeigenschappen bij verschillende vullingen
    df_wp (df): 
        eigenschappen van het wateroppervlak in een tank
    water_density (int): 
        waterdichtheid
    boyant_volume (flt): 
        drijvend volume
    COV (arr):
        lcg tcg en vcg van het onderwatervolume 
        
    Attributes:
    volume_data (df): 
        Kopie van df_volume, aangevuld met massa, lM en tM
    waterplane_data (df): 
        Kopie van df_wp, aangevuld met GG
    meter (array): 
            Vullingshoogte in meters.
    percentage (array):
        Vullingsgraad in procent van de tankhoogte
    volume : array
        Tankvolume per vullingshoogte
    lcg, tcg, vcg : ndarray
        Zwaartepuntcoördinaten per vullingshoogte
    mass : array
        Massa van de tankinhoud per vullingshoogte
    lM : array
        Longitudinaal moment m * (lcg - COV_x)
    tM : array
        Transversaal moment m * tcg
    Ix : array
        Waterlijntraagheidsmoment rond de x-as
    GG : array
        Metacentrische afstand GG = Ix / buoyant_volume

    Attributes created by percentage_filled

    exact_lM, exact_tM : float
        Exacte longitudinale en transversale momenten bij gegeven vullingsgraad
    exact_lcg, exact_tcg, exact_vcg : float
        Exacte zwaartepuntcoördinaten bij gegeven vullingsgraad
    exact_mass : float
        Exacte massa bij gegeven vullingsgraad
    exact_Ix : float
        Exact waterlijntraagheidsmoment bij gegeven vullingsgraad
    exact_GG : float
        Exacte afstand bij gegeven vullingsgraad

    """
    def __init__(self, df_volume, df_wp, water_density, buoyant_volume, COV):
        #data
        self.volume_data = df_volume.copy()
        self.waterplane_data = df_wp.copy()
        self.volume_data.columns = self.volume_data.columns.str.strip()
        self.waterplane_data.columns = self.waterplane_data.columns.str.strip()
        
        #volume data
        self.meter = self.volume_data['Tankfilling [m]'].to_numpy()
        self.percentage = self.volume_data['Tankfilling [% of h_tank]'].to_numpy()
        self.volume = self.volume_data['Tankvolume [m3]'].to_numpy()
        self.lcg = self.volume_data['lcg [m]'].to_numpy()
        self.tcg = self.volume_data['tcg [m]'].to_numpy()
        self.vcg = self.volume_data['vcg [m]'].to_numpy()
        self.mass = self.volume*water_density
        self.lM = self.mass*(self.lcg-COV[0])
        self.tM = self.mass*self.tcg
        self.volume_data['mass [kg]'] = self.mass
        self.volume_data['lM [kgm]'] = self.lM
        self.volume_data['tM [kgm]'] = self.tM
        #waterplane data
        self.Ix = self.waterplane_data['Inertia_x [m4]'].to_numpy()
        self.GG = self.Ix/buoyant_volume
        self.waterplane_data['GG [m]'] = self.GG
    def percentage_filled(self, percentage):
        self.exact_lM = CubicSpline(self.percentage, self.lM)(percentage)
        self.exact_tM = CubicSpline(self.percentage, self.tM)(percentage)
        self.exact_lcg = CubicSpline(self.percentage, self.lcg)(percentage)
        self.exact_tcg = CubicSpline(self.percentage, self.tcg)(percentage)
        self.exact_vcg = CubicSpline(self.percentage, self.vcg)(percentage)
        self.exact_mass = CubicSpline(self.percentage, self.mass)(percentage)
        self.exact_Ix = CubicSpline(self.percentage, self.Ix)(percentage)
        self.exact_GG = CubicSpline(self.percentage, self.GG)(percentage)
        
def deck(crane_position=None, TP_position=None, TP_mass=0, TP_amount=0, jib_length=None, jib_angle=0, slewing_angle=0): #positions(COG) = [x,y,z]
    """
        Berekent de massa en center of gravity van alles op het dek samen
        voor de momentenstelling

        Parameters
        ----------
        crane_position : array
            Kraanpositie. The default is None.
        TP_position : array
            Transition piece positie. The default is None.
        TP_mass : float
            Massa van 1 Transition piece. The default is 0.
        TP_amount : int.
            Aantal Transition pieces. The default is 0.
        jib_length : float
            float. The default is None.
        jib_angle : float
            float. The default is 0.
        slewing_angle : float
            float. The default is 0.

        Returns
        -------
        np.array([mass_deck, lcg_deck, tcg_deck, vcg_deck])

        """
    if crane_position is None or jib_length is None: 
        
        if TP_position is None or TP_amount==0 : 
            #als er geen deklading of kraan is
            return (np.array([]), np.array([]), np.array([]), np.array([]))
        
        #als er wel deklading is
        cargo_mass = TP_amount*TP_mass
        return (np.array([cargo_mass]), np.array([TP_position[0]]), 
                np.array([TP_position[1]]), np.array([TP_position[2]]))
        
    #Als er een kraan is
        
    #degrees to radians
    jib_angle = (jib_angle/180)*math.pi
    slewing_angle = (slewing_angle/180)*math.pi
    
    cargo_mass = TP_amount*TP_mass
    cargo_lcg, cargo_tcg, cargo_vcg = TP_position
    
    crane_SWL = TP_mass/0.94
    
    crane_housing_mass = 0.34*crane_SWL
    crane_housing_lcg = crane_position[0]
    crane_housing_tcg = crane_position[1]
    crane_housing_vcg = crane_position[2]
    
    jib_mass = 0.17*crane_SWL
    jib_lcg = round(crane_housing_lcg+((jib_length/2)*math.cos(jib_angle))*math.cos(slewing_angle),3)
    jib_tcg = round(crane_housing_tcg+((jib_length/2)*math.cos(jib_angle))*math.sin(slewing_angle),3)
    jib_vcg = round(crane_housing_vcg+(jib_length/2)*math.sin(jib_angle),3)
    
    load_mass = crane_SWL
    load_lcg = round(crane_housing_lcg+jib_length*math.cos(jib_angle)*math.cos(slewing_angle),3)
    load_tcg = round(crane_housing_tcg+jib_length*math.cos(jib_angle)*math.sin(slewing_angle),3)
    load_vcg = round(crane_housing_vcg+jib_length*math.sin(jib_angle),3)
    
    mass_deck = np.array([crane_housing_mass, jib_mass, load_mass, cargo_mass])
    lcg_deck = np.array([crane_housing_lcg, jib_lcg, load_lcg, cargo_lcg])
    tcg_deck = np.array([crane_housing_tcg, jib_tcg, load_tcg, cargo_tcg])
    vcg_deck = np.array([crane_housing_vcg, jib_vcg, load_vcg, cargo_vcg])
    return np.array([mass_deck, lcg_deck, tcg_deck, vcg_deck])

def plates(file, df_hull, df_BHD, hull_thickness, BHD_thickness, material_density, mass_factor): #file = [group, version, subversion]
    """
    

    Parameters
    ----------
    file : TYPE
        list.
    df_hull : TYPE
        df.
    df_BHD : TYPE
        df.
    hull_thickness : TYPE
        df. [transom, shell, deck]
    BHD_thickness : TYPE
        float.
    material_density : TYPE
        Int.
    mass_factor : TYPE
        float.

    Returns
    -------
    TYPE:array
        np.array([mass_plates, lcg_plates, tcg_plates, vcg_plates])

    """
    #hull
    area_hull = df_hull['Area [m2]'].to_numpy()
    lcg_hull = df_hull['lca [m]'].to_numpy()
    tcg_hull = df_hull['tca [m]'].to_numpy()
    vcg_hull = df_hull['vca [m]'].to_numpy()
    volume_hull = area_hull*hull_thickness
    mass_hull = volume_hull*material_density*mass_factor
    
    #bulkheads
    area_BHD = df_BHD['BHD Area [m2]'].to_numpy()
    lcg_BHD = df_BHD['lcg [m]'].to_numpy()
    tcg_BHD = df_BHD['tcg [m]'].to_numpy()
    vcg_BHD = df_BHD['vcg [m]'].to_numpy()
    volume_BHD = area_BHD*BHD_thickness
    mass_BHD = volume_BHD*material_density*mass_factor
    
    mass_plates = np.append(mass_hull, mass_BHD)
    lcg_plates = np.append(lcg_hull, lcg_BHD)
    tcg_plates = np.append(tcg_hull, tcg_BHD)
    vcg_plates = np.append(vcg_hull, vcg_BHD)
    
    return np.array([mass_plates, lcg_plates, tcg_plates, vcg_plates])

def resistance(file, df_resistance, design_speed): #speed in knots
    """
    Leest en berekent data van de weerstand en plot op aanvraag een grafiek

    Parameters
    ----------
    file : TYPE
        List.
    design_speed : TYPE
        float.

    Returns
    -------
    design_resistance : TYPE
        float.

    """
    speed = df_resistance['V [kn]'].to_numpy()[:11]
    resistance = df_resistance['Rtot [N]'].to_numpy()[:11]/1000
    design_resistance = CubicSpline(speed,resistance)(design_speed)
    plt.plot(speed,resistance,'b')
    plt.title('resistance')
    plt.xlabel('speed [kn]')
    plt.ylabel('resistance [kN]')
    return design_resistance

def ZCG(mass_list, zcg_list):
    """
    Berekent transverse, longitudonal of vertical center of gravity van het gehele schip

    Parameters
    ----------
    mass_list : TYPE
        lLst.
    zcg_list :     
        List.

    Returns
    -------
    ZCG : TYPE
        List.

    """
    M = sum(mass_list*zcg_list)
    F = sum(mass_list)
    ZCG = M/F
    return ZCG

def array_add(arr1, arr2, arr3):
    arr = np.append(np.append(arr1, arr2), arr3)
    return arr

def matrix_add(matrix1, matrix2):
    matrix3 = np.zeros(len(matrix1[0])+len(matrix2[0]))
    for i in range(0,len(matrix1)):
        matrix3 = np.vstack([matrix3,np.append(matrix1[i],matrix2[i])])
    matrix3 = np.delete(matrix3,0,axis=0)

    return matrix3




#test