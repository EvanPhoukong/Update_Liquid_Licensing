"""
General Pipeline

1. Parse CSV for lines containing Stockton addresses
    - May need to store in datframe, drop every other row

1. UPDATE: Need to account for the sphere of influence of Stockton
    - Iterate through each line and see which one clips with sphere of influence?
    - Possible use of locators here

2. Access the gdb and the layer

3. For each line in dataframe, update corresponding feature in layer
    -Locator could be used to access every address possible, if iteration is not efficient

"""
from tkinter import filedialog
import pandas as pd
import numpy as np
import arcpy

#Initialize connection to geodatabase and allow editing of contents
print("Please select the geodatabase to access.")
arcpy.env.workspace = r"C:\Users\ephoukong\OneDrive - City of Stockton\Desktop\Training_Data\DB01_bak_20231018.gdb"
layer = "LiquorLicenseLocations"
arcpy.env.overwriteOutput = True

#Initialize connection to layer and create update cursor
fc = arcpy.env.workspace + '\\' + layer
cursor = arcpy.UpdateCursor(fc)

def create_condition():
    pass

def extract_stockton_addresses() -> pd.DataFrame:
    """
    Extract Stockton addresses from CSV and store in dataframe for processing
    """

    #Read CSV into a dataframe
    print("Please select the CSV of liquor licenses to process.")
    #df = pd.read_csv(filedialog.askopenfilename())
    df = pd.read_csv(arcpy.GetParameterAsText(0), skiprows=1)

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
    print(df)
    return df

def update_feature(feature: pd.DataFrame) -> None:
    pass

def main():
    df = extract_stockton_addresses()
    #df.to_csv(filedialog.askopenfilename(), index=False)
    df.to_csv(arcpy.GetParameterAsText(1), index=False)
    # for feature in df.values:
    #     update_feature(feature)

if __name__ == "__main__":
    main()