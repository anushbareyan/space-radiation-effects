import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import configparser

config = configparser.ConfigParser()
config.read('simulation.config')

# Read dimensions from config
length = float(config['DIMENSIONS']['length_nm']) * 1e-9
width = float(config['DIMENSIONS']['width_nm']) * 1e-9
thickness = float(config['DIMENSIONS']['thickness_nm']) * 1e-9

# ... rest of analyze_output.py code remains the same ...
def apply_dark_blue_theme():
    plt.rcParams.update({
        'figure.facecolor': 'white', 'axes.facecolor': 'white',
        'axes.edgecolor': 'black', 'axes.labelcolor': 'black',
        'xtick.color': 'black', 'ytick.color': 'black',
        'text.color': 'black', 'axes.titlecolor': 'black',
        'grid.color': 'gray', 'grid.alpha': 0.3,
    })

# --- File Loading ---
df = pd.read_csv(
    'out_100_10_w0001_15_final.dat',
    sep='\t',
    names=[
        'E_beam', 'E_incident', 'E_deposited', 'x_incident', 'y_incident',
        'z_incident', 'theta', 'Time', 'EventID', 'TrackID', 'ParticleID',
        'ParticleName', 'CreatorProcessName', 'IsEdepositedTotalEntry',
        'IsSurfaceHitTrack', 'detector#'
    ],
    skiprows=1
)

# --- Data Filtering ---
df_cu = df[(df['detector#'] == 0) & (df['E_deposited'] > 0)]

# --- Physics Constants (NRT) ---
rho_0 = 1.68e-8  # Cu resistivity [Ω·m] (NIST SRD 126)
eta = 0.8         # NRT efficiency factor
E_d = 18.0        # Displacement threshold 30[eV] (ASTM E521-16) worst case 18
alpha = 1e-6    # Δρ/DPA [Ω·m/DPA] (JPS Conf. Proc. 33)

# --- Geometry ---
L = 100e-9  # Length [m]
W = 100e-9  # Width [m]
T = 10e-9   # Thickness [m]
A = W * T   # Cross-section [m²]
V = L * A   # Volume [m³]

# Atomic density
rho_Cu = 8960         # Density [kg/m³]
M_Cu = 0.063546       # Molar mass [kg/mol]
N_atoms = (rho_Cu * V / M_Cu) * 6.022e23  # Atoms in volume
print(f"N_atoms: {N_atoms}")
# --- NRT Damage Calculation ---
E_dep_eV = df_cu['E_deposited'].sum() * 1e6  # MeV→eV
print(f"E_dep_eV: {E_dep_eV}")
DPA = (0.8 * E_dep_eV) / (2 * E_d * N_atoms)  # NRT formula
print(f"DPA: {DPA}")
delta_rho = alpha * DPA  # Resistivity change
print(f"delta_rho: {delta_rho}")
# --- Resistance Change ---
R0 = rho_0 * L / A
R_new = (rho_0 + delta_rho) * L / A
delta_R_pct = ((R_new - R0)/R0) * 100

# --- Output ---
print("=== NRT Model Results (100×100×10 nm³ Cu) ===")
print(f"DPA (NRT): {DPA:.3e}")
print(f"Resistance change: {delta_R_pct}%")

# --- Visualization ---
apply_dark_blue_theme()
plt.hist(df_cu['E_deposited'], bins=30, color='cyan', edgecolor='white')
plt.title('NRT: Energy Deposition Distribution')
plt.xlabel('Energy (MeV)')
plt.ylabel('Counts')
plt.show()
plt.scatter(df_cu['E_beam'], df_cu['E_deposited'],
            color='magenta', alpha=0.7, edgecolor='white')
plt.title('ARC-DPA: Incident vs Deposited Energy')
plt.xlabel('Incident Energy (MeV)')
plt.ylabel('Deposited Energy (MeV)')
plt.show()
