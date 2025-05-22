import pandas as pd
import numpy as np
import configparser

config = configparser.ConfigParser()
config.read('simulation.config')

GAMMA = 3.0


years = list(map(int, config['SIMULATION']['years'].split(',')))
months = list(map(int, config['SIMULATION'].get('months', '1,12').split(',')))
days = list(map(int, config['SIMULATION'].get('days', '1,31').split(',')))

year_range = f"{years[0]}-{years[1]}"
month_range = f"{months[0]}-{months[1]}"
day_range = f"{days[0]}-{days[1]}"

fluence_filename = f"cumulative_fluence_{year_range}_{month_range}_{day_range}.txt"


df = pd.read_csv(
    fluence_filename,
    sep='\t',
    names=['Energy Band', 'Fluence'],
    skiprows=1
)
df['Fluence'] = df['Fluence'].astype(float)


energy_bands = [
    [(1.0, 1.9), (1.9, 2.3), (2.3, 3.4), (3.4, 6.5), (6.5, 12.0), (12.0, 25.0)],
    [(25.0, 40.0), (40.0, 80.0)],
    [(83.0, 99.0), (99.0, 118.0), (118.0, 150.0), (150.0, 275.0), (275.0, 500.0)]
]


fluence_dict = {
    tuple(map(float, band.split('-'))): fluence
    for band, fluence in zip(df['Energy Band'], df['Fluence'])
}


spectrum = []

for tier in energy_bands:
    for e_low, e_high in tier:
        fluence = fluence_dict.get((e_low, e_high), 0.0)
        sub_bins = np.logspace(np.log10(e_low), np.log10(e_high), num=11)
        mid_points = np.sqrt(sub_bins[:-1] * sub_bins[1:])
        bin_widths = sub_bins[1:] - sub_bins[:-1]

        weights = mid_points ** -GAMMA
        weights /= weights.sum()  #normalize within band

        for mp, w, bw in zip(mid_points, weights, bin_widths):
            spectrum.append((mp, fluence * w, bw))

# Normalize spectrum to get PDF
energies, counts, widths = zip(*spectrum)
total_counts = sum(counts)
pdf_values = [c / (total_counts * w) for c, w in zip(counts, widths)]

with open('input_spectrum.txt', 'w') as f:
    for e, pdf in sorted(zip(energies, pdf_values), key=lambda x: x[0]):
        f.write(f"{e:.6f}\t{pdf:.6e}\n")

# Print verification
integral = sum(pdf * w for pdf, w in zip(pdf_values, widths))
print(f"PDF integral: {integral:.6f} (should be approx 1.0)")
print(f"Energy range: {min(energies):.1f}-{max(energies):.1f} MeV")
print(f"Number of bins: {len(energies)}")
