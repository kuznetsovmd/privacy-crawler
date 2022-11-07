import random
import re
from time import sleep

from crawler.plugins.plugin import Plugin
from tools.exceptions import CaptchaException


class Walmart(Plugin):
    sanitize_label = re.compile(r"[^\w]|_")
    sanitize_value = re.compile(r"[^\w ]|_")
    manufacturer = re.compile(r"^manufacturer$", flags=re.IGNORECASE)
    brand = re.compile(r"^brand$", flags=re.IGNORECASE)
    captcha_catch = re.compile("verify your identity", flags=re.IGNORECASE)

    def __init__(self, keywords, pages, products_json, cooldown=0., random_cooldown=0.,
                 max_captcha_attempts=0, max_error_attempts=0, sync=False):

        super().__init__(keywords, pages, products_json,
                         cooldown=cooldown, random_cooldown=random_cooldown,
                         max_captcha_attempts=max_captcha_attempts,
                         max_error_attempts=max_error_attempts, sync=sync)

    def gen_search_urls(self, keyword, pages):
        return [f"https://www.walmart.com/search/?page={p}&ps=40&query={keyword}"
                for p in range(1, self.pages + 1)]

    def scrap_products(self, url):
        sleep(self.cooldown + random.random() * self.random_cooldown)
        return self.scrap_page(
            url,
            (self.product_template,),
        )

    def get_product(self, url):
        sleep(self.cooldown + random.random() * self.random_cooldown)
        return url, self.scrap_page(
            url,
            (self.template1, self.template2),
        )

    def captcha(self, markup):
        if self.captcha_catch.search(markup):
            raise CaptchaException()

    @classmethod
    def product_template(cls, soup):
        return [f"https://www.walmart.com{item.get('href')}"
                for item in soup.findAll("a", {"class": "product-title-link"})]

    def template1(self, body):
        try:
            div = body.find("table", {"class": "product-specification-table"})
            for tr in div.tbody.findChildren("tr"):
                tds = tr.findChildren("td")
                label = self.sanitize_label.sub("", tds[0].text)
                if self.manufacturer.search(label):
                    manufacturer = tds[1].text
                    self.logger.info(f"Got manufacturer {manufacturer}")
                    return self.sanitize_value.sub("", manufacturer).lower()

        except (AttributeError, TypeError):
            self.logger.error("Manufacturer field is not found")

    def template2(self, body):
        try:
            div = body.find("table", {"class": "product-specification-table"})
            for tr in div.tbody.findChildren("tr"):
                tds = tr.findChildren("td")
                label = self.sanitize_label.sub("", tds[0].text)
                if self.brand.search(label):
                    manufacturer = tds[1].text
                    self.logger.info(f"Got manufacturer {manufacturer}")
                    return self.sanitize_value.sub("", manufacturer).lower()

        except (AttributeError, TypeError):
            self.logger.error("Manufacturer field is not found")
