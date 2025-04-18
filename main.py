"""
This is the main file to handle passed in args and call parse_files.

Author: Raine Fuerst
"""

import argparse
from parse_items import parse_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="The name of the input file to parse items for.")
    parser.add_argument("output_file", help="The name of the file to output the results.")
    parser.add_argument("--empty_desc", action="store_true", help="Add this argument if an empty description is valid.")
    args = parser.parse_args()
    # parse_files('errors_file.xlsx')
    parse_files(args.input_file, args.output_file, args.empty_desc)