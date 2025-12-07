from fastmcp import FastMCP
import httpx

mcp = FastMCP("weather")

@mcp.tool()
async def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    async with httpx.AsyncClient() as client:
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {"name": city, "count": 1, "language": "en", "format": "json"}
        geo_resp = await client.get(geo_url, params=geo_params)
        geo_data = geo_resp.json()

        if not geo_data.get("results"):
            if "," in city:
                simple_city = city.split(",")[0].strip()
                geo_params["name"] = simple_city
                geo_resp = await client.get(geo_url, params=geo_params)
                geo_data = geo_resp.json()
            
            if not geo_data.get("results"):
                return f"Could not find coordinates for {city}"

        location = geo_data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        name = location["name"]
        country = location.get("country", "")

        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code",
        }
        weather_resp = await client.get(weather_url, params=weather_params)
        weather_data = weather_resp.json()
        
        current = weather_data.get("current", {})
        temp = current.get("temperature_2m")
        code = current.get("weather_code")
        
        conditions = "Unknown"
        if code == 0: conditions = "Clear sky"
        elif code in [1, 2, 3]: conditions = "Partly cloudy"
        elif code in [45, 48]: conditions = "Fog"
        elif code in [51, 53, 55]: conditions = "Drizzle"
        elif code in [61, 63, 65]: conditions = "Rain"
        elif code in [71, 73, 75]: conditions = "Snow"
        elif code in [95, 96, 99]: conditions = "Thunderstorm"

        return f"Weather in {name}, {country}: {temp}°C, {conditions}"
