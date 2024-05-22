#run : streamlit run streamlit_applications/regressions.py
import pandas as pd
import streamlit as st
import statsmodels.api as sm

# Load your merged data
data = pd.read_csv('merged_fatal_accidents_weather.csv')

# List of weather parameters
weather_parameters = ['temperature_2m', 'relative_humidity_2m', 'precipitation', 'rain', 'snowfall', 'cloud_cover', 'wind_speed_10m']

# Streamlit app
st.title('Relationship between Weather Parameters and Accidents')

# Iterate over each weather parameter
for parameter in weather_parameters:
    st.header(f'Analysis for {parameter}')
    
    # Scatter plot of weather parameter vs. number of accidents
    st.write(f'Scatter plot of {parameter} vs. Number of Accidents')
    st.write(st.pyplot(sm.graphics.abline_plot(model_results=model, 
                                                xlabel=parameter, 
                                                ylabel='Number of Accidents', 
                                                color='blue')))
    
    # Fit the regression model
    X = sm.add_constant(data[parameter])
    y = data['fatal_accidents']
    model = sm.OLS(y, X).fit()
    
    # Get the summary of the regression model
    st.write(model.summary())
    
    # Check if the coefficient of the weather parameter is statistically significant
    if model.pvalues[parameter] < 0.05:
        st.write(f'The coefficient of {parameter} is statistically significant, indicating a relationship with the number of accidents.')
    else:
        st.write(f'The coefficient of {parameter} is not statistically significant, indicating no significant relationship with the number of accidents.')
