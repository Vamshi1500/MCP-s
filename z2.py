from mcp.server.fastmcp import FastMCP
import json
import os

mcp = FastMCP("Auto_Location_Link_Tool")

@mcp.tool()
def show_my_location_on_map() -> str:
    """Show my location on a map.
    Example: show my location on map"""

    try:
        # Load from location.json
        if not os.path.exists("location.json"):
            return "Location not yet captured. Run the location script first."

        with open("location.json", "r") as f:
            coords = json.load(f)

        lat = coords["lat"]
        lon = coords["lon"]

        return f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=15/{lat}/{lon}"

    except Exception as e:
        return f"Error generating map link: {str(e)}"

if __name__ == "__main__":
    mcp.settings.port=8002
    mcp.settings.sse_path= "/location_map"
    mcp.run(transport="sse")