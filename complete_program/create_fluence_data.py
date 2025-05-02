from netCDF4 import Dataset
import numpy as np
from pathlib import Path
from collections import defaultdict
import configparser

config = configparser.ConfigParser()
config.read('simulation.config')

# Read dimensions from config
length = float(config['DIMENSIONS']['length_nm'])
width = float(config['DIMENSIONS']['width_nm'])
thickness = float(config['DIMENSIONS']['thickness_nm'])

# Configuration
BASE_DIR = 'goes16_data/'
YEARS = list(map(int, config['SIMULATION']['years'].split(',')))
YEARS = range(YEARS[0], YEARS[1]+1)
SECONDS_PER_5MIN = 300
SOLID_ANGLES = {"T1": 1.84, "T2": 1.84, "T3": 6.28}

# ... rest of create_fluence_data.py code remains the same ...

def decode_energy_label(label):
    """Convert netCDF energy label to numerical bounds with proper parsing"""
    if isinstance(label, np.ndarray):
        label_str = b''.join(label).decode('utf-8').strip('\x00')
    else:
        label_str = label.decode('utf-8').strip('\x00')

    # Improved parsing for energy range
    energy_part = label_str.split(':')[-1].replace("MeV", "").strip()
    e_low, e_high = map(float, energy_part.split('-'))
    return (e_low, e_high)

# Initialize cumulative fluence with float values
cumulative_fluence = defaultdict(float)

# Collect and process files
file_paths = []
for year in YEARS:
    year_dir = Path(BASE_DIR) / str(year)
    if year_dir.exists():
        file_paths.extend(sorted(year_dir.glob('*.nc')))

for file_path in file_paths:
    try:
        with Dataset(file_path, 'r') as nc:
            for telescope in ["T1", "T2", "T3"]:
                try:
                    # Get flux data as numpy array with missing values filled
                    flux_var = nc[f'{telescope}_DifferentialProtonFluxes']
                    flux_data = np.ma.filled(flux_var[:], fill_value=0.0)

                    # Parse energy bins
                    energy_labels = nc[f'energy_{telescope}_label'][:]
                    energy_bins = [decode_energy_label(l) for l in energy_labels]
                    bin_widths = np.array([(e_high - e_low)*1000 for (e_low, e_high) in energy_bins])

                    # Verify array dimensions
                    if flux_data.ndim == 3:  # [time, sector, energy]
                        flux_data = np.sum(flux_data, axis=1)  # Sum across sectors

                    # Calculate fluence with proper unit conversions
                    fluence_5min = flux_data * SECONDS_PER_5MIN  # Time integration
                    fluence_5min *= SOLID_ANGLES[telescope]     # Solid angle
                    fluence_5min *= bin_widths[np.newaxis, :]   # Energy bin width

                    # Sum across all time periods and sectors
                    daily_fluence = np.sum(fluence_5min, axis=(0))

                    # Accumulate to cumulative total
                    for (e_low, e_high), fluence in zip(energy_bins, daily_fluence):
                        band_key = f"{int(e_low)}-{e_high:.1f}" if e_high < 1 else f"{e_low:.1f}-{e_high:.1f}"
                        cumulative_fluence[band_key] += float(fluence)

                except KeyError:
                    continue

    except Exception as e:
        print(f"Skipping {file_path.name}: {str(e)}")
        continue
# Write results with proper formatting
with open('cumulative_fluence_2020-2025.txt', 'w') as f:
    f.write("Energy Band (MeV)\tTotal Fluence 2020-2025 (particles/cm²)\n")
    # Sort bands numerically by lower energy
    sorted_bands = sorted(cumulative_fluence.keys(),
                         key=lambda x: float(x.split('-')[0]))

    for band in sorted_bands:
        fluence_val = cumulative_fluence[band]
        # Format large numbers properly
        if fluence_val >= 1e10:
            formatted = f"{fluence_val:.4e}".replace('e+', ' × 10^')
        else:
            formatted = f"{fluence_val:.4f}"
        f.write(f"{band}\t{fluence_val}\n") #formatted

print("Created cumulative_fluence_2020-2025.txt with correct values")
print(f"{sum(cumulative_fluence.values())*0.0001}")
