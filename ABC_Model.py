"""
General Pipeline:

    1. Filter CSV for StocktonParcel Area (Call Function)

    2. Create Locator

    3. Geocode Addresses

    4. Make Query Table
        4.5. Convert table to Excel

    5. Update LiquorLicenseLocations
        -Truncate the table so only the metadata remains
            -All data points should be removed
        -Append the geocoded addresses that had a match to the layer

"""

from tkinter import filedialog
import pandas as pd
import requests, arcpy, zipfile, io, os

print("Please select the geodatabase to access.")
arcpy.env.workspace = filedialog.askdirectory()
arcpy.env.overwriteOutput = True
layer = "LiquorLicenseLocations"


def extract_CSV_from_link() -> str:
    """
    Extract ABC CSV from link
    """

    #Specify download url and where to save the file
    url = r"https://www.abc.ca.gov/wp-content/uploads/WeeklyExport_CSV.zip"
    save_to = os.getcwd()

    #Obtain the zip from the url
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, stream=True, verify=False, headers=headers)
    zip = zipfile.ZipFile(io.BytesIO(res.content))
    file = zip.namelist()[0]

    #Remove CSV if it already exists
    file_path = os.path.join(save_to, file)
    if os.path.exists(file_path):
        os.remove(file_path)

    #Extract the zip file
    saved_csv_path = zip.extract(file, save_to)

    return saved_csv_path


def filter_csv(file_path: str) -> str:
    """
    Filter out all features not within StocktonParcelArea from CSV.
    """

    #Read CSV into a dataframe
    csv_path = os.path.join(os.path.dirname(file_path), 'filtered.csv')
    df = pd.read_csv(file_path, skiprows=1)

    #Delete old csv if it exists
    if os.path.exists(csv_path):
        os.remove(csv_path)

    #Ensure uniform formatting in city columns
    df['Mail City'] = df['Mail City'].str.upper()
    df['Prem City'] = df['Prem City'].str.upper()
    df['Mail City'] = df['Mail City'].str.strip()
    df['Prem City'] = df['Prem City'].str.strip()

    #Keep rows that pertain to Stockton
    zips = [95202, 95203, 95204, 95205, 95206, 95207, 95209, 95210, 95211, 95212, 95215, 95219, 95231, 95240, 95242, 95330, 95336]
    condition = (df['Prem City'] == "STOCKTON") | (df['Prem City'] == "FRENCH CAMP") | (df['Prem City'] == "LODI") # | (df['Mail City'] == "STOCKTON")
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
    
    layer = os.path.join(arcpy.env.workspace, 'ABC_Geocoded_Addresses')
    output_fields = "MINIMAL"

    #Geocode the addresses
    arcpy.geocoding.GeocodeAddresses(table, locator, fields, layer, output_fields=output_fields)

    return layer


def extract_unmatched_addresses(addrs: str) -> None:
    """
    Extract unmatched addresses into table.
    """

    #Set the parameters
    where_clause = "ABC_Geocoded_Addresses.STATUS = 'U'"

    #Query the table for unmatched addresses
    table, count= arcpy.management.SelectLayerByAttribute(addrs, where_clause=where_clause)
    
    return table, count


def convert_table_to_excel(table: str, folder: str) -> None:
    """
    Convert the table into an Excel Spreadsheet
    """

    #Set the parameter
    out_table = os.path.join(folder, "Unmatched_Addresses.xlsx")

    #Convert the table into an Excel Spreadsheet
    arcpy.conversion.TableToExcel(table, out_table)

    return out_table


def extract_matched_addresses(addrs: str) -> None:
    """
    Extract matched addresses into table.
    """

    #Set the parameters
    where_clause = "ABC_Geocoded_Addresses.STATUS = 'M' Or " \
                 + "ABC_Geocoded_Addresses.STATUS = 'T'"

    #Query the table for unmatched addresses
    table, count = arcpy.management.SelectLayerByAttribute(addrs, where_clause=where_clause)
    arcpy.management.DeleteField(table, "Status")

    return table, count


