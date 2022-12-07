import json
import os
import random
import re
from multiprocessing import Pool
from time import sleep

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from crawler.plugins.plugin import Plugin
from crawler.web.driver import Driver
from crawler.website import Website
from tools.arrays import flatten_list

from selenium.webdriver.support import expected_conditions as ec


class RamblerTop(Plugin):

    def __init__(self, websites_json, pages, cooldown=0.,
                 random_cooldown=0.):
        super().__init__(None, None, None, cooldown=cooldown,
                         random_cooldown=random_cooldown)

        self.websites_json = websites_json
        self.records = []
        self.pages = pages

    def scrap_products(self, url):
        raise NotImplementedError("This method is not implemented!")

    def get_product(self, url):
        raise NotImplementedError("This method is not implemented!")

    def scrap(self, p: Pool = None):
        try:
            with open(os.path.relpath(self.websites_json), "r") as f:
                self.records = json.load(f)
        except FileNotFoundError:
            pass

        Website.counter = len(self.records)

        search_urls = self.gen_search_urls(None, self.pages)
        found_items = flatten_list(p.map(self.scrap_websites, search_urls))
        websites = [Website(keyword=k, website=w)
                    for k, w in [(None, item) for item in found_items]]

        self.records.extend(websites)

        with open(os.path.relpath(self.websites_json), "w") as f:
            json.dump(self.records, f, indent=2)

    def gen_search_urls(self, keyword, pages):
        return [f"https://top100.rambler.ru/navi/?period=month&sort=viewers"
                f"&page={p}&_openstat=catalogue_top100"
                for p in range(1, pages + 1)]

    def scrap_websites(self, url):
        return self.scrap_page(
            url,
            (self.template1,),
        )

    def scrap_page(self, url, templates):
        driver = Driver()
        driver.get(url, cooldown=self.cooldown,
                   random_cooldown=self.random_cooldown)
        while not Driver().wait(ec.presence_of_element_located(
                (By.TAG_NAME, "table"))):
            driver.get(url, cooldown=self.cooldown,
                       random_cooldown=self.random_cooldown)
        markup = driver.source()
        if markup:
            soup = BeautifulSoup(markup, "lxml").find("body")
            for t in templates:
                match = t(soup)
                if match is not None:
                    return match

    @classmethod
    def template1(cls, soup):
        return [item.get('href') for item in soup.select(
            "tr > td > div > div > div > a")]
