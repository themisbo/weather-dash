import streamlit as st
import requests
import pandas as pd
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page Configuration
st.set_page_config(page_title="Bristol Weather Dashboard", layout="wide")

# Constants
LATITUDE = 51.4545
LONGITUDE = -2.5879
API_URL = "https://api.open-meteo.com/v1/forecast"

# Weather Code Mapping (WMO)
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Drizzle: Light", 53: "Drizzle: Moderate", 55: "Drizzle: Dense intensity",
    61: "Rain: Slight", 63: "Rain: Moderate", 65: "Rain: Heavy intensity",
    71: "Snow fall: Slight", 73: "Snow fall: Moderate", 75: "Snow fall: Heavy intensity",
    77: "Snow grains",
    80: "Rain showers: Slight", 81: "Rain showers: Moderate", 82: "Rain showers: Violent",
    85: "Snow showers: Slight", 86: "Snow showers: Heavy",
    95: "Thunderstorm: Slight or moderate",
    96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
}

@st.cache_data(ttl=900)
def get_weather_data():
    """Fetches weather data from Open-Meteo API."""
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": ["temperature_2m", "wind_speed_10m", "weather_code"],
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation_probability"],
        "timezone": "Europe/London"
    }
    
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None

def main():
    st.title("Bristol Weather Dashboard")
    
    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    data = get_weather_data()
    
    if data:
        # Current Conditions
        current = data.get("current", {})
        current_temp = current.get("temperature_2m", "N/A")
        current_wind = current.get("wind_speed_10m", "N/A")
        weather_code = current.get("weather_code", 0)
        weather_desc = WEATHER_CODES.get(weather_code, "Unknown")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Temperature", f"{current_temp} °C")
        col2.metric("Wind Speed", f"{current_wind} km/h")
        col3.metric("Condition", weather_desc)
        
        # Hourly Forecast Data Processing
        hourly = data.get("hourly", {})
        if hourly:
            df = pd.DataFrame(hourly)
            df['time'] = pd.to_datetime(df['time'])
            
            # Filter for next 24 hours
            now = datetime.datetime.now()
            next_24h = df[(df['time'] >= now) & (df['time'] < now + datetime.timedelta(hours=24))]
            
            # Create figure with secondary y-axis
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            # Add Temperature Trace
            fig.add_trace(
                go.Scatter(
                    x=next_24h['time'],
                    y=next_24h['temperature_2m'],
                    name="Temperature",
                    mode="lines+text",
                    text=["🌡️"] * len(next_24h),
                    textposition="top center",
                    line=dict(color="#FF4B4B", width=2),
                    textfont=dict(size=14)
                ),
                secondary_y=False,
            )

            # Add Precipitation Trace
            fig.add_trace(
                go.Scatter(
                    x=next_24h['time'],
                    y=next_24h['precipitation_probability'],
                    name="Precipitation",
                    mode="text",
                    text=["🌧️"] * len(next_24h),
                    textposition="top center",
                    textfont=dict(size=18)
                ),
                secondary_y=True,
            )

            # Update Layout
            fig.update_layout(
                title_text="24h Weather Forecast",
                height=500,
                template="plotly_dark",
                showlegend=False,
                xaxis=dict(showgrid=False),
                yaxis=dict(title="Temperature (°C)", showgrid=False),
                yaxis2=dict(title="Precipitation (%)", showgrid=False, range=[0, 110])
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("View Raw Data"):
                st.dataframe(df)

if __name__ == "__main__":
    main()
