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

print("Please select the geodatabase to access.")
arcpy.env.workspace = filedialog.askdirectory()
layer = "LiquorLicenseLocations"
arcpy.env.overwriteOutput = True

#Initialize connection to layer and create update cursor
fc = arcpy.env.workspace + '\\' + layer
cursor = arcpy.UpdateCursor(fc)

def filter_csv() -> str:
    """
    Filter out all features not within StocktonParcelArea from CSV.
    """

    #Read CSV into a dataframe
    print("Please select the CSV of liquor licenses to process.")
    file_path = filedialog.askopenfilename()
    csv_path = os.path.dirname(file_path) + '\\' + 'filtered_csv'
    df = pd.read_csv(file_path, skiprows=1)

    #Ensure uniform formatting in city columns
    df['Mail City'] = df['Mail City'].str.upper()
    df['Prem City'] = df['Prem City'].str.upper()
    df['Mail City'] = df['Mail City'].str.strip()
    df['Prem City'] = df['Prem City'].str.strip()

    #Keep rows that pertain to Stockton
    zips = [95202, 95203, 95204, 95205, 95206, 95207, 95209, 95210, 95211, 95212, 95215, 95219, 95231, 95240, 95242, 95330, 95336]
    condition = (df['Prem City'] == "STOCKTON") | (df['Prem City'] == "FRENCH CAMP") | (df['Prem City'] == "LODI") | (df['Mail City'] == "STOCKTON")
    df = df.loc[condition]
    df.to_csv(csv_path, index=False)

    return csv_path


def create_locator() -> str:
    """
    Create a point address locator.
    """

    #Set the parameters
    country_code = "USA"
    reference_data = arcpy.env.workspace + '\\' + "Addresses"
    field_mapping =   'HouseNumber FROM AddressNumber,' \
                    + 'PrefixDirection FROM StreetDirectional,' \
                    + 'StreetName FROM StreetName,' \
                    + 'SuffixType FROM StreetType,' \
                    + 'FullStreeetName FROM FullAddress,' \
                    + 'Unit FROM Suite, City FROM City,' \
                    + 'State FROM State'
    locator = r"C:\GIS\Project\ABCLocator.loc"

    #Delete old locator if it exists
    if os.path.exists(locator):
        os.remove(locator)

    #Create Locator
    arcpy.geocoding.CreateLocator(country_code, reference_data, field_mapping, locator)

    return locator

def geocode_addresses(table: str, locator: str) -> str:
    """
    Create a feature layer of address points given a table of addresses and locator.
    """

    #Set the parameters
    fields =  'Address "Prem Addr 1" VISIBLE NONE;' \
            + 'Address2 "Prem Addr 2" VISIBLE NONE;' \
            + 'City "Prem City" VISIBLE NONE;' \
            + 'Region District VISIBLE NONE;' \
            + 'Postal "Prem Zip" VISIBLE NONE;'
    layer = arcpy.env.workspace + '\\' + 'ABC_Addresses'

    #Geocode the addresses
    arcpy.geocoding.GeocodeAddresses(table, locator, fields, layer)

    return layer


def extract_unmatched_addresses(addrs):
    """
    Extract unmatched addresses into table.
    """

    #Set the parameters
    table = arcpy.env.workspace + '\\' + 'unmatched_addresses'

    #Geocode the addresses
    arcpy.management.MakeQueryTable(addrs, table)

    return table


def main() -> None:

    #Step 1: Filter CSV
    csv = filter_csv()

    #Step 2: Create Locator
    locator = create_locator()

    #Step 3: Geocode Addresses
    abc_addrs = geocode_addresses(csv, locator)

    #Step 4: Extract unmatched addresses into table
    queryTable = extract_unmatched_addresses(abc_addrs)

    #Remove intermediate layers
    os.remove(csv)
    os.remove(locator)
    os.remove(abc_addrs)
    os.remove(queryTable)


if __name__ == "__main__":
    main()