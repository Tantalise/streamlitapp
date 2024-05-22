# run: streamlit run streamlitwebsitecombined.py
import streamlit as st
import plotnine
from plotnine import *
import geopandas as gpd
from pickle import load
import plotly.express as px
import pandas as pd 

# Define HTML content
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>My Streamlit App</title>
  <style>
    <body {
      font-family: Arial, sans-serif;
    }
    .header {
      background-color: #4CAF50;
      padding: 20px;
      text-align: center;
      color: white;
    }
    .content {
      padding: 20px;
    }
    .footer {
      background-color: #f1f1f1;
      text-align: center;
      padding: 10px;
      position: fixed;
      left: 0;
      bottom: 0;
      width: 100%;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>Khenny's Kangaroos DS105 Project</h1>
  </div>
  <div class="content">
    <!-- Streamlit content will be injected here -->
  </div>
  <div class="footer">
    <p>&copy; 2024 My Streamlit App</p>
  </div>
</body>
</html>
"""
# Inject HTML content
st.markdown(html_content, unsafe_allow_html=True)



# Add your Streamlit application logic here
st.title('Accident Location Analysis')
st.write('This is where your Streamlit app content goes.')

# Example content
st.write("""
    <div class="content">
      <p>This is a paragraph in the content section.</p>
    </div>
""", unsafe_allow_html=True)


# Title
st.markdown("<h1 class='title'>Welcome to My Streamlit Website</h1>", unsafe_allow_html=True)

# Content
st.markdown("<div class='content'>", unsafe_allow_html=True)
st.write("""
### Introduction
This is a sample Streamlit application that demonstrates how to create a website using Streamlit.
You can add more content here, including text, images, and even interactive components like charts and tables.
""")


st.write("""
### About
Here is some information about the website. You can add more details as needed.
""")

st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("<div class='footer'>© 2024 Your Name</div>", unsafe_allow_html=True)

st.write("""
### Accident Locations streamlit
""")


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
        
    
    

st.write("""
### Work day populations and Accidents streamlit
""")

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



st.write("""
### Matching weather data with Fatal accidents streamlit
""")

# Read the merged CSV file
merged_df = pd.read_csv('merged_fatal_accidents_weather.csv')

# Rename the columns
merged_df = merged_df.rename(columns={
    "temperature_2m": "Temperature (°C)",
    "relative_humidity_2m": "Humidity (%)",
    "precipitation": "Precipitation (mm)",
    "rain": "Rain (mm)",
    "snowfall": "Snowfall (cm)",
    "cloud_cover": "Cloud Cover (%)",
    "wind_speed_10m": "Wind Speed (km/h)"
})

# List of available weather parameters
available_parameters = ['Temperature (°C)', 'Humidity (%)', 'Precipitation (mm)', 'Rain (mm)', 'Snowfall (cm)', 'Cloud Cover (%)', 'Wind Speed (km/h)']

# Streamlit app
st.title('Fatal Accidents by Borough and Weather Parameter')

# Dropdown menu for selecting the weather parameter
selected_parameter = st.selectbox('Select Weather Parameter', available_parameters)

# Aggregate the data by borough and the selected weather parameter
aggregated_data = merged_df.groupby(['borough', selected_parameter]).size().reset_index(name='count')

# Calculate the total number of fatal accidents per borough
total_fatal_accidents = aggregated_data.groupby('borough')['count'].sum().reset_index(name='total_count')

# Sort boroughs by total number of fatal accidents in ascending order
sorted_boroughs = total_fatal_accidents.sort_values(by='total_count', ascending=True)['borough']

# Convert the borough column to a categorical type with the order based on the sorted total counts
aggregated_data['borough'] = pd.Categorical(aggregated_data['borough'], categories=sorted_boroughs, ordered=True)

# Create a plot using Plotly
fig = px.bar(
    aggregated_data, 
    x='count', 
    y='borough', 
    color=selected_parameter, 
    orientation='h',
    title=f'Fatal Accidents by Borough and {selected_parameter.capitalize()}'
)

# Update layout to make the figure larger and adjust margins
fig.update_layout(
    xaxis_title='Number of Fatal Accidents',
    yaxis_title='Borough',
    height=800,  # Adjust height as needed
    margin=dict(l=200, r=20, t=50, b=50)  # Adjust left margin to ensure borough names fit
)

# Display the plot
st.plotly_chart(fig)

# Add additional information about weather parameters
st.markdown("""
### Weather Parameter Descriptions
- **Temperature (°C):** Air temperature at 2 meters above ground
- **Humidity (%):** Relative humidity at 2 meters above ground
- **Precipitation (mm):** Total precipitation (rain, showers, snow) sum of the preceding hour. Data is stored with a 0.1 mm precision. If precipitation data is summed up to monthly sums, there might be small inconsistencies with the total precipitation amount.
- **Rain (mm):** Only liquid precipitation of the preceding hour including local showers and rain from large scale systems.
- **Snowfall (cm):** Snowfall amount of the preceding hour in centimeters. For the water equivalent in millimeter, divide by 7. E.g. 7 cm snow = 10 mm precipitation water equivalent.
- **Cloud Cover (%):** Total cloud cover as an area fraction.
- **Wind Speed (km/h):** Wind speed at 10 meters above ground.
""")




