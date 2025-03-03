import requests
import googlemaps

# 🔹 Your Google Maps API Key
API_KEY = "YOUR_GOOGLE_MAPS_API_KEY"
gmaps = googlemaps.Client(key=API_KEY)

# 🔹 Function to get geographical coordinates of a location
def get_location_coordinates(location):
    url = f"https://geocode.maps.co/search?q={location}&format=json"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    data = response.json()
    if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
    return None

# 🔹 Function to get road data between two locations using Overpass API
def get_osm_roads_between(start_coords, end_coords):
    overpass_url = "https://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      way["highway"~"^(motorway|trunk|primary|secondary|tertiary|residential|service|unclassified)$"]
      ({start_coords[0]}, {start_coords[1]}, {end_coords[0]}, {end_coords[1]});
    );
    out body;
    >;
    out skel qt;
    """
    response = requests.get(overpass_url, params={"data": overpass_query})
    return response.json()

# 🔹 Function to get polygon boundary of a specified area using Google Places API
def get_polygon_for_area(area_name):
    try:
        place_results = gmaps.places(area_name)
        if not place_results['results']:
            print("No area found for:", area_name)
            return None
        place_id = place_results['results'][0]['place_id']
        details = gmaps.place(place_id)
        if "geometry" in details["result"] and "viewport" in details["result"]["geometry"]:
            viewport = details["result"]["geometry"]["viewport"]
            polygon = [
                (viewport["northeast"]["lat"], viewport["northeast"]["lng"]),
                (viewport["southwest"]["lat"], viewport["northeast"]["lng"]),
                (viewport["southwest"]["lat"], viewport["southwest"]["lng"]),
                (viewport["northeast"]["lat"], viewport["southwest"]["lng"]),
            ]
            return polygon
    except Exception as e:
        print(f"Error fetching polygon for {area_name}: {e}")
        return None

# 🔹 Function to generate the best route while avoiding specific roads and areas
def get_routes_googlemaps(start, end, avoid_areas=[], avoid_roads=[]):
    try:
        directions = gmaps.directions(start, end, mode="driving")
        if not directions:
            print("No available path right now.")
            return None

        best_route = None
        min_time = float("inf")

        # Iterate over all possible routes
        for route in directions:
            steps = route["legs"][0]["steps"]
            path = []
            total_time = 0
            avoid = False

            for step in steps:
                lat, lng = step["start_location"]["lat"], step["start_location"]["lng"]
                path.append((lat, lng))
                total_time += step["duration"]["value"]  # Duration in seconds

                # **Check if the step includes an avoided road**
                if avoid_roads and step.get("html_instructions") and any(road in step["html_instructions"] for road in avoid_roads):
                    avoid = True
                    break

                # **Check if the step enters an avoided area**
                for polygon in avoid_areas:
                    if is_inside_polygon(lat, lng, polygon):
                        avoid = True
                        break

            # Choose the best route with the shortest time that does not enter restricted areas
            if not avoid and total_time < min_time:
                min_time = total_time
                best_route = path

        if best_route:
            return best_route, min_time
        else:
            print("All routes contain restricted roads/areas.")
            return None
    except Exception as e:
        print(f"API request failed: {e}")
        return None

# 🔹 Function to check if a point is inside a polygon
def is_inside_polygon(lat, lng, polygon):
    """
    - lat, lng: location coordinates
    - polygon: list of polygon coordinates [(lat1, lng1), (lat2, lng2), ...]
    - Uses the "Ray Casting Algorithm" to determine if a point is inside a polygon
    """
    num = len(polygon)
    j = num - 1
    inside = False
    for i in range(num):
        lat1, lng1 = polygon[i]
        lat2, lng2 = polygon[j]
        if ((lng1 > lng) != (lng2 > lng)) and (
            lat < (lat2 - lat1) * (lng - lng1) / (lng2 - lng1) + lat1
        ):
            inside = not inside
        j = i
    return inside

# 🔹 Test case
start_location = "Times Square, New York, NY"
end_location = "Statue of Liberty, New York, NY"

# 🔹 Prompt user to enter an area to avoid
avoid_area_name = input("Enter the area to avoid (e.g., Central Park, NY): ")
avoid_area_polygon = get_polygon_for_area(avoid_area_name)
avoid_areas = [avoid_area_polygon] if avoid_area_polygon is not None else []

# 🔹 Define specific roads to avoid
avoid_roads = ["FDR Drive"]

# 🔹 Generate the best route
route_info = get_routes_googlemaps(start_location, end_location, avoid_areas, avoid_roads)
if route_info:
    best_route, min_time = route_info
    print("Best Route Found:")
    for lat, lng in best_route:
        print(f"({lat}, {lng})")
    print(f"Estimated Time: {min_time / 60:.2f} min")
