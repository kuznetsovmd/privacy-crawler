from pathlib import Path
from typing import Callable, List, Set, Tuple
from bs4 import BeautifulSoup
from functools import partial
from multiprocessing.pool import Pool

from crawler.plugins.plugin import Plugin
from crawler.product import Product
from tools.functions import (
    chunked,
    concat_files, 
    gen_search_urls, 
    get_logger, 
    get_soup_from_url,
    load_last_id_page,
    read_models, 
    read_object_chunks_from_id,
    skip_to, 
    temp_descriptor, 
    write_models
)


def extract_product_links(data: Tuple[str, str], template, cooldown, random_cooldown) -> Tuple[str, str, Set[str]]:
    url, keyword = data
    soup = get_soup_from_url(url, cooldown, random_cooldown)
    if not soup:
        return keyword, url, set()
    return keyword, url, set(template(soup))


def extract_manufacturer(product: Product, templates, cooldown, random_cooldown) -> Product:
    logger = get_logger()
    soup = get_soup_from_url(product.url, cooldown, random_cooldown)
    if not soup:
        logger.warning("No markup is found")
        return product

    for template in templates:
        if manufacturer := template(soup):
            product.manufacturer = manufacturer
            logger.info(f"Got manufacturer: {manufacturer}")
            break
    return product


class BaseMarket(Plugin):

    def __init__(self,
                 search_url: str,
                 product_template: Callable[[BeautifulSoup], List[str]],
                 templates: Tuple[Callable[[BeautifulSoup], List[str]], ...],
                 keywords: List[str],
                 pages: int,
                 descriptor: str,
                 cooldown=0.0,
                 chunk_size=0.0,
                 random_cooldown=0.0):
        
        self.logger = get_logger()
        self.search_url = search_url
        self.descriptor = Path(descriptor)
        self.keywords = keywords
        self.pages = pages
        self.cooldown = cooldown
        self.random_cooldown = random_cooldown
        self.product_template = product_template
        self.templates = templates
        self.chunk_size = chunk_size

    def scrap_records(self, pool: Pool):
        tmp1 = temp_descriptor(self.descriptor, self.__class__.__name__, "cache")
        tmp2 = temp_descriptor(self.descriptor, self.__class__.__name__, "tmp")

        desc_id, _ = load_last_id_page(self.descriptor)
        last_id, last_page = load_last_id_page(tmp1)
        Product._counter = max(int(desc_id or 0), int(last_id or 0)) + 1

        product_func = partial(
            extract_product_links,
            template=self.product_template,
            cooldown=self.cooldown,
            random_cooldown=self.random_cooldown,
        )
        
        urls_iter = gen_search_urls(self.search_url, self.keywords, self.pages)
        skipped_iter = skip_to(urls_iter, last_page)
        for keyword, page, urls in pool.imap(product_func, skipped_iter):
            write_models(tmp1, [Product(url=u, keyword=keyword, page=page) for u in urls], mode="a")

        manufacturer_func = partial(
            extract_manufacturer,
            templates=self.templates,
            cooldown=self.cooldown,
            random_cooldown=self.random_cooldown,
        )

        last_id, _ = load_last_id_page(tmp2)

        models_iter = read_models(self.descriptor, Product)
        skipped_iter = skip_to(models_iter, last_id)

        for product in pool.imap(manufacturer_func, skipped_iter):
            write_models(tmp2, [product], mode="a")
        
        for i, model in enumerate(read_models(tmp1, Product), start=int(desc_id or 0) + 1):
            model.id = i
            write_models(tmp2, [model], mode="a")
        
        tmp2.replace(tmp1)
        concat_files([self.descriptor, tmp1], tmp2)
        tmp2.replace(self.descriptor)
        