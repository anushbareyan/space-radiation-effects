For this program, you need [**grasshopper**](https://github.com/ustajan/grasshopper) to run simulations. Please follow the instructions to install it first, then come back.

## Manual 

To run the program manually, use the notebook:

**`Final_Radiation_effects_on_copper.ipynb`**

Run all the cells except the last one, get the input_spectrum.txt file(put in your grasshopper simulation directory), and the number of simulations(change the .gdml file <constant name="EventsToRun" value="{number of simulations}"/> ). Then, simulate in Grasshopper, and put the output.dat file back in the notebook, change the name in the last cell, and run.

An example of gdml file needed to run grasshopper is copper.gdml

## Automated (easier to use)

do

pip install netCDF4 numpy scipy matplotlib pandas bs4 requests

To use the automated program created in the complete_program directory, after downloading grasshopper and setting it up(add to PATH), git clone this repository. Go into complete_program directory, then run run_simulation.py. The program will ask for the dataset link, the number of years of the dataset to download(or days, or months), the scaling factor, to which the program will scale the results, and the copper dimensions(nm).

Example usage: 

**`python3 run_simulation.py   --length 100   --width 10000   --thickness 10   --years 2020   --months 1   --days 1   --url https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l1b/seis-l1b-sgps --scale_factor 365`**

This downloads 1 day of data(Jan 1, 2020 proton observations), scales it to 1 year, runs a simulation in grasshopper, and gives the resistance change in 1 year(assuming that the fluence for each day of the  year was the same as the downloaded day). Tested for GOES-16_SEISS_SGPS Data.

Please refer to this site to learn more about what this program does and the algorithms it uses.

https://anushbareyan.github.io/copper-radiation-site/
