import json
import os
import random
import re
from multiprocessing import Pool
from time import sleep

from crawler.plugins.plugin import Plugin
from crawler.website import Website
from tools.arrays import flatten_list


class MailTop(Plugin):

    captcha_catch = re.compile("captcha", flags=re.IGNORECASE)

    def __init__(self, keywords, pages, websites_json, cooldown=0., random_cooldown=0., sync=False):

        super().__init__(keywords, pages, None, cooldown=cooldown, random_cooldown=random_cooldown)

        self.sync = sync
        self.websites_json = websites_json

    def scrap_products(self, url):
        raise NotImplementedError("This method is not implemented!")

    def get_product(self, url):
        raise NotImplementedError("This method is not implemented!")

    def scrap(self, p: Pool = None):

        Website.counter = len(self.items)

        for keyword in self.keywords:
            search_urls = self.gen_search_urls(keyword, self.pages)

            found_items = flatten_list([self.scrap_websites(url) for url in search_urls]
                                       if p is None or self.sync else p.map(self.scrap_websites, search_urls))

            websites = [Website(keyword=k, website=w)
                        for k, w in [(keyword, item) for item in found_items]]

            self.items.extend(websites)

        with open(os.path.relpath(self.websites_json), "w") as f:
            json.dump(self.items, f, indent=2)

    def gen_search_urls(self, keyword, pages):
        return [f"https://top.mail.ru/Rating/{keyword}/Today/Visitors/{p}.html"
                for p in range(1, self.pages + 1)]

    def scrap_websites(self, url):
        sleep(self.cooldown + random.random() * self.random_cooldown)
        return self.scrap_page(
            url,
            (self.website_template,),
        )

    def captcha(self, markup):
        pass

    @classmethod
    def website_template(cls, soup):
        return [item.select_one("a.t90.t_grey").get('href')
                for item in set([item.parent for item in soup.select("td.it-title > a.t90.t_grey")])]
