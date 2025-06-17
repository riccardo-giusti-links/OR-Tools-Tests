from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
import time

def solve(data):
    # ---------------------------
    # Create routing model
    # ---------------------------
    manager = pywrapcp.RoutingIndexManager(
        len(data['distance_matrix']), data['num_vehicles'], data['depot']
    )
    routing = pywrapcp.RoutingModel(manager)
    
    # ---------------------------
    # Define distance callback
    # ---------------------------
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # ---------------------------
    # Add Distance dimension
    # ---------------------------
    routing.AddDimension(
        transit_callback_index,
        0,      # no waiting time at nodes
        data['max_travel_distance_vehicle'],   # max distance per vehicle
        True,   # start cumul to zero
        "Distance"
    )
    distance_dimension = routing.GetDimensionOrDie("Distance")
    
    # ---------------------------
    # Add Pickup and Delivery constraints
    # ---------------------------
    for pickup, delivery in data['pickups_deliveries']:
        pickup_index = manager.NodeToIndex(pickup)
        delivery_index = manager.NodeToIndex(delivery)
        routing.AddPickupAndDelivery(pickup_index, delivery_index)
        routing.solver().Add(
            routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index)
        )
        routing.solver().Add(
            distance_dimension.CumulVar(pickup_index) <= distance_dimension.CumulVar(delivery_index)
        )
    
    # ---------------------------
    # Demand parameters
    # ---------------------------
    # skip if demand or capacity is not defined in data
    if 'demands' in data and 'vehicle_capacities' in data:
        # 1. Define demand callback
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        
        # 2. Add capacity dimension
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            data['vehicle_capacities'],  # list of vehicle capacities
            True,  # start cumul to zero
            'Capacity'
        )
        
        capacity_dimension = routing.GetDimensionOrDie('Capacity')
        print("Added demand and capacity constraints")
    else:
        print("Skipping capacity constraints: data has no 'demands' or 'vehicle_capacities'")

    # ---------------------------
    # Penalty for skipping demand
    # ---------------------------
    # Add disjunctions to allow dropping nodes (except depot) with node-specific penalties if available
    if 'penalties' in data:
        for node in range(len(data['nodes'])):
            if node == data['depot']:
                continue  # never drop depot
            index = manager.NodeToIndex(node)
            node_penalty = data['penalties'][node]
            routing.AddDisjunction([index], node_penalty)
        print("Added penalties for unsatisfied demand")
    else:
        print("Skipping unsatisfied demand penalties: data has no 'penalties' field")
        print("It's mandatory to satisfy all demand")

    print("Instance loaded")

    # ---------------------------
    # Search parameters
    # ---------------------------
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    #search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.seconds = 30
    search_parameters.log_search = True  # Enable solver logs
    
    # ---------------------------
    # Solve and print solution
    # ---------------------------
    
    # Measure solving time manually
    start_time = time.time()
    solution = routing.SolveWithParameters(search_parameters)
    end_time = time.time()
    
    print(f"Solving time: {end_time - start_time:.2f} seconds")
    
    if solution:
        print("Model solved.")
    else:
        print("No solution found.")
    return manager, routing, solution