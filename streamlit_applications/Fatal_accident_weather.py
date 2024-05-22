# Run in command line (in main project directory): streamlit run streamlit_applications/Fatal_accident_weather.py
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="London Accidents and Weather Trends",
    page_icon=":umbrella:",
    layout="centered",
    initial_sidebar_state="collapsed",
)

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



