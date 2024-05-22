'''
This module contains functions and imports used in accident_analysis.ipynb
'''

from requests import Session
import pandas as pd
from io import BytesIO
import geopandas as gpd
from zipfile import ZipFile
import os
from shutil import rmtree
from tqdm.notebook import trange, tqdm
from shapely.geometry import Point
from scrapy import Selector
import xyzservices.providers as xyz
import folium
from branca.colormap import LinearColormap
from plotnine import *
from pickle import dump

MAPBOX_API_KEY = open('mapbox_api_key', 'r').read()
session = Session()

def normalise_saint(ward):
    """
    Normalises a ward starting with "St" so that it begins with "St."

    Args:
        ward (str): Ward in London.
    
    Returns:
        (str): Ward in London with saint normalised as "St."
    """
    if ward[:3] == 'St ':
        ward = 'St. ' + ward[3:]
    return ward

def list_to_path(directories):
    """
    Takes a list of folders and makes it into a relative path.

    Args:
        directories (list): 
            List of strings containing the names of directories (or dots for relative path
            structure) in the path. Each directory after the first in the list is a
            subdirectory of the preceding directory.
    
    Returns:
        (str): Relative path.
    """
    if directories == None:
        return ''
    string = ''
    for item in directories:
        string += item + '/'
    return string

def dict_to_filenames_list(filenames_dict):
    '''
    Turns a dictionary of partial filenames with multiple endings into a 
    list of full filenames.

    Args:
        filenames_dict (dict):
            keys (str): Partial filenames.
            values (list): One or more strings that are found at the
                           end of the key in the full filename.
    
    Returns (list): Full filenames as strings within the list.
    '''
    filenames_list = []
    for filename in filenames_dict.keys():
        for filetype in filenames_dict[filename]:
            filenames_list.append(filename + filetype)
    return filenames_list

def save_files_from_zip(url, filenames_in_zip, output_filenames = None, 
                        zip_folders = None, output_folders = None):
    """
    Downloads a specific file or specific files from a zip URL
    and saves it with (a) chosen name(s).

    Args:
        url (str): The URL of the zip file.
        filenames_in_zips (str, list, or dict): The name of the files within the zip archive.
        output_filenames (str, list, or dict, default = None): 
            The desired filenames for the downloaded files. 
            If None then the files keep their original names.
        zip_folders (list, default = None): 
            The folders that the file is found in within the zip in order.
        output_folders (list, default = None):
            The relative folders that the file will be saved at in order.

    Returns: None.
    """
    response = session.get(url, stream = True)
    response.raise_for_status()

    # Make filenames_in_zip into a list of filenames
    if type(filenames_in_zip) == str:
        filenames_in_zip = [filenames_in_zip]
    elif type(filenames_in_zip) == dict:
        filenames_in_zip = dict_to_filenames_list(filenames_in_zip)
    elif type(filenames_in_zip) != list:
        raise TypeError("filenames_in_zip expects str, list, or dict, "\
                        f"got {type(filenames_in_zip)}")
    
    # Make output_filenames into a list of filenames
    if output_filenames != None:
        if type(output_filenames) == str:
            output_filenames = [output_filenames]
        elif type(output_filenames) == dict:
            output_filenames = dict_to_filenames_list(output_filenames)
        elif type(output_filenames) != list:
            raise TypeError("output_filenames expects str, list, or dict, "\
                            f"got {type(output_filenames)}")
    else:
        output_filenames = filenames_in_zip
    
    # Convert lists of directories to directory paths
    zip_folder_path = list_to_path(zip_folders)
    output_folders = list_to_path(output_folders)

    if len(filenames_in_zip) != len(output_filenames):
        raise ValueError(f"{len(filenames_in_zip)} filenames in zip requested but "\
                         f"{len(output_filenames)} new filenames given.")
    
    # Download files to a relative path of choice
    for file in range(len(filenames_in_zip)):
        original_filepath = zip_folder_path + filenames_in_zip[file]
        new_filepath = output_folders + output_filenames[file]
        with ZipFile(BytesIO(response.content)) as zip_ref:
            zip_ref.extract(original_filepath, output_folders)
        if output_filenames != None:
            os.rename(output_folders + original_filepath, new_filepath)
            if os.path.exists(output_folders + zip_folders[0]):
                rmtree(output_folders + zip_folders[0])

def casualties_severities(casualties):
    """
    Takes a list of casualties of an accident as they are formatted in TfL's API
    and returns a dictionary containing the counts of how many casualties that occured
    during that accident broken down by severity.

    Args:
        casualties (list): Casualties of an accident as they are formatted in TfL's API.

    Returns:
        (dict):
            keys (str): TfL API's accident severities.
            values (int): Number of casualties of the corresponding severity 
                          in the given list of casualties.
    """
    severities = {'Slight': 0, 'Serious': 0, 'Fatal': 0}
    for casualty in casualties:
        severities[casualty['severity']] += 1
    return severities

