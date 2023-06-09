from H2_Mapping_Updated import ui_library
from H2_Mapping_Updated import mc_main
from H2_Mapping_Updated import ParameterSet
import argparse
from dotenv import load_dotenv

def main(latitude, longitude, h2_demand, year, centralised, pipeline, max_pipeline_dist, alkaline):

    paramSet = ParameterSet.ParameterSet()
    paramSet.latitude = latitude
    paramSet.longitude = longitude
    paramSet.demand = h2_demand
    paramSet.year = year
    paramSet.centralised = centralised
    paramSet.pipeline = pipeline
    paramSet.max_dist = max_pipeline_dist
    paramSet.electrolyzer_type = alkaline

    computation = ui_library.Computing(paramSet)
    result = computation.run_single_model()

    print(result)

    # Store results in database, also created file

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

args=parser.parse_args()

main(args.latitude, args.longitude, args.h2_demand, args.year, args.centralised, args.pipeline, args.max_pipeline_dist, args.electrolyzer)


