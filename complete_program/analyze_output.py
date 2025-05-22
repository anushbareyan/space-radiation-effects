import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import configparser

config = configparser.ConfigParser()
config.read('simulation.config')

#Read dimensions from config
length = float(config['DIMENSIONS']['length_nm']) * 1e-9
width = float(config['DIMENSIONS']['width_nm']) * 1e-9
thickness = float(config['DIMENSIONS']['thickness_nm']) * 1e-9

def apply_dark_blue_theme():
    plt.rcParams.update({
        'figure.facecolor': 'white', 'axes.facecolor': 'white',
        'axes.edgecolor': 'black', 'axes.labelcolor': 'black',
        'xtick.color': 'black', 'ytick.color': 'black',
        'text.color': 'black', 'axes.titlecolor': 'black',
        'grid.color': 'gray', 'grid.alpha': 0.3,
    })

#File Loading
df = pd.read_csv(
    'out_omni.dat',
    sep='\t',
    names=[
        'E_beam', 'E_incident', 'E_deposited', 'x_incident', 'y_incident',
        'z_incident', 'theta', 'Time', 'EventID', 'TrackID', 'ParticleID',
        'ParticleName', 'CreatorProcessName', 'IsEdepositedTotalEntry',
        'IsSurfaceHitTrack', 'detector#'
    ],
    skiprows=1
)

#Data Filtering
df_cu = df[
    (df['detector#'] == 0) &
    (df['E_deposited'] > 0) &
    (df['E_incident'] > 0) &
    (df['ParticleName'] == 'proton')
]

#Physics Constants (NRT)
rho_0 = 1.68e-8  # Cu resistivity [Ω·m]
eta = 0.8         # NRT efficiency factor
E_d = 18.0        # Displacement threshold [eV]
alpha = 4.1e-6    # Δρ/DPA [Ω·m/DPA] — changed to match working code

#Geometry (in meters)
L = 100e-9   # Length [m] from config or hardcoded
W = 10e-6    # Width [m] changed to 10 microns to match working code
T = 10e-9    # Thickness [m]
A = W * T    # Cross-section area [m²]
V = L * A    # Volume [m³]

#Atomic Density
rho_Cu = 8960         # Density [kg/m³]
M_Cu = 0.063546       # Molar mass [kg/mol]
N_atoms = (rho_Cu * V / M_Cu) * 6.022e23  # Number of atoms in volume
print(f"N_atoms: {N_atoms}")

#NRT Damage Calculation
E_dep_eV = df_cu['E_deposited'].sum() * 1e6  # MeV → eV
print(f"E_dep_eV: {E_dep_eV}")
DPA = (eta * E_dep_eV) / (2 * E_d * N_atoms)
print(f"DPA: {DPA}")
delta_rho = alpha * DPA
print(f"delta_rho: {delta_rho}")

#Resistance Change
R0 = rho_0 * L / A
R_new = (rho_0 + delta_rho) * L / A
delta_R_pct = ((R_new - R0) / R0) * 100


print(f"NRT Model Results ({L}×{W}×{T} m Cu)")
print(f"DPA (NRT): {DPA:.3e}")
print(f"Resistance change: {delta_R_pct}%")


apply_dark_blue_theme()
plt.hist(df_cu['E_deposited'], bins=30, color='cyan', edgecolor='white')
plt.title('Energy Deposition Distribution')
plt.xlabel('Energy (MeV)')
plt.ylabel('Counts')
plt.show()

plt.scatter(df_cu['E_beam'], df_cu['E_deposited'], color='magenta', alpha=0.7, edgecolor='white')
plt.yscale('log')
plt.title('Incident vs Deposited Energy')
plt.xlabel('Incident Energy (MeV)')
plt.ylabel('Deposited Energy (MeV)')
plt.show()
