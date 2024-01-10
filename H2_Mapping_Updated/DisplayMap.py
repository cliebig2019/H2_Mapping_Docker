import io
import sys, os
from pathlib import Path
import geopandas as gpd
import shapefile as shp
import plotly
import plotly.graph_objects as go
import openrouteservice
from openrouteservice import convert
import folium
import timeit
from H2_Mapping_Updated.print_results import *
sys.path.append("/shapefile_to_network/main/convertor")
sys.path.append("/shapefile_to_network/main/shortest_paths")
from H2_Mapping_Updated.shapefile_to_network.main.convertor.GraphConvertor import GraphConvertor
from H2_Mapping_Updated.shapefile_to_network.main.shortest_paths.ShortestPath import ShortestPath
from shapely import speedups

speedups.disable()

    # this ComboBox has to be
    #self.world_heatmap_result_metric_combo.addItems(['Total Cost per kg H2', 'Gen. cost per kg H2',
    #                                                    'Transport Cost per kg H2', 'Cheapest Medium'])
    
# For normal
def normal(path):

    df = pd.read_csv(path)
    pd.DataFrame.info(df)

    return display_map(df), plot_world_results_single_run(df, "Total Cost per kg H2"), plot_world_results_single_run(df, "Gen. cost per kg H2"), plot_world_results_single_run(df, "Transport Cost per kg H2"), plot_world_results_single_run(df, "Cheapest Medium")
    

