import matplotlib.pyplot as plt
import random
from IPython.display import display, Markdown
import ipywidgets as widgets
import matplotlib.patches as mpatches
from ipywidgets import Layout


def __make_text(manager, routing, solution, data):
    total_distance = 0
    output = "\n\n\n"

    pickup_nodes = {p for p, _ in data['pickups_deliveries']}
    delivery_nodes = {d for _, d in data['pickups_deliveries']}
    if 'demands' in data and 'vehicle_capacities' in data:
        demands = data.get('demands', [0] * len(data['nodes']))
        capacity_dimension = routing.GetDimensionOrDie("Capacity")

    visited_nodes = set()
    visited_nodes.add(data['depot'])  # depot always visited

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = f"### Route for vehicle {vehicle_id}:\n\n"
        route_distance = 0

        # Print start node (without demand/cap)
        node = manager.IndexToNode(index)
        plan_output += f"{node} -- "

        previous_index = index
        index = solution.Value(routing.NextVar(index))

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            visited_nodes.add(node)

            label = f"**{node}"
            if node in pickup_nodes:
                label += "P**"
            elif node in delivery_nodes:
                label += "D**"
            plan_output += f"{label} "

            if 'demands' in data and 'vehicle_capacities' in data:
                demand = demands[node]

                plan_output += f"({demand})"
            
                load = solution.Value(capacity_dimension.CumulVar(index)) + demand
                plan_output += f"[cap={load}/{data['vehicle_capacities'][vehicle_id]}] "

            leg_distance = routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
            route_distance += leg_distance
            plan_output += f"-- {leg_distance}m --> "
            
            previous_index = index
            index = solution.Value(routing.NextVar(index))

        # Append final node (end/depot) with no demand/cap
        last_node = manager.IndexToNode(index)
        visited_nodes.add(last_node)
        leg_distance = routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
        route_distance += leg_distance

        plan_output += f"**{last_node}** \n\n"
        plan_output += f"**Distance of the route:** {route_distance}m\n\n"
        output += plan_output
        total_distance += route_distance

    # Compute unvisited nodes (excluding depot)
    all_nodes = set(range(len(data['nodes'])))
    all_nodes.discard(data['depot'])
    unvisited = all_nodes - visited_nodes

    if unvisited:
        output += "### Unvisited nodes:\n"
        output += ", ".join(str(n) for n in sorted(unvisited)) + "\n"
    else:
        output += "### All nodes visited\n"

    output += f"## Total distance of all routes: {total_distance}m\n"
    return output

# Calcola offset verticale in pixel e converti in unità dati
def __offset_in_data_units(grid_km, fraction):
    """Calcola offset verticale in unità dati proporzionale alla griglia."""
    return grid_km * fraction
    
# Plotting function (returns an Axes object)
def __make_plot(ax, manager, routing, solution, data, node_coords):
    # Base colors for vehicles with alpha for lighter lines
    vehicle_colors = ['blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'black']
    vehicle_alpha = 0.3

    pickup_color = 'orange'
    delivery_color = 'purple'
    depot_color = 'red'

    # Map nodes to their pickup-delivery pairs
    pickup_delivery_map = {}
    for pickup, delivery in data["pickups_deliveries"]:
        pickup_delivery_map[pickup] = (pickup, delivery)
        pickup_delivery_map[delivery] = (pickup, delivery)

    offset_pickup = __offset_in_data_units(data['grid_km'], 37)  
    offset_delivery = __offset_in_data_units(data['grid_km'], 10) 

    # Plot nodes with different shapes/colors
    for node, (x, y) in node_coords.items():
        if node == data["depot"]:
            ax.plot(x, y, 's', color=depot_color, markersize=10, label='Depot')
            ax.text(x + 1, y + 1, f"{node}", fontsize=9, fontweight='bold')
            continue

        if node in pickup_delivery_map:
            pickup_id, delivery_id = pickup_delivery_map[node]
            slack = 0;
            if node == pickup_id:
                # Pickup node: orange, triangle up, bold pickup id
                ax.plot(x, y+offset_pickup, '^', color=pickup_color, markersize=10)
                label = f"$\\bf{{{pickup_id}}}$-{delivery_id}"
            else:
                # Delivery node: purple, triangle down, bold delivery id
                ax.plot(x, y-offset_delivery, 'v', color=delivery_color, markersize=10)
                label = f"{pickup_id}-$\\bf{{{delivery_id}}}$"
            
            ax.text(
                x, y,  # shift label 2 units above node; adjust as needed
                label,
                fontsize=9,
                ha='center',    # center horizontally
                va='bottom',    # align bottom of text at y+2, so text goes upwards
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.2')
            )


        else:
            # Other nodes: black circle
            ax.plot(x, y, 'o', color='black', markersize=6)
            ax.text(x + 1, y + 1, str(node), fontsize=9)

    # Plot vehicle routes with lighter colors
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route.append(node_coords[node])
            index = solution.Value(routing.NextVar(index))
        route.append(node_coords[manager.IndexToNode(index)])
        xs, ys = zip(*route)
        ax.plot(xs, ys, color=vehicle_colors[vehicle_id % len(vehicle_colors)], 
                linewidth=2, alpha=vehicle_alpha, label=f'Vehicle {vehicle_id}')

    ax.set_title("Vehicle Routes")

    # Create custom legend handles for depot, pickups, deliveries, and routes
    depot_handle = plt.Line2D([], [], color=depot_color, marker='s', linestyle='None', markersize=10, label='Depot')
    pickup_handle = plt.Line2D([], [], color=pickup_color, marker='^', linestyle='None', markersize=10, label='Pickup points')
    delivery_handle = plt.Line2D([], [], color=delivery_color, marker='v', linestyle='None', markersize=10, label='Delivery points')
    vehicle_handles = [
        plt.Line2D([], [], color=vehicle_colors[i % len(vehicle_colors)], lw=2, alpha=vehicle_alpha, label=f'Vehicle {i}')
        for i in range(data["num_vehicles"])
    ]

    handles = [depot_handle, pickup_handle, delivery_handle] + vehicle_handles
    ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1, 0.5), title="Legend")
    ax.set_xlim(0, data['grid_km']*1000)
    ax.set_ylim(0, data['grid_km']*1000)
    ax.grid(True)


def plot_solution(manager, routing, solution, data):
    node_coords = {node["id"]: (node["x"], node["y"]) for node in data["nodes"]}
    
    # Display side-by-side using widgets
    # Layout settings
    text_layout = Layout(width='35%')
    plot_layout = Layout(width='65%')
    
    # Display side-by-side using widgets
    if solution:
        text_output = __make_text(manager, routing, solution, data)
        
        out_text = widgets.Output(layout=text_layout)
        out_plot = widgets.Output(layout=plot_layout)
    
        with out_text:
            display(Markdown(text_output))
    
        with out_plot:
            fig, ax = plt.subplots(figsize=(8, 8))
            __make_plot(ax, manager, routing, solution, data, node_coords)
            plt.show()
    
        display(widgets.HBox([out_text, out_plot]))
    else:
        print("No solution found.")