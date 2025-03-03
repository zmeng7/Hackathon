import requests
import heapq
import math

# Function to get latitude and longitude for a given location using Geocode API
def get_location_coordinates(location):
    API_KEY = "API_Key"  
    url = f"https://geocode.maps.co/search?q={location}&format=json"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data and isinstance(data, list) and len(data) > 0:
            return float(data[0]["lat"]), float(data[0]["lon"])
        else:
            print(f"⚠️ Error: No coordinates found for '{location}'")
            return None
    except requests.exceptions.RequestException as e:
        print(f"API Error fetching coordinates for '{location}': {e}")
        return None


# Function to retrieve road network data using Overpass API
def get_osm_roads_between(start_coords, end_coords):
    if start_coords is None or end_coords is None:
        print("Invalid start or end coordinates. Cannot query Overpass API.")
        return None

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
    
    try:
        response = requests.get(overpass_url, params={"data": overpass_query}, timeout=10)
        response.raise_for_status()
        osm_data = response.json()

        if "elements" not in osm_data or len(osm_data["elements"]) == 0:
            print("⚠️ Warning: No roads found between the locations.")
            return None
        return osm_data
    except requests.exceptions.RequestException as e:
        print(f"Overpass API Error: {e}")
        return None

# Function to construct a graph from OSM road data
def build_graph_from_osm(osm_data):
    graph = {}  # Adjacency list {node_id: [(neighbor_id, distance), ...]}
    nodes = {}  # Node ID to (latitude, longitude) mapping

    if osm_data is None:
        print("Error: No OSM data available. Exiting.")
        return {}, {}

    for element in osm_data["elements"]:
        if element["type"] == "node":
            nodes[element["id"]] = (element["lat"], element["lon"])

    for element in osm_data["elements"]:
        if element["type"] == "way":
            node_list = element["nodes"]
            for i in range(len(node_list) - 1):
                node_a, node_b = node_list[i], node_list[i + 1]
                if node_a in nodes and node_b in nodes:
                    dist = haversine_distance(nodes[node_a], nodes[node_b])
                    if node_a not in graph:
                        graph[node_a] = []
                    if node_b not in graph:
                        graph[node_b] = []
                    graph[node_a].append((node_b, dist))
                    graph[node_b].append((node_a, dist))

    return graph, nodes

# Function to calculate Haversine distance between two coordinates
def haversine_distance(coord1, coord2):
    R = 6371  # Earth radius in km
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # Distance in km

# A star algorithm for finding the shortest path
def a_star_search(graph, nodes, start_id, end_id):
    open_set = []
    heapq.heappush(open_set, (0, 0, start_id, []))  # (f(n), g(n), current_node, path)
    visited = set()

    while open_set:
        f, g, current, path = heapq.heappop(open_set)

        if current in visited:
            continue
        visited.add(current)

        path = path + [nodes[current]]  # Store path as list of coordinates

        if current == end_id:
            return path, g  # Return shortest path and total distance

        if current not in graph or not graph[current]:
            continue  # Skip if the node has no connections

        for neighbor, cost in graph[current]:
            if neighbor not in visited:
                h = haversine_distance(nodes[neighbor], nodes[end_id])  # Heuristic estimate
                heapq.heappush(open_set, (g + cost + h, g + cost, neighbor, path))

    return None, float("inf")  # No path found

# Find the nearest OSM node to a given coordinate
def find_nearest_node(coord, nodes):
    return min(nodes, key=lambda n: haversine_distance(nodes[n], coord))


#  test case
start_location = "Times Square, New York, NY"
end_location = "Statue of Liberty, New York, NY"

# Get coordinates for start and end locations
start_coords = get_location_coordinates(start_location)
end_coords = get_location_coordinates(end_location)

if start_coords is None or end_coords is None:
    print(" Error: Could not retrieve coordinates. Exiting program.")
    exit()

#  Retrieve OSM road data
osm_data = get_osm_roads_between(start_coords, end_coords)
if osm_data is None:
    print(" Error: No road data available. Exiting program.")
    exit()

#  Build graph
graph, nodes = build_graph_from_osm(osm_data)
if not graph or not nodes:
    print(" Error: No valid road network found. Exiting program.")
    exit()

#  Find the nearest OSM nodes for start and end locations
start_node = find_nearest_node(start_coords, nodes)
end_node = find_nearest_node(end_coords, nodes)

#  Run A star search algorithm to find the shortest path
shortest_path, total_distance = a_star_search(graph, nodes, start_node, end_node)

#  Print results
if shortest_path:
    print("\n Shortest Path Found:")
    for lat, lon in shortest_path:
        print(f"({lat}, {lon})")
    print(f"\n Estimated Distance: {total_distance:.2f} km")
else:
    print(" No valid path found.")
