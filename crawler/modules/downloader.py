import json
import logging
import os
from hashlib import md5
from multiprocessing import Pool

from crawler.modules.module import Module
from crawler.product import Product
from crawler.web.driver import Driver
from tools.text import url_to_name


class Downloader(Module):

    def __init__(self, policies_json, explicit_json, downloaded_json,
                 original_policies, cooldown=0., random_cooldown=0.):

        super(Downloader, self).__init__()

        self.policies_json = policies_json
        self.explicit_json = explicit_json
        self.downloaded_json = downloaded_json
        self.original_policies = original_policies
        self.cooldown = cooldown
        self.random_cooldown = random_cooldown

    def run(self, p: Pool = None):
        self.logger.info("Download")

        jobs = filter(None, set(r["policy"] for r in self.records))
        downloaded = p.map(self.get_policy, jobs)

        for item in self.records:
            for policy, policy_path, policy_hash in downloaded:
                if policy == item["policy"]:
                    item["original_policy"] = policy_path
                    item["policy_hash"] = policy_hash

    def bootstrap(self):

        with open(os.path.relpath(self.policies_json), "r") as f:
            self.records.extend(json.load(f))

        with open(os.path.relpath(self.explicit_json), "r") as f:
            explicit = json.load(f)
            Product.counter = len(self.records)
            explicit = [Product(**item) for item in explicit]
            self.records.extend(explicit)

    def finish(self):
        with open(os.path.relpath(self.downloaded_json), "w") as f:
            json.dump(self.records, f, indent=2)

    def get_policy(self, policy_url):
        logger = logging.getLogger(f"pid={os.getpid()}")
        logger.info(f"Getting for policy to {policy_url}")

        Driver().get(policy_url, cooldown=self.cooldown,
                     random_cooldown=self.random_cooldown,
                     remove_invisible=True)
        if markup := Driver().source():
            policy = os.path.relpath(os.path.join(self.original_policies,
                                                  url_to_name(policy_url)))
            with open(policy, "w", encoding="utf-8") as f:
                f.write(markup)
            return policy_url, policy, md5(markup.encode()).hexdigest()

        return policy_url, None, None
