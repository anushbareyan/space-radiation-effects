from netCDF4 import Dataset
import numpy as np
from pathlib import Path
from collections import defaultdict
import configparser

import sys

config = configparser.ConfigParser()
config.read('simulation.config')


length = float(config['DIMENSIONS']['length_nm'])
width = float(config['DIMENSIONS']['width_nm'])
thickness = float(config['DIMENSIONS']['thickness_nm'])


years = list(map(int, config['SIMULATION']['years'].split(',')))  # e.g. "2020,2025"
months = list(map(int, config['SIMULATION'].get('months', '1,12').split(',')))
days = list(map(int, config['SIMULATION'].get('days', '1,31').split(',')))

year_range = f"{years[0]}-{years[1]}"
month_range = f"{months[0]}-{months[1]}"
day_range = f"{days[0]}-{days[1]}"

BASE_DIR = 'goes16_data/'


output_filename = f"cumulative_fluence_{year_range}_{month_range}_{day_range}.txt"


YEARS = range(years[0], years[1] + 1)


cumulative_fluence = defaultdict(float)


energy_bins = {
    'T1': [(1.0, 1.9), (1.9, 2.3), (2.3, 3.4), (3.4, 6.5), (6.5, 12.0), (12.0, 25.0)],
    'T2': [(25.0, 40.0), (40.0, 80.0)],
    'T3': [(83.0, 99.0), (99.0, 118.0), (118.0, 150.0), (150.0, 275.0), (275.0, 500.0)]
}

scaling_factor = 4 * np.pi * 1000  # 4π * 1000


file_paths = []
for year in YEARS:
    year_dir = Path(BASE_DIR) / str(year)
    if year_dir.exists():
        file_paths.extend(sorted(year_dir.glob('*.nc')))

if not file_paths:
    print("No netCDF files found in the specified year range.")
    sys.exit(1)

#Initialize total_fluence dictionary for each telescope and directions (+X and -X)
total_fluence = {}
with Dataset(file_paths[0], 'r') as nc:
    for t in range(3):
        var = nc[f'T{t+1}_DifferentialProtonFluxes']
        _, _, nbin = var.shape
        #Shape (2, nbin), nbin energy bins
        total_fluence[f'T{t+1}'] = np.zeros((2, nbin), dtype=np.float64)

def accumulate_file(fp):
    try:
        with Dataset(fp, 'r') as nc:
            for t in range(3):
                tel = f'T{t+1}'
                flux = nc[f'{tel}_DifferentialProtonFluxes'][:]  # shape (time, sectors=2, nbin)
                # Sum over time (all timesteps) -> shape (2, nbin)
                daily = np.ma.filled(flux, 0.0).sum(axis=0)
                total_fluence[tel] += daily
    except Exception as e:
        print(f"Error processing file {fp}: {str(e)}")

# Process all files
for fp in file_paths:
    accumulate_file(fp)

#Sum +X and -X directions for each telescope
summed_flux = []
#Number of energy bins per telescope (for slicing)
energy_bin_counts = [6, 2, 5]

for i, tel in enumerate(['T1', 'T2', 'T3']):
    #sum directions axis (0 and 1)
    summed = total_fluence[tel][0, :] + total_fluence[tel][1, :]

    summed_flux.append(summed[:energy_bin_counts[i]])

#Compute cumulative fluence using energy bin widths and scaling
for i, tel in enumerate(['T1', 'T2', 'T3']):
    for flux, (low, high) in zip(summed_flux[i], energy_bins[tel]):
        width = high - low
        fluence = flux * scaling_factor * width
        band_key = f"{low:.1f}-{high:.1f}"
        cumulative_fluence[band_key] += fluence


with open(output_filename, 'w') as f:
    f.write("Energy Band (MeV)\tTotal Fluence (particles/cm²)\n")
    for band in sorted(cumulative_fluence.keys(), key=lambda x: float(x.split('-')[0])):
        f.write(f"{band}\t{cumulative_fluence[band]:.1f}\n")

print(f"Created {output_filename} with correct values")
