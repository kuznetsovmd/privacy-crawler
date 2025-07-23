from functools import partial
from multiprocessing.pool import Pool

from crawler.modules.module import Module
from crawler.product import Product
from tools.functions import (
    get_logger, 
    read_models, 
    temp_descriptor, 
    write_models
)


def search_website(data, engines):
    manufacturer, keyword = data
    logger = get_logger()
    logger.info(f"Searching: {manufacturer} {keyword}")

    for engine in engines:
        site = engine.search(manufacturer, keyword)
        if site is not None:
            logger.info(f"Got website {site}")
            return manufacturer, site

    return manufacturer, None


class Websites(Module):

    def __init__(self, engines, descriptor):
        self.engines = engines
        self.descriptor = descriptor
        self.logger = get_logger()

    def run(self, pool: Pool = None):
        self.logger.info("Searching websites")

        tmp = temp_descriptor(self.descriptor, self.__class__.__name__, "1")

        products = read_models(self.descriptor, Product)
        manufacturers_keywords = {
            (p.manufacturer, p.keyword.replace("+", " ") if p.keyword else "")
            for p in products if p.manufacturer
        }

        search_func = partial(
            search_website,
            engines=self.engines,
            cooldown=2.0,
            random_cooldown=2.0
        )

        manufacturer_website = dict(pool.map(search_func, manufacturers_keywords))

        for p in products:
            if p.manufacturer:
                p.website = manufacturer_website.get(p.manufacturer)

        write_models(tmp, products)
        tmp.replace(self.descriptor)
        