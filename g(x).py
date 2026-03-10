from scipy.integrate import trapezoid, cumulative_trapezoid, simpson
from scipy.interpolate import interp1d, CubicSpline
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import random
import math
import os

def plot(x, y, x_label='x', y_label='y', title='', grid=False):
    plt.figure()
    plt.plot(x,y,'k')
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    if grid:
        plt.grid()
    return y

def interpolate(x,y,nx):
    ny = np.array([])
    for i in nx:
        if i > x[0] and i < x[-1]:
            ny = np.append(ny,interp1d(x, y)(i))
        else:
            ny = np.append(ny,0)
    return ny

water_density = 1025
metal_density = 7850
mass_factor = 2.1
shell_thickness = 8 #[mm]
g = 9.81

shell = pd.read_csv('data/Shell_CSA_Gr98_V2.0.csv', delimiter=',', skiprows=1)
s_x = shell['X [m]'].to_numpy()
s_outline = shell['OUTLINE LENGTH [m]'].to_numpy()
s_CSA = shell['CROSS SECTION AREA OF SHELL PLATING [m2]'].to_numpy()

tank1 = pd.read_csv('data/Tank1_CSA_Gr98_V2.0.csv', delimiter=',', skiprows=1)
t1x = tank1['x_in_m'].to_numpy()
t1CSA = tank1[' crossarea_in_m2'].to_numpy()

tank2 = pd.read_csv('data/Tank2_CSA_Gr98_V2.0.csv', delimiter=',', skiprows=1)
t2x = tank2['x_in_m'].to_numpy()
t2CSA = tank2[' crossarea_in_m2'].to_numpy()

tank3 = pd.read_csv('data/Tank3_CSA_Gr98_V2.0.csv', delimiter=',', skiprows=1)
t3x = tank3['x_in_m'].to_numpy()
t3CSA = tank3[' crossarea_in_m2'].to_numpy()

hull = pd.read_csv('data/HullAreaData_Gr98_V2.0.csv', delimiter=',', skiprows=1)
xtransom = hull[' lca [m]'][0]
Ntransom = hull[' Area [m2]'][0]*metal_density*g

BHD = pd.read_csv('data/TankBHD_Data_Gr98_V2.0.csv', delimiter=',', skiprows=1)
xminBHD = BHD[' x_min [m]'].to_numpy()
xmaxBHD = BHD[' x_max [m]'].to_numpy()
NBHD = BHD['BHD Area [m2]'].to_numpy()*metal_density*mass_factor*g

deck = json.load(open('data/Antwoordenblad_Gr98V2.0.json'))
xcrane = deck['Zwaartepunten_kraanlast']['LCG_kraanhuis #[m]']
TP_amount = deck['Deklast_transition_pieces']['Aantal_transition_pieces #[-]']
keylist = list(deck['Lading_locaties'].keys())

nx = np.linspace(s_x[0],s_x[-1],10000)
Nshell = interpolate(s_x,s_CSA,nx)*metal_density*mass_factor*shell_thickness*g
Nt1 = interpolate(t1x,t1CSA,nx)*water_density*g
Nt2 = interpolate(t2x,t2CSA,nx)*water_density*g
Nt3 = interpolate(t3x,t3CSA,nx)*water_density*g
Ntot = Nshell+Nt1+Nt2+Nt3

transom_index = np.searchsorted(nx,xtransom+0.5)
Ntot[1:transom_index] += Ntransom

for i in range(0,len(NBHD)):
    min_index = np.searchsorted(nx,xminBHD[i])
    max_index = np.searchsorted(nx,xmaxBHD[i])
    if xmaxBHD[i] - xminBHD[i] <= 1:
        Ntot[min_index:max_index] += NBHD[i]
    else:
        Ntot[min_index:max_index] += NBHD[i]/(xmaxBHD[i] - xminBHD[i])*0.01

weight = 230000*9.81
r1 = 4
r2 = weight/r1/np.pi*2

for i in range(0,TP_amount):
    xTP = deck['Lading_locaties'][keylist[i]]['LCG #[m]']
    xminTP = np.searchsorted(nx,xTP-r1)
    xmaxTP = np.searchsorted(nx,xTP+r1)
    Ntot[xminTP:xmaxTP] +=  r2*np.sin(np.arccos(np.linspace(-1,1,len(Ntot[xminTP:xmaxTP]))))

weight = 230000*9.81
r1 = 1
r2 = weight/r1/np.pi*2

xmincrane = np.searchsorted(nx,xcrane-r1)
xmaxcrane = np.searchsorted(nx,xcrane+r1)

Ntot[xmincrane:xmaxcrane] +=  r2*np.sin(np.arccos(np.linspace(-1,1,len(Ntot[xmincrane:xmaxcrane]))))

#Ntot[0] = 0

plot(nx,Ntot,'length [m]','load [kN/m]','load over length')
