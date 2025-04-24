"""
This is the main file to handle passed in args and call parse_files.

Author: Raine Fuerst
"""

import argparse
from item_collector import ItemCollector

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="The name of the input file to parse items for.")
    parser.add_argument("output_file", help="The name of the file to output the results.")
    parser.add_argument("--empty_desc", action="store_true", help="Add this argument if an empty description is valid.")
    args = parser.parse_args()
    collector = ItemCollector(args.input_file)
    collector.run()