import pandas as pd
import numpy as np
import configparser

config = configparser.ConfigParser()
config.read('simulation.config')

GAMMA = 2.5
BINS_PER_BAND = 10

# Read cumulative fluence data
df = pd.read_csv('cumulative_fluence_2020-2025.txt', sep='\t', names=['Energy Band', 'Fluence'], skiprows=1)
# ... rest of fluence_to_prob.py code remains the same ...

# Read cumulative fluence data
df = pd.read_csv(
    'cumulative_fluence_2020-2025.txt',
    sep='\t',
    names=['Energy Band', 'Fluence'],
    skiprows=1
)
df['Fluence'] = df['Fluence'].astype(float)

spectrum_data = []

def process_band(band, fluence):
    """Distribute fluence across sub-bins using power-law weighting"""
    e_start, e_end = map(float, band.split('-'))

    # Create sub-bins with proper energy spacing
    sub_bins = np.linspace(e_start, e_end, BINS_PER_BAND + 1)
    bin_widths = np.diff(sub_bins)
    midpoints = sub_bins[:-1] + bin_widths/2

    # Power-law weighting (E^-γ)
    weights = midpoints ** -GAMMA
    norm_weights = weights / weights.sum()

    # Distribute fluence
    for energy, weight in zip(midpoints, norm_weights):
        spectrum_data.append((energy, fluence * weight))

# Process all energy bands
for _, row in df.iterrows():
    process_band(row['Energy Band'], row['Fluence'])

# Create DataFrame and normalize probabilities
df_spectrum = pd.DataFrame(spectrum_data,
                          columns=['Energy (MeV)', 'Probability'])
total_fluence = df_spectrum['Probability'].sum()
df_spectrum['Probability'] = df_spectrum['Probability'] / total_fluence

# Format numbers without scientific notation
def format_float(value):
    """Convert float to string without scientific notation"""
    s = f"{value:.15f}"  # Format with 10 decimal places
    # Remove trailing zeros and potential . at end
    return s.rstrip('0').rstrip('.') if '.' in s else s

# Save Grasshopper-compatible spectrum
with open('input_spectrum.txt', 'w') as f:
    for energy, prob in df_spectrum.sort_values('Energy (MeV)').values:
        f.write(f"{format_float(energy)}\t{format_float(prob)}\n")

print("Created input_spectrum.txt with Grasshopper-compatible formatting")
