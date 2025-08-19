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
    ULL.main()

    #Step 2: Create Locator
    create_locator()


if __name__ == "__main__":
    main()