def create_field_map(addrs_name: str, target_name: str, type: str) -> None:
    """
    Create field maps give the feature attributes to combine
    """

    addrs = "ABC_Geocoded_Addresses"
    target = "LiquorLicenseLocations"

    fldMap = arcpy.FieldMap()

    fldMap.addInputField(addrs, addrs_name)
    fldMap.addInputField(target, target_name)

    column = fldMap.outputField
    column.name, column.aliasName, column.type = target_name, target_name, type
    fldMap.outputField = column

    return fldMap


def update_ABC_Layer(addrs: str) -> None:
    """
    Update the LiquoreLicenseLocations layer with the new addresses
    """

    target = layer

    #Create Field Mappings Object and Set Parameters
    fieldMappings = arcpy.FieldMappings()
    fieldMappings.addTable(target)

    #Specify the fields to match and their corresponding type
    fields = [("License_Type", "LicenseCode", "SHORT"),
              ("File_Number", "FileNumber", "LONG"),
              ("Type_Orig_Iss_Date", "OriginalIssueDate", "DATE"),
              ("Expir_Date", "ExpirationDate", "DATE"),
              ("DBA_Name", "PremiseName", "TEXT"),
              ("Prem_Addr_1", "PremiseAddress", "TEXT"),
              ("Prem_Addr_2", "PremiseAddress2", "TEXT"),
              ("Primary_Name", "OwnerName", "TEXT"),
              ("Prem_Zip", "PremiseZipcode", "TEXT"),
              ("Mail_Addr_1", "MailAddress", "TEXT"),
              ("Mail_Addr_2", "MailAddress2", "TEXT"),
              ("Mail_City", "MailCity", "TEXT"),
              ("Mail_State", "MailState", "TEXT"),
              ("Mail_Zip", "MailZipcode", "TEXT"),
              ("Prem_Census_Tract__", "PremiseCensusTract", "TEXT"),
              ("Lic_or_App", "LicenseType", "TEXT"),
              ("Type_Status", "Status", "TEXT"),]
            #   ("Shape", "Shape", "GEOMETRY")]
    
    schema_type = "NO_TEST"

    #Add field maps
    for (name, alias, type) in fields:
        fieldMappings.addFieldMap(create_field_map(name, alias, type))

    #Append the geocoded addresses to LiquorLicenseLocations
    arcpy.management.Append(addrs, target, schema_type, fieldMappings)


def main() -> None:

    #Step 1: Extract CSV from link
    raw_csv = extract_CSV_from_link()
    print("\n1: Extract the CSV to be processed from the url")

    #Step 2: Filter CSV
    filtered_csv = filter_csv(raw_csv)
    print("2: CSV Filtered for StocktonParcelArea Addresses")

    #Step 3: Create Locator
    locator = create_locator()
    print("3: Created Point Address Locator")

    #Step 4: Geocode Addresses
    abc_addrs = geocode_addresses(filtered_csv, locator)
    print("4: Finished Geocoding Addresses")

    #Step 5: Extract unmatched addresses into table
    unmatchedTable, count = extract_unmatched_addresses(abc_addrs)
    print(f"5: Created Unmatched Addresses Table. The total number of unmatched addresses is {count}.")

    #Step 6: Convert the table into an Excel Worksheet
    excel = convert_table_to_excel(unmatchedTable, os.path.dirname(filtered_csv))
    print("6: Unmatched Addresses Table Converted To Excel Worksheet")
    print(f"\nThe UNMATCHED ADDRESSES can be found HERE: {excel}\n")

    #Step 7: Extracted matched addresses into table
    matchedTable, count = extract_matched_addresses(abc_addrs)
    print(f"7: Created Matched Addresses Table. The total number of matched addresses is {count}.")

    #Step 8: Truncate the LiquorLicenseLocations table
    arcpy.management.TruncateTable(layer)
    print("8: Truncated LiquorLicenseLocations")

    #Step 9: Append geocoded addresses to LiquorLicenseLocations
    update_ABC_Layer(matchedTable)
    print("9: LiquorLicenseLocations appended with Geocoded Addresses")

    #Step 10: Remove intermediate layers
    os.remove(raw_csv)
    os.remove(filtered_csv)
    os.remove(locator)
    arcpy.management.Delete(abc_addrs)
    arcpy.management.Delete(unmatchedTable)
    arcpy.management.Delete(matchedTable)
    print("10: Intermediate layers removed from File System")
    print("Successfully Updated LiquorLicenseLocations")


if __name__ == "__main__":
    main()