def get_area_casualties(boundaries, casualties, workday_population):
    """
    Creates a GeoDataFrame containing London wards or boroughs and their respective counts of 
    casualties by severity and counts of casualties by severity per capita.

    Args:
        boundaries (GeoDataFrame): GeoDataFrame containing the boundaries and names of London
                                   wards or boroughs.
        casualties (GeoDataFrame): GeoDataFrame containing the number of casualties by severity
                                   and locations of accidents.
        workday_population (DataFrame): DataFrame containing the workday populations and names
                                        of London wards or boroughs.
    
    Returns:
        (GeoDataFrame): GeoDataFrame containing London wards or boroughs and their respective
                        counts of casualties by severity and counts of casualties by severity
                        per capita (by workday population).
    """
    gdf_area_casualties = boundaries.copy()
    if 'combined_name' in workday_population: # True if area type is ward
        gdf_area_casualties['combined_name'] = gdf_area_casualties['ward'] + ', ' +\
            gdf_area_casualties['borough']
        on = 'combined_name'
    else:
        on = 'borough'
    
    # Perform spatial join
    joined_data = gpd.sjoin(casualties, gdf_area_casualties,
                            how = "inner", predicate = "within")

    # Group by ward and aggregate casualties
    grouped_data = joined_data.groupby(on)\
        [["slight", "serious", "fatal", 'total', 'weighted_total']].agg("sum")

    # Merge aggregated data back to the original ward polygons
    gdf_area_casualties = gdf_area_casualties.merge(grouped_data, on = on)
    
    if on == 'combined_name': # True if area type is ward
        gdf_area_casualties = pd.merge(gdf_area_casualties, workday_population)\
            .sort_values(['borough', 'ward']).reset_index(drop = True)\
                .drop(columns = 'combined_name')
    else:
        gdf_area_casualties = pd.merge(gdf_area_casualties, workday_population)\
            .sort_values('borough').reset_index(drop = True)  

    gdf_area_casualties['slight_per_capita'] = gdf_area_casualties\
        .apply(lambda x: x['slight'] / x['workday_population'], axis = 1)
    gdf_area_casualties['serious_per_capita'] = gdf_area_casualties\
        .apply(lambda x: x['serious'] / x['workday_population'], axis = 1)
    gdf_area_casualties['fatal_per_capita'] = gdf_area_casualties\
        .apply(lambda x: x['fatal'] / x['workday_population'], axis = 1)
    gdf_area_casualties['total_per_capita'] = gdf_area_casualties\
        .apply(lambda x: x['total'] / x['workday_population'], axis = 1)
    gdf_area_casualties['weighted_total_per_capita'] = gdf_area_casualties\
        .apply(lambda x: x['weighted_total'] / x['workday_population'], axis = 1)
    
    return gdf_area_casualties

def get_tooltip(borough, column, gdf_area_casualties, borough_logos, ward = None, output_string = False):
    """
    Gets the desired tooltip for a given borough or ward in London.

    Args:
        borough (str): London borough (of ward if ward does not equal None) or City of London.
        column (str): Severity per capita column in gdf_area_casualties.
        gdf_area_casualties (GeoDataFrame): gdf_borough_casualties or gdf_ward_casualties.
        borough_logos (dict):
            keys (str): London boroughs and City of London.
            values (str): Image source of corresponding the borough or City of London's logo.
        ward (str, Default = None): Ward in London or City of London.
        output_string (bool, Default = False): True if the output should be a string instead
                                               of a tooltip.

    Returns:
        (folium.Tooltip): Tooltip containing string with HTML code to control what is displayed
                          when the ward or borough is hovered over in a folium map.
    """
    string = """<div style = "text-align: center; width: 130px;">"""
    if ward != None:
        value = gdf_area_casualties[(gdf_area_casualties['ward'] == ward) & 
                                    (gdf_area_casualties['borough'] == borough)][column].iloc[0]
        string += f"""<p style = "font-family: gill sans; font-size: 12px; """\
            f"""font-weight: bold; white-space: wrap;">{ward.upper()}</p>"""
    else:
        value = gdf_area_casualties[gdf_area_casualties['borough'] == borough][column].iloc[0]
        
        # City of London's logo does not contain its name, so it is added when it is not used as a ward name
        if borough == "City of London":
            string += """<p style = "font-family: gill sans; font-size: 12px; """\
                """font-weight: bold; white-space: wrap;">City of London</p>"""
    
    string += f"""<img style = "max-width: 130px; max-height: 90px" src = {borough_logos[borough]} """\
        f"""alt="{borough} logo"><br><br><p style = "font-family: palatino; font-size: 10px; """\
        f"""white-space: wrap;"><b>{round(value * 1000, 2)}</b> {column.split('_')[0]} casualties """\
        f"""per 10,000 people (workday population) per year in <b>{borough}</b></p></div>"""
    
    # Since the value of weighted_total is an arbitrary weighting, its tooltip omits the useless value.
    # The map's colour mapping suffices to compare areas.
    if column == 'weighted_total_per_capita':
        if output_string == True:
            return string.split('<br><br>')[0] + '</div>'
        return folium.Tooltip(string.split('<br><br>')[0] + '</div>')
    
    if output_string == True:
            return string
    return folium.Tooltip(string)

