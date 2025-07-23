import os
import random
import tempfile

from time import sleep
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    WebDriverException, 
    TimeoutException,
    NoSuchElementException, 
    NoAlertPresentException
)

from crawler.web.proxy import Proxy


class Driver:
    _instance = None

    @classmethod
    def __new__(cls, *args, **kwargs):
        from env import config
        if cls._instance is None:
            cls._instance = _DriverInstance(config.webdriver_settings)
        return cls._instance

    @classmethod
    def close(cls):
        if cls._instance:
            cls._instance.quit()
            cls._instance = None

    @classmethod
    def check_installation(cls, conf):
        from tools.functions import get_logger
        logger = get_logger()
        logger.info("Checking installed driver")

        try:
            with open(conf.dotfile, "r") as f:
                executable_path = f.read()
                logger.info(f"Driver found at {executable_path}")

        except FileNotFoundError:
            logger.info("Driver is not found, installing...")
            executable_path = GeckoDriverManager().install()
            with open(conf.dotfile, "w") as f:
                f.write(executable_path)


class _DriverInstance:

    def __init__(self, conf):
        from tools.functions import get_logger
        self.logger = get_logger()
        self.logger.setLevel(conf.log_level)

        self._sanitize = conf.sanitizejs
        self._conf = conf

        tempfile.tempdir = str(conf.temp_dir)
        os.makedirs(conf.temp_dir, exist_ok=True)
        self._driver = self.make_driver(conf)

    def make_driver(self, conf):
        profile = None
        if conf.profile_path:
            self.logger.info(f"Using profile: {conf.profile_path}")
            profile = webdriver.FirefoxProfile(conf.profile_path)
        else:
            self.logger.warning("Wrong path for profile is specified")
            self.logger.warning("Using temporary profile")
            profile = webdriver.FirefoxProfile()

        if conf.no_cache:
            profile.set_preference("browser.cache.disk.enable", False)
            profile.set_preference("browser.cache.memory.enable", False)
            profile.set_preference("browser.cache.offline.enable", False)
            profile.set_preference("network.http.use-cache", False)
            profile.set_preference("dom.webdriver.enabled", False)
            profile.set_preference("marionette.enabled", False)
            
        if conf.use_proxy:
            proxy = Proxy(conf.proxies, conf.proxies_from_conf)
            http, port = proxy.get_proxy()

            self.logger.info(f"Switching to {http}:{port} proxy")

            profile.set_preference("network.proxy.type", 1)
            profile.set_preference("network.proxy.http", http)
            profile.set_preference("network.proxy.http_port", port)
            profile.set_preference("network.proxy.ssl", http)
            profile.set_preference("network.proxy.ssl_port", port)
            profile.set_preference("network.proxy.ftp", http)
            profile.set_preference("network.proxy.ftp_port", port)

        if conf.private:
            profile.set_preference("browser.privatebrowsing.autostart", True)

        profile.set_preference("general.useragent.override", random.choice(conf.user_agents))
        profile.set_preference("intl.accept_languages", "en-US, en")
        profile.update_preferences()

        options = Options()
        options.add_argument("--no-sandbox")
        if conf.headless:
            options.add_argument("--headless")
            options.add_argument('--disable-gpu')
            options.profile = profile

        executable_path = None
        try:
            with open(conf.dotfile, "r") as f:
                executable_path = f.read().strip()
        except FileNotFoundError:
            self.logger.error(f"Dotfile with executable path not found: {conf.dotfile}")
            raise

        service = Service(executable_path=executable_path, log_output=str(conf.log_path))

        driver = webdriver.Firefox(options=options,service=service)
        driver.set_page_load_timeout(conf.page_load_timeout)
        driver.set_script_timeout(conf.page_load_timeout)
        driver.execute_script(conf.navigatorjs)
        return driver

    def get(self, url, cooldown=0, random_cooldown=0, remove_invisible=False):
        from tools.exceptions import CaptchaException

        if not url:
            raise ValueError("Null url")

        self.logger.info(f"Going to {url}")

        network_error, timeout_error, captcha_error = 0, 0, 0
        while network_error < self._conf.max_error_attempts \
                and captcha_error < self._conf.max_captcha_attempts \
                and timeout_error < self._conf.max_timeout_attempts:

            try:
                self.sleep(cooldown, random_cooldown)
                self._driver.get(url)

                try:
                    alert = self._driver.switch_to.alert
                    alert.accept()
                    self.logger.info(f"Alert accepted")
                except NoAlertPresentException:
                    pass

                try:
                    self._driver.find_element(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")
                    captcha_error += 1
                    raise CaptchaException("Captcha iframe detected")
                except NoSuchElementException:
                    pass

                if remove_invisible:
                    self.remove_invisible()

                return

            except TimeoutException:
                self.logger.warning(f"Slow connection, retying {url}")
                self._driver.quit()
                self._driver = self.make_driver(self._conf)
                timeout_error += 1

            except WebDriverException:
                self.logger.warning(f"Web driver exception, potentially net error, retying {url}")
                self._driver.quit()
                self._driver = self.make_driver(self._conf)
                network_error += 1

            except CaptchaException:
                self.logger.warning(f"Captcha detected, retying {url}")
                self._driver.quit()
                self._driver = self.make_driver(self._conf)
                captcha_error += 1

    @classmethod
    def sleep(cls, cooldown, random_cooldown):
        sleep(cooldown + random.random() * random_cooldown)

    def source(self):
        return self._driver.page_source

    def wait(self, event, timeout=5):
        try:
            WebDriverWait(self._driver, timeout).until(event)
            return True
        except TimeoutException:
            self.logger.warning("Wait timeout")
            return False
        
    def find_element(self, *args, **kwargs):
        self._driver.find_element(*args, **kwargs)

    def remove_invisible(self):
        self._driver.execute_script(self._sanitize)

    def quit(self):
        self._driver.quit()
        self._driver = None
        self.logger.info("Driver has been closed")
        