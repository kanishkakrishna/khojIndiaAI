# tools/weather_tool.py
import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

# Load environment variables from .env file
load_dotenv()

@tool
def get_weather(location: str) -> str:
    """
    Fetches the current weather and temperature for a given city, village, or location.
    Always use this tool when the user asks about the weather, climate, or temperature of a place.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    
    if not api_key:
        return "System Error: OPENWEATHER_API_KEY is missing in the .env file."
    
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": api_key,
        "units": "metric" # Ensures temperature is in Celsius
    }
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if response.status_code == 200:
            temp = data["main"]["temp"]
            condition = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            
            # Returning a clean, descriptive string that the LLM can easily understand
            return f"Current weather in {location}: {temp}°C with {condition}. Humidity is {humidity}%."
        else:
            return f"Could not fetch weather for {location}. API Error: {data.get('message', 'Unknown')}"
            
    except Exception as e:
        return f"A network error occurred while fetching the weather: {str(e)}"