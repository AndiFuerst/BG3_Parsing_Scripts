"""
This file parses an Excel file containing the basic information for BG3 items and creates a new
Excel file with all of the missing information added.

Author: Raine Fuerst
"""


import re
import chime
import pandas
import requests
import urllib3
from bs4 import BeautifulSoup


VALID_RARITIES = [
    "Common",
    "Uncommon",
    "Rare",
    "Very Rare",
    "Legendary",
    "Story Item"
]


def is_duplicate_variation(soup):
    """
    Determines whether the variations are using the same chunk of data

    Args:
        soup (BeautifulSoup): The html to be parsed for information

    Returns:
        bool: True, if the same data should be used, false otherwise
    """
    line = soup.find_all("div", class_="bg3wiki-blockquote-text")
    return True if "●" in str(line) else False


def get_properties(soup, var_num):
    """
    Returns a dictionary containing all of the information under the "properties" section: rarity,
    weight, and price.

    Args:
        soup (BeautifulSoup): The html to be parsed for information
        var_num (int): If there are multiple variations on the same item, this will determine which
            variation in the list to parse for. 

    Returns:
        Dictionary: A Dictionary containing the properties for the given item: 
            {"rarity": _, "weight": _, "price": _ "errors": []} if any information is missing from
            the HTML, these values will be None. The "errors" list will contain any issues that 
            occurred during the processing of the HTML file.
    """
    ret_val = {
        "rarity": None,
        "weight": None,
        "price": None,
        "errors": []
    }
    prop = soup.find_all("div", class_="bg3wiki-property-list")
    if var_num > 1:
        if is_duplicate_variation(soup):
            var_num = 1
    if len(prop) < var_num:
        ret_val["errors"].append("Error parsing HTML: Too few property lists")
    else:
        property_lines = prop[var_num - 1].find_all("li")
        if not property_lines:
            property_lines = prop[var_num - 1].find_all("dd")
        for line in property_lines:
            str_line = str(str(line).encode('ascii', 'ignore'))
            if "rarity" in str_line.lower():
                rarity_str = (
                    str_line.rsplit("Rarity:", maxsplit=1)[-1]
                        .rsplit("</li>", maxsplit=1)[0]
                )
                for rarity in VALID_RARITIES:
                    if rarity.lower() in rarity_str.lower():
                        ret_val["rarity"] = rarity
                        break
                if not ret_val["rarity"]:
                    ret_val["errors"].append(f"Invalid Rarity: {rarity_str}")
            elif "weight" in str_line.lower():
                weight_str = str_line.rsplit("kg / ", maxsplit=1)[-1].rsplit("lb", maxsplit=1)[0].strip()
                if re.match(r"^\d+(\.\d+)?$", weight_str):
                    ret_val["weight"] = float(weight_str)
                else:
                    ret_val["errors"].append(f"Invalid Weight: {weight_str}")
            elif "price" in str_line.lower():
                price_str = str_line.rsplit("Price: ", maxsplit=1)[-1].split("gp")[0].strip()
                if price_str.isdigit():
                    ret_val["price"] = int(price_str)
                else:
                    ret_val["errors"].append(f"Invalid Price: {price_str}")
    return ret_val

def get_description(soup, var_num, empty_desc):
    """
    Returns a tuple containing the item's description and whether the description is valid.

    Args:
        soup (BeautifulSoup): The html to be parsed for information
        var_num (int): If there are multiple variations on the same item, this will determine which
            variation in the list to parse for. 
        empty_desc (bool): True if empty descriptions are valid, False otherwise

    Returns:
        Tuple(bool, string): A tuple containing the validity of the description and the item's
            description.
            bool: True if the description is valid, false otherwise
            string: The description if bool is true, the error string otherwise
    """
    line = soup.find_all("div", class_="bg3wiki-blockquote-text")
    line = [str(x).rsplit("●", maxsplit=1)[-1] for x in line]
    if len(line) < var_num:
        if empty_desc:
            line = ""
        else:
            return (False, f"Invalid Description: No description for the given variation: {var_num}")
    description = str(line).rsplit("<p>", maxsplit=1)[-1]
    description = description.rsplit("</p>", maxsplit=1)[0]
    description = "".join([x.split(">")[-1] for x in description.split("<")])
    description = description.split("[", maxsplit=1)[-1].rsplit("]", maxsplit=1)[0]
    description = "".join(description.split("\\n"))
    description = description.translate(str.maketrans("‘’“„", "''\"\"",  '\\'))
    description = "'".join(description.split("''"))
    if description.count("'") % 2 != 0:
        description = "".join(description.split("'"))
    if description.count('"') % 2 != 0:
        description = "".join(description.split('"'))
    if not re.match(r"^(?!\[)[^●]+(?<!])$", description):
        for char in description:
            if not re.match(r"^(?!\[)[^●]+(?<!])$", char):
                return (False, f"Invalid Description: Invalid Character in Description: {char}")
    if any (x in description for x in ["''", '""', "'\"", "\"'"]):
        return(False, f"Invalid Description: Duplicate Quotes: {description}")
    return (True, description)


