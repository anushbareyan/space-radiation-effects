# run_simulation.py (MAIN EXECUTABLE)
import os
import subprocess
import configparser
import argparse

def check_data_exists(years):
    """Check if data directories exist and contain .nc files"""
    base_dir = "goes16_data"
    if not os.path.isdir(base_dir):
        return False

    for year in years:
        year_dir = os.path.join(base_dir, str(year))
        if not os.path.isdir(year_dir):
            return False
        # Check for at least one .nc file in the year directory
        if not any(f.endswith('.nc') for f in os.listdir(year_dir)):
            return False
    return True

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Radiation Damage Simulation Pipeline')
    parser.add_argument('--length', type=float, required=True, help='Copper length in nm')
    parser.add_argument('--width', type=float, required=True, help='Copper width in nm')
    parser.add_argument('--thickness', type=float, required=True, help='Copper thickness in nm')
    parser.add_argument('--years', type=str, default='2020,2025', help='Years to analyze')
    parser.add_argument('--scale_years', type=float, default=1.0, help='Scaling factor for proton count based on years')
    args = parser.parse_args()

    # Process years
    years = list(map(int, args.years.split(',')))
    YEARS = range(years[0], years[1]+1)

    # Create config file with parameters
    config = configparser.ConfigParser()
    config['DIMENSIONS'] = {
        'length_nm': args.length,
        'width_nm': args.width,
        'thickness_nm': args.thickness
    }
    config['SIMULATION'] = {
        'years': args.years,
        'base_url': 'https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l1b/seis-l1b-sgps'
    }
    config['SCALING'] = {
        'scale_years': str(args.scale_years)
    }
    with open('simulation.config', 'w') as configfile:
        config.write(configfile)

    # Check existing data
    if check_data_exists(YEARS):
        print("\nExisting data found. Skipping download.")
        steps = [
            ('create_fluence_data.py', []),
            ('fluence_to_prob.py', []),
            ('create_gdml.py', []),
            ('analyze_output.py', [])
        ]
    else:
        print("\nNo existing data found. Starting fresh download.")
        steps = [
            ('download_db.py', []),
            ('create_fluence_data.py', []),
            ('fluence_to_prob.py', []),
            ('create_gdml.py', []),
            ('analyze_output.py', [])
        ]

    # Execute pipeline steps
    for script, extra_args in steps:
        print(f"\n=== Running {script} ===")
        cmd = ['python3', script] + extra_args
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"Error running {script}")
            exit(1)
    start_year, end_year = map(int, args.years.split(','))
    actual_years = end_year - start_year + 1
    scaled_years = int(actual_years * args.scale_years)

    # Add Grasshopper execution after GDML generation
    grasshopper_cmd = [
        'grasshopper',
        f'copper_{args.length}_{args.thickness}nm_omni.gdml',
        f'out_{args.length}_{args.thickness}nm_{scaled_years}_omni.gdml'
    ]

    print("\n=== Running Grasshopper Simulation ===")
    try:
        subprocess.run(grasshopper_cmd, check=True)
    except Error:
        print("grasshopper not installed")
if __name__ == "__main__":
    main()