def make_map(severity, gdf_area_casualties, borough_logos, tile_provider):
    """
    Makes a folium map based on the requested severity within gdf_area_casualties.

    Args:
        severity (str): Severity of accidents the map focuses on.
        gdf_area_casualties (GeoDataFrame): gdf_borough_casualties or gdf_ward_casualties.
        borough_logos (dict):
            keys (str): London boroughs and City of London.
            values (str): Image source of corresponding the borough or City of London's logo.
        tile_provider (xyzservices.lib.TileProvider): Tile provider for map base.

    Returns:
        (folium.Map): Map based on the requested severity within gdf_area_casualties.
    """
    colour_map = LinearColormap(['#B4ffbe', '#900000'],
                                vmin = gdf_area_casualties[f'{severity}_per_capita'].min(),
                                vmax = gdf_area_casualties[f'{severity}_per_capita'].max())
    
    if 'ward' in gdf_area_casualties and 'borough' in gdf_area_casualties:
        area_type = 'wards'
    elif 'borough' in gdf_area_casualties:
        area_type = 'boroughs'
    else:
        raise ValueError(f"gdf_area_casualties must in include 'borough' column")

    polygons = []

    for area in range(len(gdf_area_casualties)):
        if area_type == 'wards':
            tooltip = get_tooltip(gdf_area_casualties['borough'].iloc[area],
                                  f'{severity}_per_capita',
                                  gdf_area_casualties,
                                  borough_logos,
                                  ward = gdf_area_casualties['ward'].iloc[area])
        else:
            tooltip = get_tooltip(gdf_area_casualties['borough'].iloc[area],
                                  f'{severity}_per_capita',
                                  gdf_area_casualties,
                                  borough_logos)
        polygons.append(folium.GeoJson(
            data = gdf_area_casualties['geometry'].iloc[area].__geo_interface__,
            fill_color = colour_map(gdf_area_casualties[f'{severity}_per_capita'].iloc[area]),  
            fill_opacity = 0.5,
            weight = 0,
            tooltip = tooltip,
            highlight_function = lambda x: {'fillColor': '#000000',
                                            'fillOpacity': 0.75,
                                            'weight': 0.1}))

    map = folium.Map(
        # Location is LSE Centre Building, but map doesn't centre on it because of its bounds.
        # If zoom_start were to be made a higher value then location would be higher.
        location = [51.51392455461779, -0.11641135450232364],
        zoom_start = 10,
        max_bounds = True,
        tiles = tile_provider.build_url(api_key = MAPBOX_API_KEY),
        attr = tile_provider['attribution'],
        name = tile_provider['name'],
        max_zoom = tile_provider['max_zoom'],
        min_zoom = tile_provider['min_zoom'],
        detect_retina = True,
        max_lat = 51.7,
        min_lon = -.53,
        min_lat = 51.28,
        max_lon = .35,
        )
    
    for polygon in polygons:
        map.add_child(polygon)
    
    return map

def get_severity(accident):
    """
    Assigns severity based on casualty counts, handling missing values.

    Args:
        accident (Series): Row in gdf_severities.

    Returns:
        (str): Most severe classification of the accident's casualties.
    """
    if accident.get('fatal', 0) > 0:
        return 'Fatal'
    elif accident.get('serious', 0) > 0:
        return 'Serious'
    elif accident.get('slight', 0) > 0:
        return 'Slight'
    else:
        raise ValueError(f"Accident must have at least one casualty but accident: {accident} has none.")
    
def get_size(severity):
    """
    Scales the point size of an accident's severity.

    Args:
        severity (str): Severity of an accident.

    Returns:
        (int): Relative scale for point sizing.
    """
    if severity == "Fatal":
        return 15
    elif severity == "Serious":
        return 8
    elif severity == "Slight":
        return 1
    else:
        raise ValueError(f"Argument: severity equals {severity}, it must equal 'Fatal', 'Serious', or 'Slight'")

def spaces_to_breaks(string):
    '''
    Replaces the spaces in a string into line breaks.

    Args:
        ward (str): Any string.
    
    Returns:
        (str): Original string with '\n' in place of spaces.
    '''
    if type(string) == str:
        new_string = ''
        for character in string:
            if character != ' ':
                new_string += character
            else:
                new_string += '\n'
        return new_string