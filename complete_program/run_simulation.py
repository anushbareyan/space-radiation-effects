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
        if not any(f.endswith('.nc') for f in os.listdir(year_dir)):
            return False
    return True

def parse_range(arg):

    parts = list(map(int, arg.split(',')))
    if len(parts) == 1:
        return range(parts[0], parts[0] + 1)
    return range(parts[0], parts[1] + 1)

def main():

    parser = argparse.ArgumentParser(description='Radiation Damage Simulation Pipeline')
    parser.add_argument('--length', type=float, required=True, help='Copper length in nm')
    parser.add_argument('--width', type=float, required=True, help='Copper width in nm')
    parser.add_argument('--thickness', type=float, required=True, help='Copper thickness in nm')
    parser.add_argument('--years', type=str, default='2020,2025', help='Year range (e.g. 2020 or 2020,2022)')
    parser.add_argument('--months', type=str, default='1,12', help='Month range (e.g. 1 or 1,3)')
    parser.add_argument('--days', type=str, default='1,31', help='Day range (e.g. 1 or 1,15)')
    parser.add_argument('--scale_factor', type=float, default=1.0, help='Scaling factor for proton count example, you have data of 1 day scaling 356 would give 1 year result')
    parser.add_argument('--url', type=str, required=True, help='Base URL for downloading GOES-16 data')
    args = parser.parse_args()

    YEARS = parse_range(args.years)
    MONTHS = parse_range(args.months)
    DAYS = parse_range(args.days)

    #create config file
    config = configparser.ConfigParser()
    config['DIMENSIONS'] = {
        'length_nm': args.length,
        'width_nm': args.width,
        'thickness_nm': args.thickness
    }
    config['SIMULATION'] = {
        'years': f"{YEARS.start},{YEARS.stop - 1}",
        'months': f"{MONTHS.start},{MONTHS.stop - 1}",
        'days': f"{DAYS.start},{DAYS.stop - 1}",
        'base_url': args.url
    }
    config['SCALING'] = {
        'scale_factor': str(args.scale_factor)
    }

    with open('simulation.config', 'w') as configfile:
        config.write(configfile)

    if check_data_exists(YEARS):
        print("\nExisting data found. Skipping download.")
        steps = [
            ('create_fluence_data.py', []),
            ('fluence_to_prob.py', []),
            ('create_gdml.py', []),
            ('GRASSHOPPER_SIM', []),
            ('analyze_output.py', [])
        ]
    else:
        print("\nNo existing data found. Starting fresh download.")
        steps = [
            ('download_db.py', []),
            ('create_fluence_data.py', []),
            ('fluence_to_prob.py', []),
            ('create_gdml.py', []),
            ('GRASSHOPPER_SIM', []),
            ('analyze_output.py', [])
        ]
    #Execute scripts in pipeline
    for script, extra_args in steps:
        if script == 'GRASSHOPPER_SIM':
            print("\n=== Running Grasshopper Simulation ===")
            start_year, end_year = YEARS.start, YEARS.stop - 1
            actual_years = end_year - start_year + 1
            scaled_years = int(actual_years * args.scale_factor)
            grasshopper_cmd = [
                'grasshopper',
                f'copper_omni.gdml',
                f'out_omni'
            ]
            try:
                print(grasshopper_cmd)
                subprocess.run(grasshopper_cmd, check=True)
            except Exception:
                print("grasshopper not installed or failed to execute")
                exit(1)
        else:
            print(f"\n=== Running {script} ===")
            cmd = ['python3', script] + extra_args
            result = subprocess.run(cmd, check=False)
            if result.returncode != 0:
                print(f"Error running {script}")
                exit(1)


if __name__ == "__main__":
    main()
