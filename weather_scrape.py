import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from datetime import datetime, timezone

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

def fetch_weather_data(latitude, longitude, timestamp):
    url = "https://archive-api.open-meteo.com/v1/archive"
    # Ensure the timestamp is truncated to the hour and timezone-aware in UTC
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    timestamp = timestamp.astimezone(timezone.utc)
    timestamp_hour = timestamp.replace(minute=0, second=0, microsecond=0)
    
    date_str = timestamp_hour.strftime('%Y-%m-%d')
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": date_str,
        "end_date": date_str,
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "rain", "snowfall", "cloud_cover", "wind_speed_10m"]
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    hourly = response.Hourly()
    times = pd.date_range(start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                          end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                          freq=pd.Timedelta(seconds=hourly.Interval()), inclusive="left")
    
    weather_data = {
        "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
        "relative_humidity_2m": hourly.Variables(1).ValuesAsNumpy(),
        "precipitation": hourly.Variables(2).ValuesAsNumpy(),
        "rain": hourly.Variables(3).ValuesAsNumpy(),
        "snowfall": hourly.Variables(4).ValuesAsNumpy(),
        "cloud_cover": hourly.Variables(5).ValuesAsNumpy(),
        "wind_speed_10m": hourly.Variables(6).ValuesAsNumpy(),
    }
    
    weather_df = pd.DataFrame(data=weather_data, index=times)
    return weather_df.loc[timestamp_hour]

# Test the function with an example
example_latitude = 51.488749
example_longitude = -0.165406
example_timestamp = datetime(2010, 1, 1, 10, 30, tzinfo=timezone.utc)  # Example timestamp
print(fetch_weather_data(example_latitude, example_longitude, example_timestamp))
