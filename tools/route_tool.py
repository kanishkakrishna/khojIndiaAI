import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

@tool
def get_route_info(origin: str, destination: str) -> str:
    """
    Finds the distance, travel time, and basic directions between two locations.
    Use this tool when the user asks how to reach a place, the distance between two spots, or travel duration.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY missing."

    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "key": api_key,
        "mode": "driving" # You can change this to 'transit' for bus/train later
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data["status"] == "OK":
            route = data["routes"][0]["legs"][0]
            distance = route["distance"]["text"]
            duration = route["duration"]["text"]
            
            return f"The distance from {origin} to {destination} is {distance} and it will take approximately {duration} by car."
        else:
            return f"Could not find route. Google Maps Status: {data['status']}"
            
    except Exception as e:
        return f"Error fetching route: {str(e)}"