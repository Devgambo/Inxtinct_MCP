from fastapi import FastAPI, HTTPException
import httpx
import uvicorn
from pydantic import BaseModel

app = FastAPI(title="Weather Server")

class WeatherResponse(BaseModel):
    city: str
    country: str
    temperature: float
    conditions: str
    description: str

@app.get("/weather", response_model=WeatherResponse)
async def get_weather(city: str):
    """Get the current weather for a city."""
    # 1. Geocoding
    async with httpx.AsyncClient() as client:
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {"name": city, "count": 1, "language": "en", "format": "json"}
        try:
            geo_resp = await client.get(geo_url, params=geo_params)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=503, detail=f"Geocoding service unavailable: {e}")

        if not geo_data.get("results"):
            # Try splitting by comma (e.g. "New York, USA" -> "New York")
            if "," in city:
                simple_city = city.split(",")[0].strip()
                geo_params["name"] = simple_city
                try:
                    geo_resp = await client.get(geo_url, params=geo_params)
                    geo_data = geo_resp.json()
                except httpx.HTTPError:
                    pass
            
            if not geo_data.get("results"):
                raise HTTPException(status_code=404, detail=f"Could not find coordinates for {city}")

        location = geo_data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        name = location["name"]
        country = location.get("country", "")

        # 2. Weather
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code",
        }
        try:
            weather_resp = await client.get(weather_url, params=weather_params)
            weather_resp.raise_for_status()
            weather_data = weather_resp.json()
        except httpx.HTTPError as e:
             raise HTTPException(status_code=503, detail=f"Weather service unavailable: {e}")
        
        current = weather_data.get("current", {})
        temp = current.get("temperature_2m")
        code = current.get("weather_code")
        
        # Weather codes: https://open-meteo.com/en/docs
        conditions = "Unknown"
        if code == 0: conditions = "Clear sky"
        elif code in [1, 2, 3]: conditions = "Partly cloudy"
        elif code in [45, 48]: conditions = "Fog"
        elif code in [51, 53, 55]: conditions = "Drizzle"
        elif code in [61, 63, 65]: conditions = "Rain"
        elif code in [71, 73, 75]: conditions = "Snow"
        elif code in [95, 96, 99]: conditions = "Thunderstorm"

        description = f"Weather in {name}, {country}: {temp}°C, {conditions}"
        
        return WeatherResponse(
            city=name,
            country=country,
            temperature=temp,
            conditions=conditions, 
            description=description
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
