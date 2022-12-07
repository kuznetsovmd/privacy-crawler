import json
import os
import random
import re
from multiprocessing import Pool
from time import sleep

from bs4 import BeautifulSoup

from crawler.plugins.plugin import Plugin
from crawler.web.driver import Driver
from crawler.website import Website
from tools.arrays import flatten_list


class MailTop(Plugin):

    def __init__(self, keywords, websites_json, cooldown=0.,
                 random_cooldown=0.):
        super().__init__(keywords, None, None, cooldown=cooldown,
                         random_cooldown=random_cooldown)

        self.websites_json = websites_json
        self.records = []

    def scrap_products(self, url):
        raise NotImplementedError("This method is not implemented!")

    def get_product(self, url):
        raise NotImplementedError("This method is not implemented!")

    def find_last_page(self, k, p=1000000):
        Driver().get(f"https://top.mail.ru/Rating"
                     f"/{k}/Month/Visitors/{p}.html")
        markup = Driver().source()
        soup = BeautifulSoup(markup, "lxml").find("body")
        number = self.template2(soup)
        number = int(re.findall(r"\d+", number)[0])
        return number

    def scrap(self, p: Pool = None):
        try:
            with open(os.path.relpath(self.websites_json), "r") as f:
                self.records = json.load(f)
        except FileNotFoundError:
            pass

        Website.counter = len(self.records)

        for keyword in self.keywords:
            last_page = self.find_last_page(keyword, 1)
            self.logger.info(f"Found {last_page} pages in category {keyword}")
            search_urls = self.gen_search_urls(keyword, last_page)
            found_items = flatten_list(p.map(self.scrap_websites, search_urls))
            websites = [Website(keyword=k, website=w)
                        for k, w in [(keyword, item) for item in found_items]]

            self.records.extend(websites)

        with open(os.path.relpath(self.websites_json), "w") as f:
            json.dump(self.records, f, indent=2)

    def gen_search_urls(self, keyword, pages):
        return [f"https://top.mail.ru/Rating/{keyword}/Month/Visitors/{p}.html"
                for p in range(1, pages + 1)]

    def scrap_websites(self, url):
        sleep(self.cooldown + random.random() * self.random_cooldown)
        return self.scrap_page(
            url,
            (self.template1,),
        )

    @classmethod
    def template1(cls, soup):
        return [item.select_one("a.t90.t_grey").get('href')
                for item in set([item.parent for item in
                                 soup.select("td.it-title > a.t90.t_grey")])]

    @classmethod
    def template2(cls, soup):
        return soup.select_one("div.f_left.t80").find_all("b")[-1].get_text()

