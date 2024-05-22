# Run in command line (in main project directory): streamlit run streamlit_applications/workday_population.py
import streamlit as st
from plotnine import *
import geopandas as gpd
from pickle import load

st.set_page_config(
    page_title = "London Accidents Per Capita",
    page_icon = ":kangaroo:",
    layout = "centered",
    initial_sidebar_state = "collapsed",
    )

gdf_plot = gpd.read_file("data/workday_population/gdf_plot_ward_casualties.shp")

area = st.selectbox(
        'Select area of focus',
        ['Greater London'] + list(gdf_plot['borough'].drop_duplicates()),
        )

if area == 'Greater London':
    gdf_plot = gpd.read_file("data/workday_population/gdf_plot_borough_casualties.shp")
    label = None # Too many boroughs to plot titles without it being extremely cluttered
    logo = None
else:
    gdf_plot = gdf_plot[gdf_plot['borough'] == area]
    centroids = gdf_plot.geometry.centroid
    label = geom_label(
        aes(x = centroids.x, y = centroids.y, label = 'ward'),
        family = "gill sans",
        label_size = 0.2,
        label_padding = 0.1,
        alpha = 0.75,
        boxcolor = 'white',
        size = 7,
        )
    with open('data/borough_logos.pkl', 'rb') as f:
        borough_logos = load(f)
    logo = borough_logos[area]

severity = st.radio('', ('Weighted total', 'Total', 'Slight', 'Serious', 'Fatal'), horizontal = True)
if severity != 'Weighted total':
    severity_column = severity.lower()
else:
    severity_column = 'weighted'

# Centring the radio
st.markdown("""
        <style>
        .stRadio [role=radiogroup]{
            align-items: center;
            justify-content: center;
        }
        </style>
    """,unsafe_allow_html=True)

ward_plot = (
    ggplot(gdf_plot)
    + geom_map(aes(fill = severity_column), alpha = 0.5, size = 0.1) 
    + scale_fill_gradient(low = "#B4ffbe", high = '#900000')
    + theme_minimal()
    + theme(
        panel_grid_major = element_blank(), 
        panel_grid_minor = element_blank(),
        axis_title = element_blank(),
        axis_text = element_blank(),
        legend_title = element_blank(),
        title = element_text(family = "gill sans"),
        legend_text = element_text(family = 'gill sans'),
        ) 
    + label
    + labs(title = f"{severity} casualties by ward per 10,000 people (workday population) per year in {area}")
)
plot = st.pyplot(ggplot.draw(ward_plot))

if area != 'Greater London': # We don't think the Greater London Assembly's logo is worth displaying here as if it were a council logo
    col1, col2, col3 = st.columns(3) # Centring image

    with col1:
        st.write(' ')

    with col2:
        st.markdown(f"<img style='max-height: 175px; max-width: 350px;' src='{logo}'>", unsafe_allow_html = True)

    with col3:
        st.write(' ')