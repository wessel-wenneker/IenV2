from scipy.integrate import trapezoid, cumulative_trapezoid, simpson
from scipy.interpolate import interp1d, CubicSpline
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import random
import math
import os
from read import DataLoader
from Main import file, Ship #schip is berekende boot


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

def findPercentagesequilibrium():
    
    w_change_tanks = -Q_evenwicht
    v_change_tanks = w_change_tanks /(g * water_density)

    max_v_t1 = tank1_volumes[-1]
    max_v_t2 = tank2_volumes[-1]
    max_v_t3 = tank3_volumes[-1]
    
    min_v_t1 = min_v_t3 = 0
    min_v_t2 = CubicSpline(tank2_filling_percentages, tank2_volumes)(20)
    
   #tank 2 begrensd door max en minimum 20%
    v_change_t2 = np.clip(v_change_tanks, min_v_t2 - initial_v_tank2, max_v_t2 - initial_v_tank2)
    v_change_rest = v_change_tanks - v_change_t2
    
    #tank 1&3 begrensd door max én minimum 0%
    max_change_t1_t3 = min(max_v_t1 - initial_v_tank1, max_v_t3 - initial_v_tank3)
    min_change_t1_t3 = max(min_v_t1 - initial_v_tank1, min_v_t3 - initial_v_tank3)  # meest beperkende kant
    v_change_t1_t3 = np.clip(v_change_rest / 2, min_change_t1_t3, max_change_t1_t3)
    
    needed_v_t1 = initial_v_tank1 + v_change_t1_t3
    needed_v_t2 = initial_v_tank2 + v_change_t2
    needed_v_t3 = initial_v_tank3 + v_change_t1_t3
    
    restant_v  = v_change_rest - 2*v_change_t1_t3
    
    needed_percentage_t1 = CubicSpline(tank1_volumes , tank1_filling_percentages)(needed_v_t1)
    needed_percentage_t2 = CubicSpline(tank2_volumes , tank2_filling_percentages)(needed_v_t2)
    needed_percentage_t3 = CubicSpline(tank3_volumes , tank3_filling_percentages)(needed_v_t3)
        
    return needed_v_t1, needed_v_t2, needed_v_t3, needed_percentage_t1, needed_percentage_t2, needed_percentage_t3, restant_v
    
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

x_spant_arr = df_bouyant_CSA["x_in_m"].to_numpy #arr = array
A_spant_arr = df_bouyant_CSA["crossarea_in_m2"].to_numpy

tank1_volumes = df_watervolume_tank1["Tankvolume [m3]"].to_numpy()
tank2_volumes = df_watervolume_tank2["Tankvolume [m3]"].to_numpy()
tank3_volumes = df_watervolume_tank3["Tankvolume [m3]"].to_numpy()

tank1_filling_percentages = df_watervolume_tank1["Tankfilling [% of h_tank]"].to_numpy()
tank2_filling_percentages = df_watervolume_tank2["Tankfilling [% of h_tank]"].to_numpy()
tank3_filling_percentages = df_watervolume_tank3["Tankfilling [% of h_tank]"].to_numpy()

shell = pd.read_csv('data/Shell_CSA_Gr98_V3.0.csv', delimiter=',', skiprows=1)
s_x = shell['X [m]'].to_numpy()
s_outline = shell['OUTLINE LENGTH [m]'].to_numpy()
s_CSA = shell['CROSS SECTION AREA OF SHELL PLATING [m2]'].to_numpy()

tank1 = pd.read_csv('data/Tank1_CSA_Gr98_V3.0.csv', delimiter=',', skiprows=1)
t1x = tank1['x_in_m'].to_numpy()
t1CSA = tank1[' crossarea_in_m2'].to_numpy()

tank2 = pd.read_csv('data/Tank2_CSA_Gr98_V3.0.csv', delimiter=',', skiprows=1)
t2x = tank2['x_in_m'].to_numpy()
t2CSA = tank2[' crossarea_in_m2'].to_numpy()

tank3 = pd.read_csv('data/Tank3_CSA_Gr98_V3.0.csv', delimiter=',', skiprows=1)
t3x = tank3['x_in_m'].to_numpy()
t3CSA = tank3[' crossarea_in_m2'].to_numpy()

hull = pd.read_csv('data/HullAreaData_Gr98_V3.0.csv', delimiter=',', skiprows=1)
xtransom = hull[' lca [m]'][0]
Ntransom = hull[' Area [m2]'][0]*metal_density*g

BHD = pd.read_csv('data/TankBHD_Data_Gr98_V3.0.csv', delimiter=',', skiprows=1)
xminBHD = BHD[' x_min [m]'].to_numpy()
xmaxBHD = BHD[' x_max [m]'].to_numpy()
NBHD = BHD['BHD Area [m2]'].to_numpy()*metal_density*mass_factor*g

