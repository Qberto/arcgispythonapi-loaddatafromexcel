
# coding: utf-8

# # Test: Daily Load of Records from Excel Sheet into Feature Layer, adding Geometry

# # Workflow Description
# 
# 1. Open excel file to a designated sheet
# 
# 2. Determine today's date, and retrieve records from today's date into a spatial dataframe
# 
# 3. For each record, retrieve the zip code, and get geometry from a reference shapefile or publicly available zip code layer
# 
# 4. Use the spatial dataframe of new records with geometry in an update (add) operation on a specified target layer

# Import needed modules

# In[ ]:

import arcgis
import pandas as pd
from datetime import datetime


# # User: Please enter parameters related to the input excel

# In[ ]:

excel_path = r""
sheet_name = "Master" 
excel_date_field_name = "Date"
excel_zip_field_name = "ZIP"
excel_issue_field_name = "Issue"
excel_count_field_name = "Count"


# # User: Please enter parameters related to target ArcGIS Online

# In[ ]:

target_layer_agol_org_url = ""
target_layer_agol_org_username = ""
target_layer_name = ""


# Set reference to geometry data source

# In[ ]:

reference_geometry_shapefile = r"ZipRef\zip_poly.shp"


# Authenticate with the GIS that the target layer resides in

# In[ ]:

gis = arcgis.gis.GIS(target_layer_agol_org_url, target_layer_agol_org_username)


# Instantiate connection to the target layer

# In[ ]:

target_item = gis.content.search(target_layer_name, "feature service")[0]


# # 1. Open excel file to a designated sheet

# In[ ]:

input_df = pd.read_excel(excel_path, sheetname=sheet_name)


# # 2. Determine today's date, and retrieve records from today's date into a spatial dataframe

# In[ ]:

today_string = datetime.today().strftime('%m/%d/%Y')


# In[ ]:

today_df = input_df.loc[input_df['Date'] == today_string]


# Cast the zips from the input to string

# In[ ]:

today_df[excel_zip_field_name] = today_df[excel_zip_field_name].astype(str)


# # 3. For each record, retrieve the zip code, and get geometry from a reference shapefile or publicly available zip code layer

# Bring our reference shapefile of zip codes with geometry into a spatial dataframe

# In[ ]:

sp_df = arcgis.features.SpatialDataFrame.from_featureclass(reference_geometry_shapefile)


# Retrieve today's zip codes into a list of strings to allow us to query the reference zip code spatial dataframe

# In[ ]:

today_zips_list = today_df[excel_zip_field_name].tolist()


# Create a new query of zips with geometry from today's zips

# In[ ]:

today_sp_df =  sp_df[sp_df.ZIP_CODE.isin(today_zips_list)]


# Format the columns and join the today_df

# In[ ]:

target_sp_df = pd.merge(left=today_df, right=today_sp_df, left_on=excel_zip_field_name, right_on="ZIP_CODE")


# Create order of needed columns

# In[ ]:

columns = ['SHAPE', excel_zip_field_name, excel_date_field_name, excel_issue_field_name, excel_count_field_name]


# In[ ]:

target_sp_df = target_sp_df[columns]


# Set an attribute field name map since Maps for Office gives strange column names to the service behind the scenes

# In[ ]:

attribute_map = {'f1':'ZIP', 'f2':'Date', 'f3':'Issue', 'f4': 'Count'}


# # 4. Use the spatial dataframe of new records with geometry in an update (add) operation on a specified target layer

# In[ ]:

for index, row in df.iterrows():
    print index, row['some column']


# In[ ]:

template_attribute_dict = {"f1": "99999", 
                           "f2": "01/01/1900", 
                           "f3": "None", 
                           "f4": "99"
                          }


# In[ ]:

# Build empty list that will contain the feature objects to send with the update request
features_to_add = []

# Iterate on each row of the input delta records from today
for index, row in target_sp_df.iterrows():
    # Retrieve geometry and attributes
    feat_geometry = row['SHAPE']
    feat_attributes = template_attribute_dict
    feat_attributes['f1'] = row[attribute_map['f1']]
    feat_attributes['f2'] = row[attribute_map['f2']]
    feat_attributes['f3'] = row[attribute_map['f3']]
    feat_attributes['f4'] = row[attribute_map['f4']]
    print("\nUpdating feature attributes:")
    print(feat_attributes)
    
    # Project geometry 
    projected_feat_geometry = {
    "rings" : feat_geometry['rings'],
    "spatialReference" : {"wkid" : 4326}
    }
    projected_feat_polygon = arcgis.geometry.Polygon(projected_feat_geometry)
    print("Geometry valid: "+str(projected_feat_polygon.is_valid))
    # Build feature object
    feature_to_add = arcgis.features.Feature(geometry=projected_feat_polygon, attributes=feat_attributes)
    # Append feature object to list of features to add
    features_to_add.append(feature_to_add)


# In[ ]:

target_lyr = target_item.layers[0]
target_fset = target_lyr.query()
original_record_count = target_fset.df.shape[0]
print("original record count: " + str(original_record_count))


# In[ ]:

target_lyr.edit_features(adds = features_to_add)


# In[ ]:

target_fset = target_lyr.query()
new_record_count = target_fset.df.shape[0]
print("New record count: " + str(new_record_count))
print(str(new_record_count - original_record_count) + " features successfully added.")
