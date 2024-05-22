# Run in command line (in main project directory): streamlit run streamlit_applications/accident_locations.py
import streamlit as st
from plotnine import *
import geopandas as gpd

st.set_page_config(
    page_title = "London Accident Locations",
    page_icon = ":kangaroo:",
    layout = "wide",
    initial_sidebar_state = "collapsed",
    )

gdf_ward_boundaries = gpd.read_file('boundaries/wards_2004_to_14.shp')\
    .set_crs(epsg = 27700).to_crs(epsg = 4326)\
        .drop(columns = ['GSS_CODE', "HECTARES", "NONLD_AREA", "LB_GSS_CD", "POLY_ID"])\
            .rename(columns = {'NAME': 'ward', 'BOROUGH': 'borough'})

if "ward_disabled" not in st.session_state:
    st.session_state.ward_disabled = True

if "borough_disabled" not in st.session_state:
    st.session_state.borough_disabled = True

london = st.checkbox("Display all of London")

if london == True:
    st.session_state.borough = None
    st.session_state.ward = None
    st.session_state.borough_disabled = True
    borough = st.selectbox(
        'Borough',
        [],  # Empty list when london is checked
        index = None,
        placeholder = "Select a borough",
        disabled = st.session_state.borough_disabled,
    )
    ward = st.selectbox(
        'Ward',
        [],  # Empty list when london is checked
        index = None,
        placeholder = "Select a ward",
        disabled = st.session_state.ward_disabled,
    )
    plot = st.image("london_accidents.png")
else:
    st.session_state.borough_disabled = False
    borough = st.selectbox(
        'Borough',
        list(gdf_ward_boundaries['borough'].drop_duplicates().sort_values()),
        index = None,
        placeholder = "Select a borough",
        disabled = st.session_state.borough_disabled,
        )
    
    if borough != None and borough != "City of London":
        st.session_state.ward_disabled = False
    else:
        st.session_state.ward_disabled = True

    ward = st.selectbox(
        'Ward',
        list(gdf_ward_boundaries[gdf_ward_boundaries['borough'] == borough]['ward']),
        index = None,
        placeholder = "Select a ward",
        disabled = st.session_state.ward_disabled,
        )

    if ward != None:
        ward_boundary = gdf_ward_boundaries[(gdf_ward_boundaries['borough'] == borough) & 
                                            (gdf_ward_boundaries['ward'] == ward)]
        
        gdf_plot = gpd.read_file(f"data/gdf_points/{borough}/{ward}.shp")
        
        if 'Fatal' in list(gdf_plot['Severity'].drop_duplicates()): # 122 wards have no fatal accidents
            fill_values = ['red', 'orange', 'green']
            max_point_size = 2.5
        else:
            fill_values = ['orange', 'green']
            max_point_size = 1.66

        ward_plot = (
            ggplot()
            + geom_map(ward_boundary, fill = '#E6e6e6', alpha = 0.5, size = 0) 
            + geom_point(gdf_plot, aes(x = "geometry.x", y = "geometry.y", fill = 'Severity', size = "size"), stroke = 0)
            + scale_size_radius(range = (0.7, max_point_size))
            + scale_fill_manual(values = fill_values)
            + guides(size = False)
            + theme_minimal()
            + theme(
                panel_grid_major = element_blank(), 
                panel_grid_minor = element_blank(),
                axis_title = element_blank(),
                axis_text = element_blank(),
                ) 
        )
        plot = st.pyplot(ggplot.draw(ward_plot))

    elif borough != None:
        borough_boundaries = gdf_ward_boundaries[gdf_ward_boundaries['borough'] == borough]
        
        gdf_plot = gpd.read_file(f"data/gdf_points/boroughs/{borough}.shp")

        borough_plot = (
                ggplot()
                + geom_map(borough_boundaries, fill = '#E6e6e6', alpha = 0.5, size = 0.1) 
                + geom_point(gdf_plot, aes(x = "geometry.x", y = "geometry.y", fill = 'Severity', size = "size"), stroke = 0)
                + scale_size_radius(range = (0.7, 3))
                + scale_fill_manual(values = ['red', 'orange', 'green'])
                + guides(size = False)
                + theme_minimal()
                + theme(
                    panel_grid_major = element_blank(), 
                    panel_grid_minor = element_blank(),
                    axis_title = element_blank(),
                    axis_text = element_blank(),
                    ) 
            )
        plot = st.pyplot(ggplot.draw(borough_plot))
    else:
        plot = st.image("london_accidents.png")