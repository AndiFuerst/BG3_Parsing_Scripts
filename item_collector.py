"""
This file holds the ItemCollector class, which handles collecting the list of items and calls
the corresponding parser to parse the given item.

TODO: Handle the collection of items

@Author: Raine Fuerst
"""

import json
import requests
import urllib3
import pandas as pd
from bs4 import BeautifulSoup

class ItemCollector():
    """
    This class handles collecting the list of items and calls the corresponding parser to parse 
    the given item.
    """

    def __init__(self, input_file):
        self.input_file = input_file
        self.item_df = pd.DataFrame({"name": [], "url": []})
        self.errors = {
            "Item Collection": [],
            "Items": [],
        }

    def run(self):
        """
        Begin the process to collect the list of items and parse them into their data.
        """
        self._parse_input_urls()
        # self._collect_items()

    def _parse_input_urls(self):
        """
        Parse the list of urls from the input file for items. Adds the items to the dataframe.
        """
        items = {
            "name": [],
            "url": [],
        }
        with open(self.input_file, "r", encoding="utf-8") as f:
            url_dict = json.load(f)
        for url_data in url_dict["Input Urls"]:
            try:
                r = requests.get(url_data["url"], timeout=5)
            except requests.exceptions.MissingSchema:
                self.errors["Item Collection"].append(f"Invalid URL: {url_data["url"]}")
            except urllib3.exceptions.ReadTimeoutError:
                self.errors["Item Collection"].append(f"Timeout Error: {url_data["url"]}")
            else:
                result = self._parse_items_list_soup(BeautifulSoup(r.content, 'html5lib'))
                items["name"].extend(result["name"])
                items["url"].extend(result["url"])
                if url_data["special"]:
                    result = self._parse_items_special_soup(BeautifulSoup(r.content, 'html5lib'))
                    items["name"].extend(result["name"])
                    items["url"].extend(result["url"])
        for missing_item in url_dict["Missing Items"]:
            items["name"].append(missing_item["name"])
            items["url"].append(missing_item["url"])
        for index in range(len(items["url"])):
            if (
                not self.item_df["url"].isin([items["url"][index]]).any() and 
                not list(filter(lambda x: x['url'] == items["url"][index], url_dict["Input Urls"]))
            ):
                self.item_df.loc[len(self.item_df)] = [items["name"][index], items["url"][index]]
        self.item_df.to_excel("test.xlsx", sheet_name='Sheet1')

    def _parse_items_list_soup(self, soup):
        """
        Given a BeautifulSoup containing a table of items, this method will parse that table
        and return a dict of urls
        Args:
        soup (BeautifulSoup): The HTML BeautifulSoup to be parsed for items

        Returns:
        dict: A dict containing the urls and names of the items parsed 
        """
        return_dict = {
            "name": [],
            "url": []
        }
        item_list = (
            soup.findAll("span", class_="bg3wiki-itemicon") +
            soup.findAll("span", class_="bg3wiki-itemicon-wrapper")
        )
        for item in item_list:
            for data in item.findAll("a"):
                url = f"https://bg3.wiki{data.attrs['href']}"
                if 'index' not in url and url not in return_dict["url"]:
                    return_dict["url"].append(url)
                    return_dict["name"].append(data.attrs["title"])
        return return_dict

    def _parse_items_special_soup(self, soup):
        """
        Given a BeautifulSoup containing a format of items (different than the majority), this 
        method will parse that format and return a dict of urls.

        Args:
        soup (BeautifulSoup): The HTML BeautifulSoup to be parsed for items

        Returns:
        dict: A dict containing the urls and names of the items parsed.
        """
        return_dict = {
            "name": [],
            "url": []
        }
        remove_footer = soup.find("div", class_="navbox")
        if remove_footer:
            remove_footer.decompose()
        for item in soup.findAll("span", class_="bg3wiki-icontext-icon"):
            for data in item.findAll("a"):
                url = f"https://bg3.wiki{data.attrs['href']}"
                if "Condition" not in url and url not in return_dict["url"]:
                    return_dict["url"].append(url)
                    return_dict["name"].append(data.attrs["title"])
        return return_dict

    def _collect_items(self):
        """
        Collect the list of the items within the BG3 wiki.

        TODO: Refactor this method to collect the list of items
        """
        # Verify item is obtainable?
        for index, row in self.item_df.iterrows():
            try:
                r = requests.get(row["url"], timeout=5)
            except requests.exceptions.MissingSchema:
                if row["name"] not in self.errors:
                    self.errors[row["name"]] = []
                self.errors[row["name"]].append(f"Invalid URL: {row['url']}")
                self.item_df.loc[index]["variation_data"] = None
            except urllib3.exceptions.ReadTimeoutError:
                if row["name"] not in self.errors:
                    self.errors[row["name"]] = []
                self.errors[row["name"]].append(f"Timeout Error: {row['url']}")
                self.item_df.loc[index]["variation_data"] = None
            else:
                self.item_df.loc[index]["variation_data"] = (
                    self._get_var_spec_soup(BeautifulSoup(r.content, 'html5lib'), row["variation"])
                )

    def _get_var_spec_soup(self, soup, var_num):
        """
        This method breaks down the given BeautifulSoup so that only the wanted variation is left.

        Args:
        soup (BeautifulSoup): The HTML BeautifulSoup to be broken down
        var_num (int): The integer representing which variation to return

        Returns:
        BeautifulSoup: The HTML BeautifulSoup with only the variation specific data provided.
        """
        return NotImplemented
