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
arcpy.env.workspace = r"C:\Users\ephoukong\OneDrive - City of Stockton\Desktop\Training_Data\DB01_bak_20231018.gdb"
#arcpy.env.workspace = filedialog.askdirectory()
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
    file_path = r"C:\Users\ephoukong\OneDrive - City of Stockton\Desktop\WeeklyExport_CSV\ABC_WeeklyDataExport.csv"
    #file_path = filedialog.askopenfilename()
    csv_path = os.path.dirname(file_path) + '\\' + 'filtered.csv'
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
    reference_data = [["Addresses", "PointAddress"]]

    field_mapping = ["PointAddress.HOUSE_NUMBER Addresses.AddressNumber",
                    # "PointAddress.PREFIX_DIRECTION Addresses.StreetDirectional",
                    "PointAddress.STREET_NAME Addresses.StreetName",
                    # "PointAddress.SUFFIX_TYPE Addresses.StreetType",
                    "PointAddress.FULL_STREET_NAME Addresses.FullAddress",
                    # "PointAddress.UNIT Addresses.Suite",
                    "PointAddress.CITY Addresses.City",
                    "PointAddress.REGION Addresses.State"]
    
    locator = r"C:\GIS\Project\ABCLocator.loc"
    language = "ENG"

    #Delete old locator if it exists
    if os.path.exists(locator):
        os.remove(locator)
    
    os.makedirs(os.path.dirname(locator), exist_ok=True)

    #Create Locator
    arcpy.geocoding.CreateLocator(country_code, reference_data, field_mapping, locator, language)

    return locator

def geocode_addresses(table: str, locator: str) -> str:
    """
    Create a feature layer of address points given a table of addresses and locator.
    """

    #Set the parameters
    fields =  'Address "Prem Addr 1" VISIBLE NONE;' \
            + 'Address2 "Prem Addr 2" VISIBLE NONE;' \
            + 'Address3 <None> VISIBLE NONE;' \
            + 'Neighborhood <None> VISIBLE NONE;' \
            + 'City "Prem City" VISIBLE NONE;' \
            + 'Subregion <None> VISIBLE NONE;' \
            + 'Region District VISIBLE NONE;' \
            + 'Postal "Prem Zip" VISIBLE NONE;'\
            + 'PostalExt <None> VISIBLE NONE;' \
            + 'CountryCode <None> VISIBLE NONE;'
    
    layer = arcpy.env.workspace + '\\' + 'ABC_Geocoded_Addresses'

    #Geocode the addresses
    arcpy.geocoding.GeocodeAddresses(table, locator, fields, layer)

    return layer


def extract_unmatched_addresses(addrs) -> None:
    """
    Extract unmatched addresses into table.
    """

    #Set the parameters
    table = arcpy.env.workspace + '\\' + 'Unmatched_addresses'

    where = "ABC_Geocoded_Addresses.STATUS = 'U'"

    #Geocode the addresses
    arcpy.management.MakeQueryTable(addrs, table, where_clause=where)

    return table


def main() -> None:

    #Step 1: Filter CSV
    csv = filter_csv()
    print("CSV DONE")

    #Step 2: Create Locator
    locator = create_locator()
    print("LOCATOR DONE")

    #Step 3: Geocode Addresses
    abc_addrs = geocode_addresses(csv, locator)
    print("GEOCODE DONE")

    #Step 4: Extract unmatched addresses into table
    queryTable = extract_unmatched_addresses(abc_addrs)
    print("QUERYTABLE DONE")
    print(queryTable)

    #Remove intermediate layers
    # os.remove(csv)
    # os.remove(locator)
    # os.remove(abc_addrs)
    # os.remove(queryTable)


if __name__ == "__main__":
    main()