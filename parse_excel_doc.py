import pandas
import requests
from bs4 import BeautifulSoup


def get_properties(soup):
    ret_val = {}
    prop = soup.find_all("div", class_="bg3wiki-property-list")
    if len(prop) < 1:
        raise Exception("Error parsing HTML: Cannot Find Properties")
    if len(prop) > 1:
        raise Exception("Error parsing HTML: Found Multiple Possible Property Sections")
    property_lines = prop[0].find_all("li")
    if not property_lines:
        raise Exception(f"Error parsing HTML: No properties in list")
    for line in property_lines:
        str_line = str(str(line).encode('ascii', 'ignore'))
        if "rarity" in str_line.lower():
            ret_val["rarity"] = str_line.rsplit("Rarity: ", maxsplit=1)[-1].rsplit("</li>", maxsplit=1)[0].rsplit(";\">", maxsplit=1)[-1].rsplit("</span>", maxsplit=1)[0]
        elif "weight" in str_line.lower():
            ret_val["weight"] = float(str_line.rsplit("kg / ", maxsplit=1)[-1].rsplit("lb", maxsplit=1)[0])
        elif "price" in str_line.lower():
            ret_val["price"] = int(str_line.rsplit("Price: ", maxsplit=1)[-1].rsplit("gp", maxsplit=1)[0])
    return(ret_val)







if __name__ == "__main__":
    excel_file = pandas.read_excel('begin_item_doc.xlsx')
    urls = excel_file["url"]
    for index, url in enumerate(urls):
        try:
            r = requests.get(url)
            properties = get_properties(BeautifulSoup(r.content, 'html5lib'))
        except Exception as e:
            print(f"Error ocurred during {excel_file["name"][index]}: {e}")
        