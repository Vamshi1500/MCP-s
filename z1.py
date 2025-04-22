# import base64
# from io import BytesIO
# from mcp.server.fastmcp import FastMCP
# from typing import Annotated
# from geopy.geocoders import Nominatim
# from staticmap import StaticMap, CircleMarker

# mcp = FastMCP("Map MCP Server")

# @mcp.tool()
# def show_country_on_map_as_image(
#     country: Annotated[str, "Enter a country name"]
# ) -> Annotated[str, "Base64-encoded PNG of the map"]:
#     """Generate a map image of the specified country.
#     Example: show me India"""
#     try:
#         geolocator = Nominatim(user_agent="langchain-map")
#         location = geolocator.geocode(country)

#         if not location:
#             return "Country not found"

#         # Create static map with a marker at the country's coordinates
#         m = StaticMap(600, 400)
#         marker = CircleMarker((location.longitude, location.latitude), 'blue', 12)
#         m.add_marker(marker)

#         # Render the image and convert it to a base64 string
#         image = m.render()
#         image_bytes = BytesIO()
#         image.save(image_bytes, format="PNG")
#         image_bytes.seek(0)
        
#         # Encode image as base64
#         encoded_image = base64.b64encode(image_bytes.getvalue()).decode('utf-8')

#         # Create a data URL for the image (useful for displaying in a web context)
#         return f"data:image/png;base64,{encoded_image}"

#     except Exception as e:
#         return f"Error generating map: {e}"

# if __name__ == "__main__":
#     mcp.run()

# from mcp.server.fastmcp import FastMCP
# from typing import Annotated
# from geopy.geocoders import Nominatim
# from staticmap import StaticMap, CircleMarker
# from io import BytesIO
# from io import BytesIO
# from PIL import Image

# mcp = FastMCP("Map MCP Server")

# @mcp.tool()
# def show_country_on_map_as_image(
#     country: Annotated[str, "Enter a country name"]
# ) -> Annotated[bytes, "Map of the country"]:
#     """Generate a map image of the specified country.
#     Example: show me India"""
#     try:
#         geolocator = Nominatim(user_agent="langchain-map")
#         location = geolocator.geocode(country)

#         if not location:
#             return "Country not found"

#         m = StaticMap(600, 400)
#         marker = CircleMarker((location.longitude, location.latitude), 'blue', 12)
#         m.add_marker(marker)

#         image = m.render()
#         image_bytes = BytesIO(image)
#         image = Image.open(image_bytes)
#         image.save(f"{country}_map.png")
#         image.show()
#         return f"Map image for {country} saved as '{country}_map.png'."


#     except Exception as e:
#         return f"Error generating map: {e}"

# if __name__ == "__main__":
#     mcp.run()

from mcp.server.fastmcp import FastMCP
from typing import Annotated
from geopy.geocoders import Nominatim
from urllib.parse import quote

mcp = FastMCP("Map_MCP_Server")

@mcp.tool()
def show_country_on_map_as_image_url(country: str) -> str:
    """Generate a map URL for the specified country.
    Example: show me India"""
    try:
        geolocator = Nominatim(user_agent="langchain-map")
        location = geolocator.geocode(country)

        if not location:
            return "Country not found"

        # Construct the static map URL for the country using OpenStreetMap or other services
        lat, lon = location.latitude, location.longitude
        map_url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=6/{lat}/{lon}"

        return f"Map URL for {country}: {map_url}"

    except Exception as e:
        return f"Error generating map URL: {e}"

if __name__ == "__main__":
    mcp.settings.port=8001
    mcp.settings.sse_path= "/country_map"
    mcp.run(transport="sse")