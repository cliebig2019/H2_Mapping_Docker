from H2_Mapping_Updated import ui_library
from H2_Mapping_Updated import mc_main
from H2_Mapping_Updated import ParameterSet
import argparse
from H2_Mapping_Updated import DisplayMap
from dotenv import load_dotenv
import os
from Utils.writeFile import write_html
from Utils.writeFile import write_json
from Utils.writeFile import write_file

def main(latitude, longitude, h2_demand, year, centralised, pipeline, max_pipeline_dist, electrolyzer, montecarlo, iterations):

    if montecarlo:

        paramSet = ParameterSet.ParameterSet()
        paramSet.latitude = latitude
        paramSet.longitude = longitude
        paramSet.demand = h2_demand
        paramSet.year = year
        paramSet.centralised = centralised
        paramSet.pipeline = pipeline
        paramSet.max_dist = max_pipeline_dist
        paramSet.electrolyzer_type = electrolyzer
        paramSet.iterations = iterations

        mc_computing = mc_main.MonteCarloComputing(paramSet)
        result = mc_computing.run_mc_model()

        base_path = os.environ.get("RESULT_PATH") + "/mc/"
        visualization_path = base_path + "visualization/"

        write_file(result.to_json(orient="records", lines=True, indent=4), str(os.environ.get("RESULT_PATH")) + "results.json")

        os.mkdir(visualization_path)

        solar_html = DisplayMap.plot_world_results_mc(base_path + "solar_cost.csv")
        write_html(solar_html, visualization_path + "solar_cost.html")

        generation_html = DisplayMap.plot_world_results_mc(base_path + "generation_cost_per_kg_h2.csv")
        write_html(generation_html, visualization_path + "generation_cost.html")

        total_html = DisplayMap.plot_world_results_mc(base_path + "total_cost_per_kg_h2.csv")
        write_html(total_html, visualization_path + "total_costs.html")

        wind_html = DisplayMap.plot_world_results_mc(base_path + "wind_cost.csv")
        write_html(wind_html, visualization_path + "wind_costs.html")
    else:

        paramSet = ParameterSet.ParameterSet()
        paramSet.latitude = latitude
        paramSet.longitude = longitude
        paramSet.demand = h2_demand
        paramSet.year = year
        paramSet.centralised = centralised
        paramSet.pipeline = pipeline
        paramSet.max_dist = max_pipeline_dist
        paramSet.electrolyzer_type = electrolyzer

        computation = ui_library.Computing(paramSet)
        min_cost, mindex, cheapest_source, cheapest_medium, cheapest_elec, final_path = computation.run_single_model()

        result = {
            "min_cost": str(min_cost),
            "mindex": str(mindex),
            "cheapest_source": str(cheapest_source),
            "cheapest_medium": str(cheapest_medium),
            "cheapest_elec": str(cheapest_elec),
            "final_path": str(final_path)
        }

        base_path = os.environ.get("RESULT_PATH")
        visualization_path = base_path + "visualization/"

        write_json(result, str(base_path) + "results.json")


        os.mkdir(visualization_path)

        route_html, total_cost_html, gen_cost_html, transport_cost_html, cheapest_medium_html = DisplayMap.normal(base_path + "final_df.csv")

        write_html(route_html, visualization_path + "route.html")
        write_html(total_cost_html, visualization_path + "total_cost.html")
        write_html(gen_cost_html, visualization_path + "gen_cost.html")
        write_html(transport_cost_html, visualization_path + "transport_cost.html")
        write_html(cheapest_medium_html, visualization_path + "cheapest_medium.html")
        
        
load_dotenv()

parser = argparse.ArgumentParser(description="Calculate H2 Mapping", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-la", "--latitude", nargs="?", type=float, required=True)
parser.add_argument("-lo", "--longitude", nargs="?", type=float, required=True)
parser.add_argument("-h2", "--h2_demand", nargs="?", type=float, required=True)
parser.add_argument("-y", "--year", nargs="?", type=int, required=True)
parser.add_argument("-c", "--centralised", nargs="?", type=bool, required=True)
parser.add_argument("-p", "--pipeline", nargs="?", type=bool, required=True)
parser.add_argument("-mpd", "--max_pipeline_dist", nargs="?", type=float, required=True)
parser.add_argument("-e", "--electrolyzer", nargs="?", type=str, required=True, choices=["alkaline", "solid oxide electrolyzer cell", "polymer electrolyte membrane"])
parser.add_argument("-mc", "--montecarlo", nargs="?", type=bool, required=False)
parser.add_argument("-it", "--iterations", nargs="?", type=int, required=False)

args=parser.parse_args()

main(args.latitude, args.longitude, args.h2_demand, args.year, args.centralised, args.pipeline, args.max_pipeline_dist, args.electrolyzer, args.montecarlo, args.iterations)


