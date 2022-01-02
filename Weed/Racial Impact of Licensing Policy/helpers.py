import pandas as pd
import os
import matplotlib.pyplot as plt
import re
from collections import Counter

def gmap_export_helper(ctract):
    """
    Utility function to quickly generate lists of church and school properties
    from exported MapGeo data.

    *Make sure that the data file structure is correct!!!

    /
        data
            censustract_[]
                censustract_[]_mapgeo_propertyinfo.csv

    Input:
        ctract [string] - list of census tracts to generate exports for.
    
    Output:
        export_df [csv] - exported CSV of church and school property names and addresses.
    """

    # File directory variables
    ctract_dir = "censustract_" + ctract
    filename = "censustract_" + ctract + "_mapgeo_propertyinfo.csv" 

    # Import census tract property data
    df = pd.read_csv(os.path.join("data", ctract_dir , filename), ';')

    # Rename df columns to make them easier to manage
    df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"), inplace=True)

    # Create query_df to store Church and School properties 
    query_df = df.query('{} == "{}" or {} == "{}" or {} == "{}"'\
        .format('property_class', '612', 'property_class', '614', 'property_class', '620'))

    # Begin creating dataframe to export church and school addresses and names
    # for import into Google maps

    # Copy needed data into holder df
    _export_df = pd.DataFrame([query_df.site_address, query_df.billing_info])

    # Save transposed df into export_df
    export_df = _export_df.T

    # Prepare export_df for export
    export_df.reset_index(inplace=True)
    export_df["site_name"] = export_df.billing_info.apply(lambda x: x.replace(",", ""))
    export_df["address"] = export_df.site_address.apply(lambda x: x[0:] + " ALBANY NY")
    export_df.drop(columns=["index", "site_address", "billing_info"], inplace=True)

    # Export dataframe as csv
    export_filename = "censustract_" + ctract + "_mapgeo_propertyinfo_gmapsImport.csv"

    export_df.to_csv(os.path.join("data", ctract_dir, export_filename))


def available_df_generator(ctract, distance):
    """
    Utility function to quickly generate `available_properties` datasets

    *Make sure that the data file structure is correct!!!

    /
        data
            censustract_[]
                censustract_[]_available_properties_[]ft.csv

    Input:
        ctract [str] - list of census tracts to generate exports for.
        distance [str] - abutter distance
    
    Output:
        available_df [csv] - exported CSV of properties outside of abutter range.
    """

    # File directory variables
    ctract_dir = "censustract_" + ctract
    abutter_filename = "censustract_" + ctract + "_mapgeo_" + distance + "ft_abutters.csv"
    tract_total_filename = "censustract_" + ctract + "_mapgeo_propertyinfo.csv" 

    # Import census tract property data
    abutter_df = pd.read_csv(os.path.join("data", ctract_dir , abutter_filename), ';', index_col="Tax ID")
    tract_total_df = pd.read_csv(os.path.join("data", ctract_dir , tract_total_filename), ';', index_col="Tax ID")

    # Rename columns to make them easier to work with
    abutter_df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"), inplace=True)
    tract_total_df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"), inplace=True)

    # Save df indices to lists
    abutter_idx_list = abutter_df.index.tolist()
    tract_tot_idx_list = tract_total_df.index.tolist()

    # Cut out abutter_addresses:
    #   i) IF abutter_address IN tract_dataset THEN add abutter_address to abutter_save_list.
    #   ii) IF tract_dataset_address NOT IN abutter_save_list THEN add tract_dataset_address to available_save_list
    #   iii) Create available_property_dataset by querying available_save_list addresses [if necessary]
    
    abutter_save_list = []
    tract_drop_list = []

    for item in abutter_idx_list:
        if item in tract_tot_idx_list:
            abutter_save_list.append(item)

    for item in tract_tot_idx_list:
        if item in abutter_save_list:
            tract_drop_list.append(item)

    assert len(tract_drop_list) == len(abutter_save_list)

    # Make available_df from non-abutter properties.
    available_df = tract_total_df.drop(index=tract_drop_list)

    # Prepare available_df for export
    available_df.dropna(inplace=True)
    available_df["census_tract"] = ctract

    # Export dataframe as csv
    export_filename = "censustract_" + ctract + "_available_properties_" + distance + "ft.csv"

    available_df.to_csv(os.path.join("data", ctract_dir, export_filename), sep=';')


