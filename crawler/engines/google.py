import logging
import os
import random
import re
from time import sleep

from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec

from crawler.engines.engine import Engine
from crawler.web.driver import Driver
from tools.exceptions import CaptchaException
from tools.text import similarity


class GoogleEngine(Engine):

    def __init__(self, sim=.6, delay=0., random_delay=0.,
                 max_error_attempts=0, max_captcha_attempts=0, max_timeout_attempts=0):
        self.href = re.compile(r"^((https?://)?(www\.)?([\w.\-_]+)(\.\w+)).*$")
        self.request = re.compile(r"([^\w ]+)|(\s{2,})")
        self.captcha = re.compile(r"captcha", flags=re.IGNORECASE)

        self.similarity = sim
        self.static_delay = delay
        self.random_delay = random_delay
        self.max_error_attempts = max_error_attempts
        self.max_captcha_attempts = max_captcha_attempts
        self.max_timeout_attempts = max_timeout_attempts

        self.logger = logging.getLogger(f"pid={os.getpid()}")

    def search(self, manufacturer, keyword):

        net_error = 0
        captcha_error = 0
        driver_error = 0

        results = None
        while True:

            driver = Driver()
            driver.change_proxy()
            driver.change_useragent()
            driver.restart_session()
            driver.clear_cookies()

            try:
                results = self.results(manufacturer, keyword)
                break

            except TimeoutException:
                self.logger.warning("Slow connection")
                net_error += 1
                if net_error > self.max_timeout_attempts:
                    break

            except CaptchaException:
                self.logger.warning("Google knows that this is automation script")
                captcha_error += 1
                if net_error > self.max_captcha_attempts:
                    break

            except WebDriverException:
                self.logger.warning(f"Web driver exception, potentially net error")
                driver_error += 1
                if net_error > self.max_error_attempts:
                    break

        return results

    def results(self, manufacturer, keyword):
        driver = Driver()

        sleep(self.static_delay + random.random() * self.random_delay)
        driver.get(f"https://www.google.com")
        sleep(self.static_delay + random.random() * self.random_delay)

        search = driver.manage().find_element_by_name("q")
        search.send_keys(f"{manufacturer} {keyword}")
        search.send_keys(Keys.RETURN)

        driver.wait(ec.presence_of_element_located((By.TAG_NAME, "cite")))

        if self.captcha.search(driver.source()) is not None:
            raise CaptchaException()

        soup = BeautifulSoup(driver.source(), "lxml")

        return self.similarity_filter(manufacturer, soup, threshold=self.similarity)

    def similarity_filter(self, content, soup, threshold=.6):
        best_url = None
        best_similarity = threshold

        for c in soup.findAll("cite"):
            m = self.href.match(c.text)
            if m is None:
                break

            content_list = self.request.sub(" ", content).split()
            if len(content_list) > 1:
                content_list.append("".join(content_list))

            domain = m.group(4)
            for piece in content_list:
                sim = similarity(piece, domain)

                if sim > best_similarity or domain in piece:

                    w3 = m.group(3)
                    if w3 is None:
                        w3 = ""

                    best_url = f"http://{w3}{m.group(4)}{m.group(5)}"
                    best_similarity = sim

        return best_url
