# import requests

# def get_location():
#     url = "https://www.googleapis.com/geolocation/v1/geolocate?key=YOUR_API_KEY"
#     response = requests.post(url)
#     data = response.json()
    
#     lat = data['location']['lat']
#     lon = data['location']['lng']
#     print(f"Latitude: {lat}, Longitude: {lon}")

# get_location()
import socket

# Get the private IP address (local IP address)
from geopy.geocoders import Nominatim

# Using geopy for reverse geocoding
# geolocator = Nominatim(user_agent="myGeocoder")

# latitude = 40.748817  # Example latitude
# longitude = -73.985428  # Example longitude (Empire State Building)

# location = geolocator.reverse((latitude, longitude), language='en', exactly_one=True)
# print("Address:", location.address)

# import requests
# from geopy.geocoders import Nominatim

# # Step 1: Get current location based on IP
# def get_current_location():
#     # Use ipinfo.io to get location based on IP address (city level)
#     response = requests.get('https://ipinfo.io/json')
#     data = response.json()
    
#     # Get latitude and longitude from the response
#     loc = data.get('loc').split(',')
#     latitude = float(loc[0])
#     longitude = float(loc[1])
    
#     return latitude, longitude

# # Step 2: Use Nominatim (OpenStreetMap) to reverse geocode and get address
# def get_address_from_coordinates(latitude, longitude):
#     geolocator = Nominatim(user_agent="myGeocoder")
    
#     # Reverse geocoding to get the full address
#     location = geolocator.reverse((latitude, longitude), language='en', exactly_one=True)
    
#     if location:
#         return location.address
#     else:
#         return "Address not found"

# # Main function to get current location and address
# def main():
#     latitude, longitude = get_current_location()  # Get location based on IP
#     print(f"Latitude: {latitude}, Longitude: {longitude}")
    
#     # Get the address from latitude and longitude
#     address = get_address_from_coordinates(latitude, longitude)
    
#     print("Street-level Address:", address)

# # Run the script
# if __name__ == "__main__":
#     main()

from gps3 import gps3

gps_socket = gps3.GPSDSocket()
data_stream = gps3.DataStream()

gps_socket.connect()
gps_socket.watch()

for new_data in gps_socket:
    if new_data:
        data_stream.unpack(new_data)
        latitude = data_stream.lat
        longitude = data_stream.lon
        print(f"Latitude: {latitude}, Longitude: {longitude}")