def display_map(df):
    """This Method can display the resulting transport route for the cheapest production location.
    Every combination of transport methods can be displayed. Trucking between two points is
    computed via openrouteservice. A pipeline is visualised by a straight line, since they're
    hypothetical in this model. Transport by ship can happen along a shipping network derived
    from real shipping paths obtained from tracking vessels."""

    # finds the place of the cheapest cost and stores its location as a tuple
    # stores the desired location as a tuple (location is the same for all rows of the df)
    min_cost = min(df['Total Cost per kg H2'])
    mindex = df.index.values[df['Total Cost per kg H2'] == min_cost]
    mindex = mindex[0]
    cheapest_source = (df['Latitude'][mindex], df['Longitude'][mindex])
    end_tuple = (df['End Plant Latitude'][mindex], df['End Plant Longitude'][mindex])
    transport_mode = df['Transport Mode'][mindex]

    # Create GraphConvertor object by passing the path of input shapefile and the output directory
    input_file = os.environ.get("BASE_PATH") + 'Data/shipping/shipping_routes/shipping_routes.shp'
    output_dir = os.environ.get("BASE_PATH") + 'Data/shipping/nodes'

    graph_convertor_obj = GraphConvertor(input_file, output_dir)

    # Call graph_convertor function to convert the input shapefile into road network and
    # save the newly created shapefile into specifed output_dir along with list of nodes and edges in .csv files
    network = graph_convertor_obj.graph_convertor()

    edges = gpd.read_file(input_file)
    nodes = gpd.read_file(os.environ.get("BASE_PATH") + 'Data/shipping/nodes/New Shape/nodes.shp')

    sf = shp.Reader(os.environ.get("BASE_PATH") + 'Data/shipping/shipping_routes/shipping_routes.shp')

    df_port_index = pd.read_csv(os.environ.get("BASE_PATH") + 'Data/port_index.csv', index_col=0)
    df_ports = pd.read_csv(os.environ.get("BASE_PATH") + 'Data/path/ports.csv')

    port_coords = create_port_coordinates(df_ports)

    start_plant_tuple = cheapest_source
    end_plant_tuple = end_tuple

    start_plant_tuple = start_plant_tuple[::-1]
    end_plant_tuple = end_plant_tuple[::-1]

    coords = (start_plant_tuple, end_plant_tuple)

    if "Ship" not in transport_mode:
        # no transport by ship -> either by truck or by pipeline

        if "Truck" in transport_mode:
            client = openrouteservice.Client(key='5b3ce3597851110001cf62487a8aff99152f40b9abb404dbb3a74056')

            res = client.directions(coords, radiuses=[5000, 5000])
            geometry = client.directions(coords, radiuses=[5000, 5000])['routes'][0]['geometry']
            decoded = convert.decode_polyline(geometry)

            distance_txt = "<h4> <b>Distance :&nbsp" + "<strong>" + str(
                round(res['routes'][0]['summary']['distance'] / 1000, 1)) + " Km </strong>" + "</h4></b>"
            duration_txt = "<h4> <b>Duration :&nbsp" + "<strong>" + str(
                round(res['routes'][0]['summary']['duration'] / 60, 1)) + " Mins. </strong>" + "</h4></b>"

            m = folium.Map(location=start_plant_tuple[::-1], zoom_start=2, control_scale=True,
                            tiles="cartodbpositron", zoom_control=False)
            folium.GeoJson(data=decoded).add_to(m)

            folium.Marker(
                location=list(coords[0][::-1]),
                popup="Start point",
                icon=folium.Icon(icon='map-marker', color="red"),
            ).add_to(m)

            folium.Marker(
                location=list(coords[1][::-1]),
                popup="End point",
                icon=folium.Icon(icon='map-marker', color="black"),
            ).add_to(m)
        else:
            m = folium.Map(location=start_plant_tuple[::-1], zoom_start=2, control_scale=True,
                            tiles="cartodbpositron", zoom_control=False)
            folium.Marker(
                location=list(coords[0][::-1]),
                popup="Start pipe",
                icon=folium.Icon(icon='map-marker', color="lightgreen"),
            ).add_to(m)

            folium.Marker(
                location=list(coords[1][::-1]),
                popup="End pipe",
                icon=folium.Icon(icon='map-marker', color="cadetblue"),
            ).add_to(m)

            pipe_full = [[start_plant_tuple[1], start_plant_tuple[0]],
                            [end_plant_tuple[1], end_plant_tuple[0]]]
            my_PolyLine = folium.PolyLine(locations=pipe_full, weight=3, color='purple')
            m.add_child(my_PolyLine)

    elif "Truck Ship" in transport_mode:
        # Find the closest port to the start point
        distance, index = spatial.KDTree(port_coords).query(start_plant_tuple)  # Needs [long, lat]
        start_port_code = df_ports.at[index, 'Unnamed: 0']
        print('Start Port Code: ' + str(start_port_code))
        start_port_tuple = port_coords[index][::-1]  # Outputs [long, lat]
        print('Start Port Tuple: ' + str(start_port_tuple))

        # Find the closest port to the end point
        distance, index = spatial.KDTree(port_coords).query(end_plant_tuple)  # Needs [long, lat]
        end_port_code = df_ports.at[index, 'Unnamed: 0']
        print('End Port Code: ' + str(end_port_code))
        end_port_tuple = port_coords[index][::-1]  # Outputs [long, lat]
        print('End Port Tuple: ' + str(end_port_tuple))

        # display route from production location to start port
        start_plant_to_port = (start_plant_tuple, start_port_tuple[::-1])
        client = openrouteservice.Client(key='5b3ce3597851110001cf62487a8aff99152f40b9abb404dbb3a74056')

        res = client.directions(start_plant_to_port, radiuses=[5000, 5000])
        geometry = client.directions(start_plant_to_port, radiuses=[5000, 5000])['routes'][0]['geometry']
        decoded = convert.decode_polyline(geometry)

        distance_txt = "<h4> <b>Distance :&nbsp" + "<strong>" + str(
            round(res['routes'][0]['summary']['distance'] / 1000, 1)) + " Km </strong>" + "</h4></b>"
        duration_txt = "<h4> <b>Duration :&nbsp" + "<strong>" + str(
            round(res['routes'][0]['summary']['duration'] / 60, 1)) + " Mins. </strong>" + "</h4></b>"

        m = folium.Map(location=start_plant_tuple[::-1], zoom_start=2, control_scale=True,
                        tiles="cartodbpositron", zoom_control=False)
        folium.GeoJson(data=decoded).add_to(m)

        folium.Marker(
            location=list(start_plant_to_port[0][::-1]),
            popup="Start point",
            icon=folium.Icon(icon='map-marker', color="red"),
        ).add_to(m)

        folium.Marker(
            location=list(start_plant_to_port[1][::-1]),
            popup="End point",
            icon=folium.Icon(icon='map-marker', color="black"),
        ).add_to(m)

        # Create ShortestPath object by passing all required parameters listed below
        g = network
        alpha = 0.1
        graph_buffer = 300
        point_buffer = 1
        break_point = 1  # Upper limit to save computation time

        # start timer
        start = timeit.default_timer()

        shortest_path_obj = ShortestPath(g, alpha, graph_buffer, point_buffer, break_point)

        # Run alpha_times_shortestpath function to calculate number of paths which are alpha times the shortest path
        start_tuple_port = start_port_tuple
        end_tuple_port = end_port_tuple

        shortest_paths, buffered_graph = shortest_path_obj.find_shortest_paths(start_tuple_port, end_tuple_port)

        shortest_dis = min(shortest_paths.keys())
        print('shortest distance: ' + str(shortest_dis))
        shortest_path = shortest_paths[shortest_dis]
        new_start_coord = shortest_path[0]
        print('new start coord: ' + str(new_start_coord))
        new_end_coord = shortest_path[len(shortest_path) - 1]
        print('new end coord: ' + str(new_end_coord))

        # stop timer
        stop = timeit.default_timer()

        print('Computation Time for shortest path: ', stop - start)

        # create dataframe to plot shortest path
        df = pd.DataFrame(shortest_path)
        lat = df[0]
        lon = df[1]

        # store all relevant coordinates for the shipping route inside coords_ship
        coords_ship = [start_tuple_port]
        for i in range(len(lon)):
            coords_ship.append([lat[i], lon[i]])
        coords_ship.append(end_tuple_port)

        # plot shipping route as a line on the map
        ship_route = [coords_ship]
        ship_PolyLine = folium.PolyLine(locations=ship_route, weight=3, color='seagreen')
        m.add_child(ship_PolyLine)

        if 'Pipe' in transport_mode:
            folium.Marker(
                location=end_tuple_port[::-1],
                popup="Start pipe",
                icon=folium.Icon(icon='map-marker', color="lightgreen"),
            ).add_to(m)

            folium.Marker(
                location=end_plant_tuple[::-1],
                popup="End pipe",
                icon=folium.Icon(icon='map-marker', color="cadetblue"),
            ).add_to(m)

            pipe_full = [end_tuple_port, end_plant_tuple]
            pipe_PolyLine = folium.PolyLine(locations=pipe_full, weight=3, color='purple')
            m.add_child(pipe_PolyLine)
        else:
            client = openrouteservice.Client(key='5b3ce3597851110001cf62487a8aff99152f40b9abb404dbb3a74056')
            end_port_to_end_plant = [end_tuple_port[::-1], end_plant_tuple]

            res = client.directions(end_port_to_end_plant, radiuses=[5000, 5000])
            geometry2 = client.directions(end_port_to_end_plant, radiuses=[5000, 5000])['routes'][0]['geometry']
            decoded2 = convert.decode_polyline(geometry2)

            distance_txt = "<h4> <b>Distance :&nbsp" + "<strong>" + str(
                round(res['routes'][0]['summary']['distance'] / 1000, 1)) + " Km </strong>" + "</h4></b>"
            duration_txt = "<h4> <b>Duration :&nbsp" + "<strong>" + str(
                round(res['routes'][0]['summary']['duration'] / 60, 1)) + " Mins. </strong>" + "</h4></b>"

            folium.GeoJson(data=decoded2).add_to(m)

            folium.Marker(
                location=list(end_port_to_end_plant[0][::-1]),
                popup="Start point",
                icon=folium.Icon(icon='map-marker', color="red"),
            ).add_to(m)

            folium.Marker(
                location=list(end_port_to_end_plant[1][::-1]),
                popup="End point",
                icon=folium.Icon(icon='map-marker', color="black"),
            ).add_to(m)

    elif 'Pipe Ship' in transport_mode:
        # Find the closest port to the start point
        distance, index = spatial.KDTree(port_coords).query(start_plant_tuple)  # Needs [long, lat]
        start_port_code = df_ports.at[index, 'Unnamed: 0']
        print('Start Port Code: ' + str(start_port_code))
        start_port_tuple = port_coords[index][::-1]  # Outputs [long, lat]
        print('Start Port Tuple: ' + str(start_port_tuple))

        # Find the closest port to the end point
        distance, index = spatial.KDTree(port_coords).query(end_plant_tuple)  # Needs [long, lat]
        end_port_code = df_ports.at[index, 'Unnamed: 0']
        print('End Port Code: ' + str(end_port_code))
        end_port_tuple = port_coords[index][::-1]  # Outputs [long, lat]
        print('End Port Tuple: ' + str(end_port_tuple))

        # display route from production location to start port
        start_plant_to_port = (start_plant_tuple, start_port_tuple[::-1])

        m = folium.Map(location=start_plant_tuple[::-1], zoom_start=2, control_scale=True,
                        tiles="cartodbpositron", zoom_control=False)

        folium.Marker(
            location=list(start_plant_to_port[0][::-1]),
            popup="Start point",
            icon=folium.Icon(icon='map-marker', color="red"),
        ).add_to(m)

        folium.Marker(
            location=list(start_plant_to_port[1][::-1]),
            popup="End point",
            icon=folium.Icon(icon='map-marker', color="black"),
        ).add_to(m)

        pipe_to_port = [start_plant_tuple[::-1], start_port_tuple]
        pipe_PolyLine = folium.PolyLine(locations=pipe_to_port, weight=3, color='purple')
        m.add_child(pipe_PolyLine)

        # Create ShortestPath object by passing all required parameters listed below
        g = network
        alpha = 0.1
        graph_buffer = 300
        point_buffer = 1
        break_point = 1  # Upper limit to save computation time

        # start timer
        start = timeit.default_timer()

        shortest_path_obj = ShortestPath(g, alpha, graph_buffer, point_buffer, break_point)

        # Run alpha_times_shortestpath function to calculate number of paths which are alpha times the shortest path
        start_tuple_port = start_port_tuple
        end_tuple_port = end_port_tuple

        shortest_paths, buffered_graph = shortest_path_obj.find_shortest_paths(start_tuple_port, end_tuple_port)

        shortest_dis = min(shortest_paths.keys())
        print('shortest distance: ' + str(shortest_dis))
        shortest_path = shortest_paths[shortest_dis]
        new_start_coord = shortest_path[0]
        print('new start coord: ' + str(new_start_coord))
        new_end_coord = shortest_path[len(shortest_path) - 1]
        print('new end coord: ' + str(new_end_coord))

        # stop timer
        stop = timeit.default_timer()

        print('Computation Time for shortest path: ', stop - start)

        # create dataframe to plot shortest path
        df = pd.DataFrame(shortest_path)
        lat = df[0]
        lon = df[1]

        # store all relevant coordinates for the shipping route inside coords_ship
        coords_ship = [start_tuple_port]
        for i in range(len(lon)):
            coords_ship.append([lat[i], lon[i]])
        coords_ship.append(end_tuple_port)

        # plot shipping route as a line on the map
        ship_route = [coords_ship]
        ship_PolyLine = folium.PolyLine(locations=ship_route, weight=3, color='seagreen')
        m.add_child(ship_PolyLine)

        if 'Truck' in transport_mode:
            client = openrouteservice.Client(key='5b3ce3597851110001cf62487a8aff99152f40b9abb404dbb3a74056')
            end_port_to_end_plant = [end_tuple_port[::-1], end_plant_tuple]

            res = client.directions(end_port_to_end_plant, radiuses=[5000, 5000])
            geometry2 = client.directions(end_port_to_end_plant, radiuses=[5000, 5000])['routes'][0]['geometry']
            decoded2 = convert.decode_polyline(geometry2)

            distance_txt = "<h4> <b>Distance :&nbsp" + "<strong>" + str(
                round(res['routes'][0]['summary']['distance'] / 1000, 1)) + " Km </strong>" + "</h4></b>"
            duration_txt = "<h4> <b>Duration :&nbsp" + "<strong>" + str(
                round(res['routes'][0]['summary']['duration'] / 60, 1)) + " Mins. </strong>" + "</h4></b>"

            folium.GeoJson(data=decoded2).add_to(m)

            folium.Marker(
                location=list(end_port_to_end_plant[0][::-1]),
                popup="Start point",
                icon=folium.Icon(icon='map-marker', color="red"),
            ).add_to(m)

            folium.Marker(
                location=list(end_port_to_end_plant[1][::-1]),
                popup="End point",
                icon=folium.Icon(icon='map-marker', color="black"),
            ).add_to(m)
        else:
            folium.Marker(
                location=end_tuple_port,
                popup="Start pipe",
                icon=folium.Icon(icon='map-marker', color="lightgreen"),
            ).add_to(m)

            folium.Marker(
                location=end_plant_tuple[::-1],
                popup="End pipe",
                icon=folium.Icon(icon='map-marker', color="cadetblue"),
            ).add_to(m)

            pipe_full = [end_tuple_port, end_plant_tuple[::-1]]
            pipe_PolyLine = folium.PolyLine(locations=pipe_full, weight=3, color='purple')
            m.add_child(pipe_PolyLine)

    data = io.BytesIO()
    m.save(data, close_file=False)

    return data.getvalue().decode()

