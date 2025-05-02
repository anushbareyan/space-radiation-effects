import os
import requests
import numpy as np
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import configparser

config = configparser.ConfigParser()
config.read('simulation.config')

# Configuration from file
BASE_URL = config['SIMULATION']['base_url']
YEARS = list(map(int, config['SIMULATION']['years'].split(',')))
YEARS = range(YEARS[0], YEARS[1]+1)
SAMPLE_DAYS_PER_MONTH = 31

def create_year_folders():
    for year in YEARS:
        os.makedirs(f"goes16_data/{year}", exist_ok=True)

# ... rest of download_db.py code remains the same ...
def get_monthly_files(year, month):
    """Get list of available daily files for a given month"""
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
    """Download a single daily file to its year folder"""
    day = day_file[20:22]  # Extract day from filename
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
    """Process one month's data with sampling"""
    files = get_monthly_files(year, month)
    if not files:
        return 0

    # Sample evenly across the month
    sample_indices = np.linspace(0, len(files)-1, SAMPLE_DAYS_PER_MONTH, dtype=int)
    sampled_files = [files[i] for i in sample_indices]

    # Download sampled files in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda f: download_file(year, month, f), sampled_files))

    return sum(results)

def main():
    create_year_folders()
    total_downloaded = 0

    for year in YEARS:
        for month in range(1, 13):
            downloaded = process_year_month(year, month)
            total_downloaded += downloaded

    print(f"\nDownload complete! {total_downloaded} files saved in year folders.")

if __name__ == "__main__":
    main()
