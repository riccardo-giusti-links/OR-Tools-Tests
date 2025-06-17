import random
import math

def __generate_pickup_delivery_instance(seed, grid_km, num_requests):
    grid_m = grid_km * 1000  # convert to meters

    if seed is not None:
        random.seed(seed)
    
    data = {}
    
    # Depot at the center
    depot = (grid_m / 2, grid_m / 2)
    locations = [depot]

    # Generate pickup and delivery points
    pickups_deliveries = []
    for _ in range(num_requests):
        pickup = (random.uniform(0, grid_m), random.uniform(0, grid_m))
        delivery = (random.uniform(0, grid_m), random.uniform(0, grid_m))
        locations.append(pickup)
        locations.append(delivery)
        pickups_deliveries.append([len(locations) - 2, len(locations) - 1])

    # Compute Euclidean distance matrix
    def euclidean(p1, p2):
        return int(round(math.hypot(p1[0] - p2[0], p1[1] - p2[1])))

    distance_matrix = [
        [euclidean(loc1, loc2) for loc2 in locations]
        for loc1 in locations
    ]

    data['nodes'] = [{'id': idx, 'x': round(coord[0], 2), 'y': round(coord[1], 2)} for idx, coord in enumerate(locations)]
    data['distance_matrix'] = distance_matrix
    data['depot'] = 0
    data['pickups_deliveries'] = pickups_deliveries

    return data

# data keys (generate_basic_instance input)
# grid_km = side of the area 
# num_requests = number of requests
# seed = random seed for generating instances

# data keys (generate_basic_instance output)
# nodes = list of nodes, each element has id and x,y coordinates
# distance_matrix = all distances between each couple of nodes
# depot = id 0 and position in the center of the area 
# pickups_deliveries = list of requests, each element has node ids for pickup and delivery 
def generate_basic_instance(seed, grid_km, num_requests):
    data = __generate_pickup_delivery_instance(seed, grid_km, num_requests)
    data['grid_km'] = grid_km
    data['num_requests'] = num_requests
    data['seed'] = seed
    return data

# simply add demand 1 to each request
def add_demands(data):
    num_nodes = len(data['nodes'])
    demands = [1] * num_nodes  # Initialize all demands to 1
    demands[0] = 0
    demands[-1] = 0

    for _, delivery in data['pickups_deliveries']:
        demands[delivery] = -1   # Delivery node: negative demand

    data['demands'] = demands

    return data