def plot_world_results_single_run(df, desired_metric):
    """Plots world map showing various cost metrics for producing H2."""
    data = df

    if desired_metric == 'Cheapest Medium':
        total = range(len(data))
        for i in total:
            if data.iloc[i, 28] == 'LOHC':
                data.iloc[i, 28] = 1
            if data.iloc[i, 28] == 'NH3':
                data.iloc[i, 28] = 2
            if data.iloc[i, 28] == 'H2 Liq':
                data.iloc[i, 28] = 3
            if data.iloc[i, 28] == 'H2 Gas':
                data.iloc[i, 28] = 4

        color_schemes = [
            ['#890000', '#890000', '#5c0000'],
            ['#1d79ad', '#1d79ad', '#1d79ad'],
            ['#4f5a90', '#374798', '#30375a'],
            ['#fff4b1', '#ffed86', '#ffdb00']
        ]

        colorscale = generate_Discrete_ColourScale(color_schemes)

        x = data.iloc[:, 28]

        fig = go.Figure(data=go.Scattergeo(
            lat=data.loc[:, 'Latitude'],
            lon=data.loc[:, 'Longitude'],
            mode='markers',
            text=x,
            marker=dict(
                color=x,
                size=3,
                colorscale=colorscale,
            )))

        fig.update_layout(
            geo=dict(
                showland=True,
                landcolor="rgb(212, 212, 212)",
                subunitcolor="rgb(255, 255, 255)",
                countrycolor="rgb(255, 255, 255)",
                showlakes=True,
                lakecolor="rgb(255, 255, 255)",
                showsubunits=True,
                showcountries=True,
                projection=dict(
                    type='natural earth'
                ),
            ),
            title='Cheapest transport medium by location',
            font_color='black',
            font_size=15,
            font_family='Times New Roman',

        )
        html = '<html><body>'
        html += plotly.offline.plot(fig, output_type='div', include_plotlyjs='cdn')
        html += '</body></html>'

        return html

    else:
        fig = go.Figure(data=go.Scattergeo(
            lat=data.loc[:, 'Latitude'],
            lon=data.loc[:, 'Longitude'],
            mode='markers',
            text=round(data.loc[:, desired_metric], 2),
            marker=dict(
                color=data.loc[:, desired_metric],
                size=3,
                colorscale='Portland',
                # reversescale = True,
                colorbar=dict(
                    title=dict(
                            side="right"),
                    outlinecolor="rgba(68, 68, 68, 0)",
                    ticks="outside",
                    showticksuffix="last",
                    dtick=1),

            ),
        ))

        fig.update_layout(
            geo=dict(
                # scope='europe',
                showland=True,
                landcolor="rgb(212, 212, 212)",
                subunitcolor="rgb(255, 255, 255)",
                countrycolor="rgb(255, 255, 255)",
                showlakes=True,
                lakecolor="rgb(255, 255, 255)",
                showsubunits=True,
                showcountries=True,
                projection=dict(
                    type='natural earth'
                ),
            ),
            font_color='black',
            font_size=15,
            font_family='Times New Roman'
        )
        fig.add_annotation(x=1.05, y=-0.08,
                            text="Black locations represent transport routes that could not be calculated",
                            showarrow=False)
        fig.add_annotation(x=1, y=0.977,
                            text=desired_metric,
                            font=dict(
                                size=18),
                            showarrow=False)

        html = '<html><body>'
        html += plotly.offline.plot(fig, output_type='div', include_plotlyjs='cdn')
        html += '</body></html>'

        return html

