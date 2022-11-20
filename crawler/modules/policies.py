import json
import logging
import os
from multiprocessing import Pool

from bs4 import BeautifulSoup

from crawler.modules.module import Module
from crawler.web.driver import Driver


class Policies(Module):

    def __init__(self, websites_json, policies_json, link_matcher,
                 cooldown=0., random_cooldown=0.):

        super(Policies, self).__init__()

        self.link_matcher = link_matcher
        self.websites_json = websites_json
        self.policies_json = policies_json
        self.cooldown = cooldown
        self.random_cooldown = random_cooldown

    def run(self, p: Pool = None):
        self.logger.info("Searching policies")

        jobs = set(filter(None, [r["website"] for r in self.records]))
        privacy_policies = p.map(self.scrap_policies_urls, jobs)

        for item in self.records:
            for website, policy in privacy_policies:
                if website == item["website"]:
                    item["policy"] = policy

    def bootstrap(self):
        with open(os.path.relpath(self.websites_json), "r") as f:
            self.records = json.load(f)

    def finish(self):
        with open(os.path.relpath(self.policies_json), "w") as f:
            json.dump(self.records, f, indent=2)

    def scrap_policies_urls(self, website_url):
        logger = logging.getLogger(f"pid={os.getpid()}")
        logger.info(f"Getting policy for {website_url}")
        markup = Driver().get(website_url, cooldown=self.cooldown,
                              random_cooldown=self.random_cooldown)
        if markup:
            policy_url = self.link_matcher.match(
                website_url, BeautifulSoup(markup, "lxml").find("body")
            )
            return website_url, policy_url

        return website_url, None