def available_zones_df_generator(ctract_list, distance_list):

    """
    Utility function to quickly generate tally of zones in
    multiple `available_properties` datasets.

    Focus zone categories are:
    R = residential
    MU = mixed use
    I - industrial

    *Make sure that the data file structure is correct!!!

    /
        data
            censustract_[]
                censustract_[]_available_properties_[]ft.csv

    Input:
        ctract_list [list] - list of census tracts to generate exports for.
        distance_list [list] - list of abbutter distances
    
    Output:
        export_df [df] - exported DataFrame of zone category tallies of
        multiple census tracts' properties.
    """

    holder_dict = {}

    for ctract in ctract_list:
        for distance in distance_list:

            if distance != '0':
                # File directory variables
                ctract_dir = "censustract_" + ctract
                available_properties_filename = "censustract_" + ctract + "_available_properties_" + distance + "ft.csv"
                
                # Import
                ctract_df = pd.read_csv(os.path.join("data", ctract_dir , available_properties_filename), ';')
                
                # Declare zone category dictionary
                zone_dict = {'ctract':'', 'distance':'', 'R':0, 'MU':0, 'I':0}

                # Declare regex search pattern
                #   Searches for zone prefix: MU-NE > MU
                rgx = r'([A-Z]*)'

                # Declare prefix holder list
                holder_list = []

                # Gather prefixes in zoning column
                for item in ctract_df.zoning.values:
                    query = re.match(rgx, item)
                    holder_list.append(query[0])

                # Create Counter object with the prefixes
                c = Counter(holder_list)
                count = c.most_common()

                # Add Counter data to zone_dict
                for item in count:
                    label = item[0]
                    qty = item[1]
                    zone_dict[label] = qty
                    zone_dict['ctract'] = ctract
                    zone_dict['distance'] = distance

                # Add zone_dict data to holder_dict
                holder_dict[ctract + "-" + distance] = {}
                holder_dict[ctract + "-" + distance] = zone_dict

            if distance == '0':
                # Follow the same steps as above. But 0 distances pull in
                # data from all properties in the census tract.

                # File directory variables
                ctract_dir = "censustract_" + ctract
                tract_total_filename = "censustract_" + ctract + "_mapgeo_propertyinfo.csv"
                tract_total_df = pd.read_csv(os.path.join("data", ctract_dir , tract_total_filename), ';')

                zone_dict = {'ctract':'', 'distance':'', 'R':0, 'MU':0, 'I':0}

                rgx = r'([A-Z]*)'
                holder_list = []

                for item in tract_total_df.Zoning.values:
                    query = re.match(rgx, item)
                    holder_list.append(query[0])

                c = Counter(holder_list)
                count = c.most_common()

                for item in count:
                    label = item[0]
                    qty = item[1]
                    zone_dict[label] = qty
                    zone_dict['ctract'] = ctract
                    zone_dict['distance'] = distance

                holder_dict[ctract + "-" + distance] = {}
                holder_dict[ctract + "-" + distance] = zone_dict

    export_df_ = pd.DataFrame(holder_dict)
    export_df = export_df_.T
    
    return export_df


def available_change_df_generator(ctract_list, distance_list, zone_count_df):

    """
    Utility function to quickly compare the percentage of decrease in 
    available properties across census tracts and abutter distances.

    Input:
        ctract_list [list] - list of census tracts to generate exports for.
        distance_list [list] - list of abbutter distances
        zone_count_df [df] - DataFrame with tallies of zones 
                        (generated by available_zones_df_generator())
    
    Output:
        export_df [df] - exported DataFrame with percentage change columns.
    """
    # Add empty columns to `zone_count_df` to hold percent change 
    # in available census tract properties.

    zone_count_df['r_change'] = 0
    zone_count_df['mu_change'] = 0
    zone_count_df['i_change'] = 0

    zone_list = ['r', 'mu', 'i']

    r_total = 0
    mu_total = 0
    i_total = 0

    for ctract in ctract_list:
        for distance in distance_list:
            if distance == '0':
                r_total = zone_count_df.loc[ctract+"-"+distance]['r']
                mu_total = zone_count_df.loc[ctract+"-"+distance]['mu']
                i_total = zone_count_df.loc[ctract+"-"+distance]['i']
            if distance != '0':
                for zone in zone_list:
                    if zone == 'r':
                        if r_total != 0:
                            r_abutter = zone_count_df.loc[ctract+"-"+distance]['r']
                            r_percent_change = ((r_abutter - r_total) * 100)/r_total
                            zone_count_df.loc[(ctract+"-"+distance,'r_change')] = r_percent_change
                        else:
                            zone_count_df.loc[(ctract+"-"+distance,'r_change')] = 0
                    if zone == 'mu':
                        if mu_total != 0:
                            mu_abutter = zone_count_df.loc[ctract+"-"+distance]['mu']
                            mu_percent_change = ((mu_abutter - mu_total) * 100)/mu_total
                            zone_count_df.loc[(ctract+"-"+distance,'mu_change')] = mu_percent_change
                        else:
                            zone_count_df.loc[(ctract+"-"+distance,'mu_change')] = 0
                    if zone == 'i':
                        if i_total != 0:
                            i_abutter = zone_count_df.loc[ctract+"-"+distance]['i']
                            i_percent_change = ((i_abutter - i_total) * 100)/i_total
                            zone_count_df.loc[(ctract+"-"+distance,'i_change')] = i_percent_change
                        else:
                            zone_count_df.loc[(ctract+"-"+distance,'i_change')] = 0

    return zone_count_df



def double_hist(arr1, arr2, label1, label2):
    """
    Utility function to quickly draw double histogram visuals.

    Input:
        arr1 [df column] - data being compared
        arr2 [df column] - data being compared
        label1 [str] - arr1 data label
        label2 [str] - arr2 data label
    
    Output:
        Double histogram visual.
    
    """
    
    plt.hist(arr1, color='r', alpha=0.5, label=label1)
    plt.hist(arr2, color='b', alpha=0.5, label=label2)
    plt.legend()
    plt.show()