def plot_world_results_mc(path):
    

    mc_df = pd.read_csv(path, header=None)
    pd.DataFrame.info(mc_df)

    list_locations = pd.read_csv(os.environ.get("BASE_PATH") + "Data/locationslist.csv")
    data = mc_df.mean()
    dataframes = [list_locations[['Latitude', 'Longitude']], data]

    x = pd.concat(dataframes, axis=1)

    fig = go.Figure(data=go.Scattergeo(
        lat=x.loc[:, 'Latitude'],
        lon=x.loc[:, 'Longitude'],
        mode='markers',
        text=round(x.iloc[:, 2], 2),
        marker=dict(
            color=x.iloc[:, 2],
            size=3,
            colorscale='Portland',
            # reversescale = True,
            colorbar=dict(
                titleside="right",
                outlinecolor="rgba(68, 68, 68, 0)",
                ticks="outside",
                showticksuffix="last",
                dtick=5)
        ),
    ))

    fig.update_layout(
        geo=dict(
            # scope='europe',
            showland=True,
            landcolor="rgb(212, 212, 212)",
            subunitcolor="rgb(255, 255, 255)",
            countrycolor="rgb(255, 255, 255)",
            showlakes=True,
            lakecolor="rgb(255, 255, 255)",
            showsubunits=True,
            showcountries=True,
            projection=dict(
                type='natural earth'
            ),
        ),
        # title='Total cost per kg H2 (Eur) for H2 required in Cologne, Germany',
        font_color='black',
        font_size=15,
        font_family='Times New Roman'
    )
    fig.add_annotation(x=1.05, y=-0.08,
                        text="Black locations represent transport routes that could not be calculated",
                        showarrow=False)
    fig.add_annotation(x=1, y=0.977,
                        text="Cost",
                        font=dict(
                            size=18
                        ),
                        showarrow=False)

    html = '<html><body>'
    html += plotly.offline.plot(fig, output_type='div', include_plotlyjs='cdn')
    html += '</body></html>'

    return html

@staticmethod
def create_port_coordinates(df_ports):
    """Creates a list of the port co-ordinates that can be used to find the nearest port to any point. Requires no
    input."""

    coords = df_ports['coords'].values.tolist()
    coords = [i.strip('()') for i in coords]
    coords = [i.strip("'),'") for i in coords]
    coords = [i.split(', ') for i in coords]

    coords2 = []
    for i in range(len(coords)):
        li = []
        for j in range(2):
            li.append(float(coords[i][j]))
        coords2.append(li)

    return coords2

@staticmethod
def generate_Discrete_ColourScale(colour_set):
    # colour set is a list of lists
    colour_output = []
    num_colours = len(colour_set)
    divisions = 1. / num_colours
    c_index = 0.
    # Loop over the colour set
    for cset in colour_set:
        num_subs = len(cset)
        sub_divisions = divisions / num_subs
        # Loop over the sub colours in this set
        for subcset in cset:
            colour_output.append((c_index, subcset))
            colour_output.append((c_index + sub_divisions -
                                    .001, subcset))
            c_index = c_index + sub_divisions
    colour_output[-1] = (1, colour_output[-1][1])
    return colour_output