deck = json.load(open('data/Antwoordenblad_Gr98V3.0.json'))
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

#------------------------------------------------------------------------------
# Direct uit CSV via read.dataloader (x en area van spanten) 
x_spant_arr = df_bouyant_CSA["x_in_m"] #arr = array
A_spant_arr = df_bouyant_CSA["crossarea_in_m2"]

#drijfkracht in N/m lengte schip (negatief) en "fijnere" array voor Q
buoyancy_arr = water_density * g * -A_spant_arr  
buoyancy_arr_fine = np.interp(nx, x_spant_arr, buoyancy_arr) 

q_arr = Ntot + buoyancy_arr_fine #totale verdeelde belasting

#evenwicht check
W = trapezoid(Ntot,nx)
B = trapezoid(buoyancy_arr, x_spant_arr)
Q_evenwicht = W + B
print(Q_evenwicht)

#initial = rechtstreeks uit grasshopper
Fs_initial = cumulative_trapezoid(q_arr, nx, initial = 0) 

#benodigd volume berekenen
initial_v_tank1 = trapezoid(t1CSA,t1x)
initial_v_tank2 = trapezoid(t2CSA,t2x)
initial_v_tank3 = trapezoid(t3CSA,t3x)

#benodigde percentages vert. evenwicht (+volume dat niet past)
needed_v_t1, needed_v_t2, needed_v_t3, needed_perc_t1, needed_perc_t2, needed_perc_t3, restant = findPercentagesequilibrium()
print(f"Er is {restant} volume tekort voor evenwicht")
#verschil factor volume
fchange_v_t1 = needed_v_t1/initial_v_tank1
fchange_v_t2 = needed_v_t2/initial_v_tank2
fchange_v_t3 = needed_v_t3/initial_v_tank3

#nieuwe belasting
Nt1_new = Nt1 * fchange_v_t1
Nt2_new = Nt2 * fchange_v_t2
Nt3_new = Nt3 * fchange_v_t3

#copy van eerder deel----------------------------------------------------------
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

weight_tp = 230000 * 9.81
r1_tp = 4
r2_tp = weight_tp / r1_tp / np.pi * 2

for i in range(0, TP_amount):
    xTP = deck['Lading_locaties'][keylist[i]]['LCG #[m]']
    xminTP = np.searchsorted(nx, xTP - r1_tp)
    xmaxTP = np.searchsorted(nx, xTP + r1_tp)

    Ntot_new[xminTP:xmaxTP] += r2_tp * np.sin(np.arccos(np.linspace(-1, 1, len(Ntot_new[xminTP:xmaxTP]))))

weight_crane = 230000 * 9.81 
r1_c = 1
r2_c = weight_crane / r1_c / np.pi * 2

xmincrane = np.searchsorted(nx, xcrane - r1_c)
xmaxcrane = np.searchsorted(nx, xcrane + r1_c)
Ntot_new[xmincrane:xmaxcrane] += r2_c * np.sin(np.arccos(np.linspace(-1, 1, len(Ntot_new[xmincrane:xmaxcrane]))))
#------------------------------------------------------------------------------
q_balanced_arr = Ntot_new + buoyancy_arr_fine

Fs_balanced_arr = cumulative_trapezoid(q_balanced_arr, nx, initial=0)
Ms_balanced_arr = cumulative_trapezoid(Fs_balanced_arr, nx, initial=0)

#check
#trapezoid(Nt1/(g*water_density),nx)
#trapezoid(Nt2/(g*water_density),nx)
#trapezoid(Nt3/(g*water_density),nx)
#print(trapezoid(Ntot,nx))
#print(trapezoid(Ntot_new,nx))
#print(trapezoid(q_balanced_arr,nx))

#Plots
plot(x_spant_arr, buoyancy_arr,"Length [m]" , "Buoyancy [N/m]", "Buoyancy along ship length")
plot(nx,q_arr,"Lengte [m]", "Belasting [N/m]", "Belasting langs scheepslengte")
plot(nx, Fs_initial, "Lengte [m]", "Schuifkracht [N]", "Schuifkracht langs scheepslengte zonder tank aanpassingen")
#Met tanks in balans
plot(nx, Ntot_new, "Lengte [m]", "Lading [N/m]", "Belading met tanks in evenwicht")
plot(nx,q_balanced_arr ,"Lengte [m]", "Belasting [N/m]", "Belasting langs scheepslengte met tanks in evenwicht")
plot(nx, Fs_balanced_arr, "Lengte [m]", "Schuifkracht [N]", "Schuifkracht langs scheepslengte met de tanks in evenwicht")
plot(nx, Ms_balanced_arr, "Lengte [m]", "Moment [Nm]", "Moment langs scheepslengte met de tanks in evenwicht")

