from multiprocessing.pool import Pool

from crawler.modules.module import Module
from tools.functions import get_logger


class Urls(Module):

    def __init__(self, plugins):
        self.plugins = plugins

    def run(self, p: Pool = None):
        get_logger().info("Searching urls")

        for plugin in self.plugins:
            plugin.scrap_records(p)
            