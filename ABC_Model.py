"""
General Pipeline:

    1. Filter CSV for StocktonParcel Area (Call Function)
    2. Create Locator
    3. Geocode Addresses
    4. Make Query Table
        4.5. Convert table to Excel
    5. Make a copy the addresses table
        --TENTATIVE--
        5.5. Merge the copy with the LiquorLicenseLocations
"""


from tkinter import filedialog
import pandas as pd
import numpy as np
import arcpy
import Update_Liquid_Licensing as ULL
import os


arcpy.env.workspace = r"C:\Users\ephoukong\OneDrive - City of Stockton\Desktop\Training_Data\DB01_bak_20231018.gdb"
layer = "LiquorLicenseLocations"
arcpy.env.overwriteOutput = True

#Initialize connection to layer and create update cursor
fc = arcpy.env.workspace + '\\' + layer
cursor = arcpy.UpdateCursor(fc)

def filter_csv() -> None:
    """
    Extract Stockton addresses from CSV and store in dataframe for processing
    """

    #Read CSV into a dataframe
    print("Please select the CSV of liquor licenses to process.")
    file_path = filedialog.askopenfilename()
    df = pd.read_csv(file_path, skiprows=1)

    #Ensure uniform formatting in city columns
    df['Mail City'] = df['Mail City'].str.upper()
    df['Prem City'] = df['Prem City'].str.upper()
    df['Mail City'] = df['Mail City'].str.strip()
    df['Prem City'] = df['Prem City'].str.strip()

    #Keep rows that pertain to Stockton
    zips = [95202, 95203, 95204, 95205, 95206, 95207, 95209, 95210, 95211, 95212, 95215, 95219, 95231, 95240, 95242, 95330, 95336]
    condition = (df['Prem City'] == "STOCKTON") | (df['Prem City'] == "FRENCH CAMP") | (df['Prem City'] == "LODI") | (df['Mail City'] == "STOCKTON")
    #condition = (df['Prem Zip'])
    #| (df['Prem City'] == "FRENCH CAMP") | (df['Prem City'] == "LODI") | (df['Mail City'] == "STOCKTON")
    df = df.loc[condition]
    df.to_csv(os.path.dirname(file_path), index=False)


def create_locator():

    #Set the Parameters
    country_code = "USA"
    reference_data = arcpy.env.workspace +'\\' + "Addresses"
    field_mapping = "HouseNumber FROM AddressNumber, PrefixDirection FROM StreetDirectional, StreetName FROM StreetName, SuffixType FROM StreetType, FullStreeetName FROM FullAddress, Unit FROM Suite, City FROM City, State FROM State"
    locator = r"C:\GIS\Project\ABCLocator.loc"

    #Delete old locator if it exists
    if os.path.exists(locator):
        os.remove(locator)

    #Create Locator
    arcpy.geocoding.CreateLocator(country_code, reference_data, field_mapping, locator)


def main():
    #Step 1: Filter CSV
    filter_csv()

    #Step 2: Create Locator
    create_locator()


if __name__ == "__main__":
    main()