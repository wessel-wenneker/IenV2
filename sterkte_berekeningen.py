# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:00:50 2026

@author: ellin
"""
from scipy.integrate import trapezoid, cumulative_trapezoid, simpson
from scipy.interpolate import interp1d, CubicSpline
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import random
import math
import os
from read import DataLoader
from Main import file, Ship #schip is berekende boot

antwoordenblad = json.load(open("Data/Antwoordenblad_Gr98V3.0.json"))
lengte_kraanarm = antwoordenblad["Kraan_beladingsconditie"]["Kraanboom_lengte #[m]"]
tp_wheight = antwoordenblad["Kraan_beladingsconditie"]["Gewicht_per_TP #[N]"]
aantal_tp = antwoordenblad["Kraan_beladingsconditie"]["Aantal_TP_in_kraan #[-]"]
slewing_angle = antwoordenblad["Kraan_beladingsconditie"]["Zwenkhoek #[graden]"]
jib_angle = antwoordenblad["Kraan_beladingsconditie"]["Giekhoek #[graden]"]
x_kraan = antwoordenblad["Zwaartepunten_kraanlast"]["LCG_kraanhuis #[m]"]
def computeQFsMbArrays(buoyancy_arr, g_arr,x):
    """Moet nog aanpassingen in om het moment van de kraan er in te krijgen als die er is!!"""
    q = g_arr + buoyancy_arr
    Fs = cumulative_trapezoid(q, x, initial=0)
    Mb = cumulative_trapezoid(Fs, x, initial=0)
    moment_kraan = lengte_kraanarm * tp_wheight * aantal_tp * math.cos(slewing_angle) * math.cos(jib_angle)
    for i in range(len(x)-1):
        if x[i] >= x_kraan:
            Mb[i] += moment_kraan
    return q, Fs, Mb

def integrateTankCrossections():
    """"""
    
    csa_tank1 = loader.read_custom("Tank1_CSA")
    csa_tank2 = loader.read_custom("Tank2_CSA")
    csa_tank3 = loader.read_custom("Tank3_CSA")
    
    t1CSA = csa_tank1["crossarea_in_m2"]
    t1x   = csa_tank1["x_in_m"].to_numpy()
    t2CSA = csa_tank2["crossarea_in_m2"].to_numpy()
    t2x   = csa_tank2["x_in_m"].to_numpy()
    t3CSA = csa_tank3["crossarea_in_m2"].to_numpy()
    t3x   = csa_tank3["x_in_m"].to_numpy()
    
    initial_v_tank1 = trapezoid(t1CSA,t1x)
    initial_v_tank2 = trapezoid(t2CSA,t2x)
    initial_v_tank3 = trapezoid(t3CSA,t3x)
    return np.array([initial_v_tank1,initial_v_tank2,initial_v_tank3])

def plot(x, y, x_label='x', y_label='y', title='', grid=False):
    plt.figure()
    plt.plot(x,y,'k')
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    if grid:
        plt.grid()
    plt.show()
    return y

def interpolate(x,y,nx):
    ny = np.array([])
    for i in nx:
        if i > x[0] and i < x[-1]:
            ny = np.append(ny,interp1d(x, y)(i))
        else:
            ny = np.append(ny,0)
    return ny

def findPercentagesequilibrium(Q_evenwicht):
    
    w_change_tanks = -Q_evenwicht
    v_change_tanks = w_change_tanks /(g * water_density)

    max_v_t1 = tank1_volumes[-1]
    max_v_t2 = tank2_volumes[-1]
    max_v_t3 = tank3_volumes[-1]
    
    min_v_t1 = min_v_t3 = 0
    min_v_t2 = CubicSpline(tank2_filling_percentages, tank2_volumes)(20)
    
    initial_v_tanks = integrateTankCrossections()
    
   #tank 2 begrensd door max en minimum 20%
    v_change_t2 = np.clip(v_change_tanks, min_v_t2 - initial_v_tanks[1], max_v_t2 - initial_v_tanks[1])
    v_change_rest = v_change_tanks - v_change_t2
    
    #tank 1&3 begrensd door max én minimum 0%
    max_change_t1_t3 = min(max_v_t1 - initial_v_tanks[0], max_v_t3 - initial_v_tanks[2])
    min_change_t1_t3 = max(min_v_t1 - initial_v_tanks[0], min_v_t3 - initial_v_tanks[2])  # meest beperkende kant
    v_change_t1_t3 = np.clip(v_change_rest / 2, min_change_t1_t3, max_change_t1_t3)
    v_change_arr = np.array([v_change_t1_t3,v_change_t2,v_change_t1_t3])
    
    needed_v_tanks = initial_v_tanks + v_change_arr
    
    restant_v  = v_change_rest - 2*v_change_t1_t3
    print(f"Er is {restant_v} volume te weinig voor evenwicht")
    needed_percentage_t1 = CubicSpline(tank1_volumes , tank1_filling_percentages)(needed_v_tanks[0])
    needed_percentage_t2 = CubicSpline(tank2_volumes , tank2_filling_percentages)(needed_v_tanks[1])
    needed_percentage_t3 = CubicSpline(tank3_volumes , tank3_filling_percentages)(needed_v_tanks[2])
        
    return needed_v_tanks, needed_percentage_t1, needed_percentage_t2, needed_percentage_t3, restant_v
    
def checkTankvullingConsistency():
    #evenwicht check
    Q_evenwicht = trapezoid(Ntot,nx) + trapezoid(buoyancy_arr, x_spant_arr)
    #huidig volume in de tank
    initial_v_tanks = integrateTankCrossections()
    
    #functie de evenwicht zoekt met tanks 
    needed_v_tanks, needed_perc_t1, needed_perc_t2, needed_perc_t3, restant = findPercentagesequilibrium(Q_evenwicht)
    
    fchange_v_tanks = needed_v_tanks/initial_v_tanks #verschil factor volume
    #nieuwe belasting
    Nt1_new = Nt1 * fchange_v_tanks[0]
    Nt2_new = Nt2 * fchange_v_tanks[1]
    Nt3_new = Nt3 * fchange_v_tanks[2]

    #copy van eerder deel
    Ntot_new = Nshell.copy()

    transom_index = np.searchsorted(nx, xtransom + 0.5)
    Ntot_new[1:transom_index] += Ntransom

    for i in range(0, len(NBHD)):
        min_index = np.searchsorted(nx, xminBHD[i])
        max_index = np.searchsorted(nx, xmaxBHD[i])
        if xmaxBHD[i] - xminBHD[i] <= 1:
            Ntot_new[min_index:max_index] += NBHD[i]
        else:
            Ntot_new[min_index:max_index] += NBHD[i] / (xmaxBHD[i] - xminBHD[i]) * 0.01

    #Voeg de NIEUWE ballast toe (zorgt voor verticaal evenwicht)
    Ntot_new += (Nt1_new + Nt2_new + Nt3_new)

    r1_tp = 4
    r2_tp = weight_TP / r1_tp / np.pi * 2

    for i in range(0, TPamount):
        xTP = deck['Lading_locaties'][keylist[i]]['LCG #[m]']
        xminTP = np.searchsorted(nx, xTP - r1_tp)
        xmaxTP = np.searchsorted(nx, xTP + r1_tp)

        Ntot_new[xminTP:xmaxTP] += r2_tp * np.sin(np.arccos(np.linspace(-1, 1, len(Ntot_new[xminTP:xmaxTP]))))

    r1_c = 1
    r2_c = weight_crane / r1_c / np.pi * 2

    xmincrane = np.searchsorted(nx, xcrane - r1_c)
    xmaxcrane = np.searchsorted(nx, xcrane + r1_c)
    Ntot_new[xmincrane:xmaxcrane] += r2_c * np.sin(np.arccos(np.linspace(-1, 1, len(Ntot_new[xmincrane:xmaxcrane]))))

    q_check, Fs_check, Mb_check = computeQFsMbArrays(buoyancy_arr_fine, Ntot_new, nx)
    
    return Ntot_new, q_check, Fs_check, Mb_check


#waardes/constanten, dit stuk moet nog anders----------------------------------
water_density = 1025
metal_density = 7850
mass_factor = 2.1
shell_thickness = 8 #[mm]
g = 9.81

loader = DataLoader(file=file) #dataloader defineren voor goede file
df_bouyant_CSA = loader.read_custom("Buoyant_CSA")
df_watervolume_tank1 = loader.load_inputs().df_tank1
df_watervolume_tank2 = loader.load_inputs().df_tank2
df_watervolume_tank3 = loader.load_inputs().df_tank3

x_spant_arr = df_bouyant_CSA["x_in_m"] #arr = array
A_spant_arr = df_bouyant_CSA["crossarea_in_m2"]

tank1_volumes = df_watervolume_tank1["Tankvolume [m3]"].to_numpy()
tank2_volumes = df_watervolume_tank2["Tankvolume [m3]"].to_numpy()
tank3_volumes = df_watervolume_tank3["Tankvolume [m3]"].to_numpy()

tank1_filling_percentages = df_watervolume_tank1["Tankfilling [% of h_tank]"].to_numpy()
tank2_filling_percentages = df_watervolume_tank2["Tankfilling [% of h_tank]"].to_numpy()
tank3_filling_percentages = df_watervolume_tank3["Tankfilling [% of h_tank]"].to_numpy()

shell = pd.read_csv('Data/Shell_CSA_Gr98_V3.0.csv', delimiter=',', skiprows=1)
s_x = shell['X [m]'].to_numpy()
s_outline = shell['OUTLINE LENGTH [m]'].to_numpy()
s_CSA = shell['CROSS SECTION AREA OF SHELL PLATING [m2]'].to_numpy()

tank1 = pd.read_csv('Data/Tank1_CSA_Gr98_V3.0.csv', delimiter=',', skiprows=1)
t1x = tank1['x_in_m'].to_numpy()
t1CSA = tank1[' crossarea_in_m2'].to_numpy()

tank2 = pd.read_csv('Data/Tank2_CSA_Gr98_V3.0.csv', delimiter=',', skiprows=1)
t2x = tank2['x_in_m'].to_numpy()
t2CSA = tank2[' crossarea_in_m2'].to_numpy()

tank3 = pd.read_csv('Data/Tank3_CSA_Gr98_V3.0.csv', delimiter=',', skiprows=1)
t3x = tank3['x_in_m'].to_numpy()
t3CSA = tank3[' crossarea_in_m2'].to_numpy()

hull = pd.read_csv('Data/HullAreaData_Gr98_V3.0.csv', delimiter=',', skiprows=1)
xtransom = hull[' lca [m]'][0]
Ntransom = hull[' Area [m2]'][0]*metal_density*g

BHD = pd.read_csv('Data/TankBHD_Data_Gr98_V3.0.csv', delimiter=',', skiprows=1)
xminBHD = BHD[' x_min [m]'].to_numpy()
xmaxBHD = BHD[' x_max [m]'].to_numpy()
NBHD = BHD['BHD Area [m2]'].to_numpy()*metal_density*mass_factor*g

deck = json.load(open('Data/Antwoordenblad_Gr98V3.0.json'))
SWLcrane = deck['Kraan_beladingsconditie']['SWLmax_kraan #[N]']
xcrane = deck['Zwaartepunten_kraanlast']['LCG_kraanhuis #[m]']
TPamount = deck['Deklast_transition_pieces']['Aantal_transition_pieces #[-]']
keylist = list(deck['Lading_locaties'].keys())
#------------------------------------------------------------------------------


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

weight_TP = 230000*9.81
r1 = 4
r2 = weight_TP/r1/np.pi*2

for i in range(0,TPamount):
    xTP = deck['Lading_locaties'][keylist[i]]['LCG #[m]']
    xminTP = np.searchsorted(nx,xTP-r1)
    xmaxTP = np.searchsorted(nx,xTP+r1)
    Ntot[xminTP:xmaxTP] +=  r2*np.sin(np.arccos(np.linspace(-1,1,len(Ntot[xminTP:xmaxTP]))))

weight_crane = SWLcrane*1.51*9.81
r1 = 1
r2 = weight_crane/r1/np.pi*2
    
xmincrane = np.searchsorted(nx,xcrane-r1)
xmaxcrane = np.searchsorted(nx,xcrane+r1)
    
Ntot[xmincrane:xmaxcrane] +=  r2*np.sin(np.arccos(np.linspace(-1,1,len(Ntot[xmincrane:xmaxcrane]))))

#Ntot[0] = 0

#drijfkracht in N/m lengte schip (negatief) en "fijnere" array voor Q
buoyancy_arr = water_density * g * -A_spant_arr  
buoyancy_arr_fine = np.interp(nx, x_spant_arr, buoyancy_arr) 

q_arr, Fs, Mb = computeQFsMbArrays(buoyancy_arr_fine, Ntot, nx)



s_Ix_ref = shell['INERTIA_X[m4]'].to_numpy()   # bij 1 mm referentiedikte
s_cz     = shell['CENTROID_Z[m]'].to_numpy()
s_zk     = shell['Z_Keel[m]'].to_numpy()
s_zd     = shell['Z_DECK[m]'].to_numpy()

# Schalen: I schaalt lineair met t voor dunne schaal
Ix = interpolate(s_x, s_Ix_ref * shell_thickness, nx)  # shell_thickness = 8

# Stap 12: Buigstijfheid EI(x) 
E = 205e9  # Pa
EI = E * Ix

# Stap 13: Gereduceerd moment κ(x) = M(x) / (E·I(x)) 
kappa = np.where(Ix > 0, Mb / EI, 0)

# Stap 14: Buigspanning dek en bodem 
z_na   = interpolate(s_x, s_cz, nx)
z_keel = interpolate(s_x, s_zk, nx)
z_deck = interpolate(s_x, s_zd, nx)

# sigma = M·z / I  (z vanaf NA, positief omhoog)
sigma_bodem = np.where(Ix > 0, Mb * (z_keel - z_na) / Ix, 0)  # bodem onder NA → negatieve z
sigma_dek   = np.where(Ix > 0, Mb * (z_deck - z_na) / Ix, 0)  # dek boven NA → positieve z

# Omzetten naar MPa
sigma_bodem_MPa = sigma_bodem / 1e6
sigma_dek_MPa   = sigma_dek / 1e6

# Plot
sigma_y = 355  # MPa
x_min= s_x[0]
x_max= s_x[-2]
mask = (nx>=x_min) & (nx<=x_max)  
kappa[~mask] = 0
sigma_bodem[~mask] = 0
sigma_dek[~mask] = 0






#------------------------------------------------------------------------------
#Plots
plot(nx,Ntot,'length [m]','load [kN/m]','load over length')
plot(x_spant_arr, buoyancy_arr,"Length [m]" , "Buoyancy [N/m]", "Buoyancy along ship length")
plot(nx,q_arr,"Lengte [m]", "Belasting [N/m]", "Belasting langs scheepslengte")
plot(nx, Fs, "Lengte [m]", "Schuifkracht [N]", "Schuifkracht langs scheepslengte")
plot(nx,Mb,"Lengte [m]", "Moment [Nm]", "Moment langs scheepslengte")
#Met tanks in balans
Ntot_check, q_check, Fs_check, Mb_check = checkTankvullingConsistency()
plot(nx, Ntot_check, "Lengte [m]", "Lading [N/m]", "Belading met verdeelde belasting evenwicht")
plot(nx,q_check ,"Lengte [m]", "Belasting [N/m]", "Belasting langs scheepslengte met verdeelde belasting evenwicht")
plot(nx, Fs_check, "Lengte [m]", "Schuifkracht [N]", "Schuifkracht langs scheepslengte met de verdeelde belasting evenwicht")
plot(nx, Mb_check, "Lengte [m]", "Moment [Nm]", "Moment langs scheepslengte met de verdeelde belasting evenwicht")

plt.figure()
plt.plot(nx, Ix, 'k')
plt.xlabel('Lengte [m]')
plt.ylabel('Traagheidsmoment I [m^4]')

plt.figure()
plt.plot(nx, EI, 'k')
plt.xlabel('Lengte [m]')
plt.ylabel('Buigstijfheid EI [Nm^2]')

plt.figure()
plt.plot(nx, kappa, 'k')
plt.xlabel('Lengte [m]')
plt.ylabel('Gereduceerd moment κ [1/m]')

plt.figure()
plt.plot(nx, sigma_bodem_MPa, 'b', label='Bodem')
plt.plot(nx, sigma_dek_MPa, 'r', label='Dek')
plt.ylim(-800,500)
plt.axhline(sigma_y, color='k', linestyle='--', label=f'σ_y = {sigma_y} MPa')
plt.axhline(-sigma_y, color='k', linestyle='--')
plt.xlabel('Lengte [m]')
plt.ylabel('Buigspanning [MPa]')
plt.title('Buigspanning dek en bodem over scheepslengte')
plt.legend()
plt.grid()

# Deel 2: Doorbuiging bepalen
# 1. Bepaal de verdeling van de hoekverdraaiing door het verdeelde gereduceerde moment te integreren.
theta_prime_rad = cumulative_trapezoid(kappa, nx, initial=0)
theta_prime_deg = np.degrees(theta_prime_rad)

# 2. Bepaal de verdeling van de doorbuiging door de verdeelde hoekverdraaiing te integreren.
w_prime = cumulative_trapezoid(theta_prime_rad, nx, initial=0)

# Relatieve waarden berekenen (w(0) = 0 en w(L) = 0)
delta_x = nx[-1] - nx[0]
theta_corr_rad = (w_prime[-1] - w_prime[0]) / delta_x if delta_x != 0 else 0

theta_rad = theta_prime_rad - theta_corr_rad
theta_deg = np.degrees(theta_rad)

w = w_prime - theta_corr_rad * (nx - nx[0]) - w_prime[0]

# Extra plots voor doorbuiging
plt.figure()
plt.plot(nx, theta_prime_deg, 'k')
plt.xlabel('x [m]')
plt.ylabel("Hoek - \u03B8'(x) [deg]")
plt.grid()

plt.figure()
plt.plot(nx, w_prime, 'k')
plt.xlabel('x [m]')
plt.ylabel("Doorbuiging - w'(x) [m]")
plt.grid()

plt.figure()
plt.plot(nx, theta_deg, 'k')
plt.xlabel('x [m]')
plt.ylabel("Relatieve hoek - \u03B8(x) [deg]")
plt.grid()

plt.figure()
plt.plot(nx, w, 'k')
plt.xlabel('x [m]')
plt.ylabel("relatieve doorbuiging - w(x) [m]")
plt.grid()

plt.show()
