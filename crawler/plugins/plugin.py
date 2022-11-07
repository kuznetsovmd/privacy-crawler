import json
import logging
import os
import random
import re
from multiprocessing import Pool
from time import sleep

from bs4 import BeautifulSoup
from selenium.common.exceptions import WebDriverException

import config
from crawler.product import Product
from crawler.web.driver import Driver
from tools.arrays import flatten_list
from tools.exceptions import CaptchaException


class Plugin:

    def __init__(self, keywords, pages, products_json,
                 max_error_attempts=0, max_captcha_attempts=0,
                 cooldown=0., random_cooldown=0., sync=False):
        self.keywords = keywords
        self.pages = pages
        self.products_json = products_json
        self.sync = sync
        self.to_query = re.compile(r"\s+")
        self.items = []
        self.cooldown = cooldown
        self.random_cooldown = random_cooldown
        self.max_error_attempts = max_error_attempts
        self.max_captcha_attempts = max_captcha_attempts

        self.logger = logging.getLogger(f"pid={os.getpid()}")

    def gen_search_urls(self, keyword, pages):
        raise NotImplementedError("Scraper is not implemented!")

    def scrap_products(self, url):
        raise NotImplementedError("Scraper is not implemented!")

    def get_product(self, url):
        raise NotImplementedError("Scraper is not implemented!")

    def on_captcha_exception(self):
        self.logger.error("Sorry, we need to make sure that you are not a robot")
        sleep(self.cooldown + random.random() * self.random_cooldown)

        driver = Driver()
        driver.change_proxy()
        driver.change_useragent()
        driver.restart_session()
        driver.clear_cookies()

    def on_webdriver_exception(self):
        self.logger.error("Webdriver exception, potentially net error")
        sleep(self.cooldown + random.random() * self.random_cooldown)

        driver = Driver()
        driver.change_proxy()
        driver.restart_session()

    def captcha(self, markup):
        return False

    def scrap(self, p: Pool = None):

        try:
            with open(os.path.relpath(self.products_json), "r") as f:
                self.items = json.load(f)
        except FileNotFoundError:
            pass

        Product.counter = len(self.items)

        for keyword in self.keywords:
            search_urls = self.gen_search_urls(self.to_query.sub("+", keyword), self.pages)

            items_urls = flatten_list([self.scrap_products(url) for url in search_urls]
                                      if p is None or self.sync else p.map(self.scrap_products, search_urls))

            found_items = [self.get_product(product) for product in items_urls] \
                if p is None or self.sync else p.map(self.get_product, items_urls)

            products = [Product(keyword=k, url=u, manufacturer=m)
                        for k, u, m in [(keyword, *item) for item in found_items]]

            self.items.extend(products)

        with open(os.path.relpath(self.products_json), "w") as f:
            json.dump(self.items, f, indent=2)

    def scrap_page(self, url, templates):

        driver = Driver()
        net_error = 0

        markup = ""
        while True:

            try:
                markup = driver.get(url)
                self.captcha(markup)
                break

            except WebDriverException:
                self.on_webdriver_exception()
                net_error += 1
                if net_error > self.max_error_attempts:
                    break

            except CaptchaException:
                self.on_captcha_exception()
                net_error += 1
                if net_error > self.max_captcha_attempts:
                    break

        soup = BeautifulSoup(markup, "lxml").find("body")
        for t in templates:
            match = t(soup)
            if match is not None:
                return match
