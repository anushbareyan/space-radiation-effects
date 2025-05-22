import os
import requests
import numpy as np
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import configparser


config = configparser.ConfigParser()
config.read('simulation.config')

BASE_URL = config['SIMULATION']['base_url']
YEAR_RANGE = list(map(int, config['SIMULATION']['years'].split(',')))
MONTH_RANGE = list(map(int, config['SIMULATION']['months'].split(',')))
DAY_RANGE = list(map(int, config['SIMULATION']['days'].split(',')))

YEARS = range(YEAR_RANGE[0], YEAR_RANGE[1] + 1)
MONTHS = range(MONTH_RANGE[0], MONTH_RANGE[1] + 1)
SAMPLE_DAYS = DAY_RANGE[1] - DAY_RANGE[0] + 1

def create_year_folders():
    for year in YEARS:
        os.makedirs(f"goes16_data/{year}", exist_ok=True)

def get_monthly_files(year, month):
    url = f"{BASE_URL}/{year}/{month:02d}/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return [link['href'] for link in soup.find_all("a")
               if link['href'].endswith('.nc') and 'ops_seis-l1b-sgps' in link['href']]
    except Exception as e:
        print(f"Error fetching {year}-{month:02d}: {str(e)}")
        return []

def download_file(year, month, day_file):
    url = f"{BASE_URL}/{year}/{month:02d}/{day_file}"
    local_path = f"goes16_data/{year}/{day_file}"

    if not os.path.exists(local_path):
        try:
            with requests.get(url, stream=True, timeout=15) as response:
                response.raise_for_status()
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"Downloaded {year}/{month:02d}/{day_file}")
            return True
        except Exception as e:
            print(f"Failed {year}/{month:02d}/{day_file}: {str(e)}")
            return False
    return True

def process_year_month(year, month):
    files = get_monthly_files(year, month)
    if not files:
        return 0


    sample_indices = np.linspace(0, len(files) - 1, min(SAMPLE_DAYS, len(files)), dtype=int)
    sampled_files = [files[i] for i in sample_indices]

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda f: download_file(year, month, f), sampled_files))

    return sum(results)

def main():
    create_year_folders()
    total_downloaded = 0

    for year in YEARS:
        for month in MONTHS:
            downloaded = process_year_month(year, month)
            total_downloaded += downloaded

    print(f"\nDownload complete! {total_downloaded} files saved in year folders.")

if __name__ == "__main__":
    main()
