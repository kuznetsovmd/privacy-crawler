import logging
import os
import re


class LinkMatcher:
    href = re.compile(r"^((https?://)?(www\.)?([\w.-_]+)\.\w+)?(.*$)")
    http = re.compile("(https?:(//)?)")

    def __init__(self, privacy_links):
        self.logger = logging.getLogger(f"pid={os.getpid()}")

        privacy_links = [pl.replace(" ", ".*") for pl in privacy_links]
        self.regexes = [re.compile(pl) for pl in privacy_links]
        self.templates = [self.template1]

    def match(self, website, soup):
        for t in self.templates:
            if policy_url := t(website, soup):
                return policy_url

    def template1(self, website, soup):
        links = soup.findAll("a")
        try:
            for link in reversed(links):
                if any((reg.match(link.text.lower()) for reg in self.regexes)):
                    if ref := self.href.match(link.get("href")):
                        return f"http://{self.http.sub('', website)}" \
                               f"{ref.group(5)}"

        except (AttributeError, TypeError):
            self.logger.error("Policy is not found")