def percentage_message(index, total):
    """
    Determines and prints out the percentage completed.

    Args:
        index (int): The current index
        total (int): The total number of items to process
    """
    fraction = int((index / total) * 100)
    fraction_old = int(((index -1) / total) * 100)
    if fraction - fraction_old < 1 and index > 0:
        return
    ending = "\n" if index == total - 1 else "\r"
    padding = ""
    if fraction < 10:
        padding = "0"
    print(f"{padding}{fraction}%", end=ending)


def parse_files(input_file, output_file, empty_desc):
    """
    Parses the given Excel file and creates a new Excel file with all of the missing information.

    Args:
        input_file (str): The excel file containing items to be parsed
        output_file (str): The excel file to output the results into
        empty_desc (bool): True if empty descriptions are valid, False otherwise
    """
    chime.theme('material')
    print("Parsing Beginning")
    excel_file = pandas.read_excel(input_file)
    urls = excel_file["url"]
    variations = excel_file["variation"]
    data = {
        "rarities": [None] * len(urls),
        "weights": [None] * len(urls),
        "prices": [None] * len(urls),
        "desc": [None] * len(urls)
    }
    errors = {}
    item_errors = {
        "item_id": [],
        "category": [],
        "sub_category": [],
        "name": [],
        "variation": [],
        "url": [],
    }
    for index, url in enumerate(urls):
        properties = {
            "rarity": None,
            "weight": None,
            "price": None,
            "errors": []
        }
        percentage_message(index, len(urls))
        try:
            r = requests.get(url, timeout=5)
            properties = get_properties(
                BeautifulSoup(r.content, 'html5lib'), int(variations[index])
            )
            (desc_valid, desc) = get_description(
                BeautifulSoup(r.content, 'html5lib'), int(variations[index]), empty_desc
            )
        except requests.exceptions.MissingSchema:
            properties["errors"].append(f"Invalid URL: {url}")
            desc_valid = False
        except urllib3.exceptions.ReadTimeoutError:
            properties["errors"].append(f"Timeout Error: {url}")
            desc_valid = False
        # except Exception as error:
        #     properties["errors"].append(f"Misc Error: {error}: {url}")
        #     desc_valid = False

        data["rarities"][index] = properties["rarity"]
        data["prices"][index] = properties["price"]
        data["weights"][index] = properties["weight"]
        
        if properties["errors"] or not desc_valid:
            item_errors["item_id"].append(excel_file["item_id"][index])
            item_errors["category"].append(excel_file["category"][index])
            item_errors["sub_category"].append(excel_file["sub_category"][index])
            item_errors["name"].append(excel_file["name"][index])
            item_errors["variation"].append(excel_file["variation"][index])
            item_errors["url"].append(excel_file["url"][index])
            errors[excel_file["name"][index]] = properties["errors"] if properties["errors"] else [desc] 
        if desc_valid:
            data["desc"][index] = desc
    excel_file["rarity"] = data["rarities"]
    excel_file["price_gp"] = data ["prices"]
    excel_file["weight_lb"] = data["weights"]
    excel_file["description"] = data["desc"]
    try:
        excel_file.to_excel(output_file, sheet_name='Sheet1')
    except(PermissionError):
        chime.warning()
        input(f"Permission Error with '{output_file}'\nPress any button to try again:")
        excel_file.to_excel(output_file, sheet_name='Sheet1')
    print("The following errors occurred during parsing:")
    for item, error_list in errors.items():
        print(f"\t{item}")
        for error in error_list:
            print(f"\t\t{error}")
    error_file = pandas.DataFrame(item_errors)
    try:        
        error_file.to_excel('errors_file.xlsx', sheet_name='Sheet1')
    except(PermissionError):
        chime.warning()
        input("Permission Error with 'errors_file.xlsx'\nPress any button to try again:")
        error_file.to_excel('errors_file.xlsx', sheet_name='Sheet1')
    print("Created 'errors_file.xlsx' with all of the items with errors.")
    chime.success()


