from functools import partial
from multiprocessing.pool import Pool

from crawler.modules.module import Module
from crawler.product import Product
from tools.functions import (
    chunked,
    concat_files,
    get_logger,
    load_last_id_page,
    read_models,
    skip_to,
    temp_descriptor,
    write_models,
)


def search_website(data, engines, cooldown=2.0, random_cooldown=2.0):
    manufacturer, keyword = data
    logger = get_logger()
    logger.info(f"Searching: {manufacturer} {keyword}")

    for engine in engines:
        site = engine.search(manufacturer, keyword, cooldown=cooldown, random_cooldown=random_cooldown)
        if site is not None:
            logger.info(f"Got website {site}")
            return manufacturer, site

    return manufacturer, None


class Websites(Module):

    def __init__(self, descriptor, engines, cooldown=0.0, random_cooldown=0.0, chunk_size=64):
        self.descriptor = descriptor
        self.engines = engines
        self.cooldown = cooldown
        self.random_cooldown = random_cooldown
        self.chunk_size = chunk_size
        self.logger = get_logger()

    def run(self, pool: Pool = None):
        self.logger.info("Searching websites")

        tmp1 = temp_descriptor(self.descriptor, self.__class__.__name__, "cache")
        tmp2 = temp_descriptor(self.descriptor, self.__class__.__name__, "tmp")

        search_func = partial(
            search_website,
            engines=self.engines,
            cooldown=self.cooldown,
            random_cooldown=self.random_cooldown,
        )

        last_id, _ = load_last_id_page(tmp1)

        products_iter = read_models(self.descriptor, Product)
        skipped_iter = skip_to(products_iter, last_id, lambda x: x.id)

        site_cache = dict()
        for models in chunked(skipped_iter, self.chunk_size):
            models = list(models)
            pairs = [
                (m.manufacturer, m.keyword.replace("+", " ") if m.keyword else "")
                for m in models if m.manufacturer and m.manufacturer not in site_cache
            ]

            for manufacturer, website in pool.imap(search_func, pairs):
                site_cache[manufacturer] = website

            for m in models:
                m.website = site_cache.get(m.manufacturer, None)

            write_models(tmp1, models, mode="a")

        concat_files([tmp1], tmp2)
        tmp2.replace(self.descriptor)
        