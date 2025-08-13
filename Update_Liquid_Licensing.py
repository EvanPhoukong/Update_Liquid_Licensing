"""
General Pipeline

1. Parse CSV for lines containing Stockton addresses
    - May need to store in datframe, drop every other row

2. Access the gdb and the layer

3. For each line in datframe, update corresponding feature in layer

"""
from tkinter import filedialog
import pandas as pd
import numpy as np
import arcpy

#Access geodatabase and allow editing of contents
print("Please select the geodatabase to access.")
arcpy.env.workspace = filedialog.askdirectory()
layer = "LiquorLicenseLocations"
arcpy.env.overwriteOutput = True

#Initialize layer and update cursor
fc = arcpy.env.workspace + '\\' + layer
cursor = arcpy.UpdateCursor(fc)

def extract_stockton_addresses() -> pd.DataFrame:
    """
    Extract Stockton addresses from CSV and store in dataframe for processing
    """

    #Read CSV into a dataframe
    print("Please select the CSV of liquor licenses to process.")
    df = pd.read_csv(filedialog.askopenfilename(), skiprows=1)

    #Ensure uniform formatting in city columns
    df['Mail City'] = df['Mail City'].str.upper()
    df['Prem City'] = df['Prem City'].str.upper()
    df['Mail City'] = df['Mail City'].str.strip()
    df['Prem City'] = df['Prem City'].str.strip()

    #Keep rows that pertain to Stockton
    condition = (df['Prem City'] == "STOCKTON") | (df['Mail City'] == "STOCKTON")
    df = df.loc[condition]
    print(df)
    return df

def update_feature(feature: pd.DataFrame) -> None:
    pass

def main():
    df = extract_stockton_addresses()
    for feature in df.values:
        update_feature(feature)

if __name__ == "__main__":
    main()