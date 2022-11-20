import logging
import os
import pathlib
import random
from time import sleep as sleep_

from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager

import config
from crawler.web.proxy import Proxy
from tools.exceptions import CaptchaException
from tools.text import parse_proxy


class Driver:

    @classmethod
    def __new__(cls, *args, **kwargs):
        if hasattr(cls, "_instance"):
            return cls._instance
        setattr(cls, "_instance", _DriverInstance(config.webdriver_settings))
        return getattr(cls, "_instance")

    @classmethod
    def close(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            return
        delattr(cls, "_instance")


class _DriverInstance:

    def __init__(self, conf):

        self.config = conf

        self.max_error_attempts = conf["max_error_attempts"]
        self.max_captcha_attempts = conf["max_captcha_attempts"]
        self.max_timeout_attempts = conf["max_timeout_attempts"]

        self.logger = logging.getLogger(f"pid={os.getpid()}")
        self.logger.setLevel(self.config["log_level"])

        self._script_path = pathlib.Path(__file__).parent.resolve()
        self._service_log_path = os.path.join(
            os.path.relpath(self.config["log_path"]))

        self._check_installation()

        try:
            self._profile = webdriver.FirefoxProfile(
                os.path.abspath(self.config['profile_path']))
        except (ValueError, TypeError):
            self.logger.warning("No path for profile is specified")
        except FileNotFoundError:
            self.logger.warning("Wrong path for profile is specified")
        finally:
            self.logger.warning("Using temporary profile")
            self._profile = webdriver.FirefoxProfile()

        if self.config["no_cache"]:
            self._profile.set_preference("browser.cache.disk.enable", False)
            self._profile.set_preference("browser.cache.memory.enable", False)
            self._profile.set_preference("browser.cache.offline.enable", False)
            self._profile.set_preference("network.http.use-cache", False)
            self._profile.set_preference("dom.webdriver.enabled", False)
            self._profile.set_preference("marionette.enabled", False)

        self._profile.set_preference("general.useragent.override",
                                     random.choice(self.config['user_agents']))
        self._profile.set_preference("intl.accept_languages", "en-US, en")
        self._profile.update_preferences()

        self._options = webdriver.FirefoxOptions()
        self._options.add_argument("--no-sandbox")

        if self.config["headless"]:
            self._options.add_argument("--headless")
            self._options.add_argument('--disable-gpu')

        self._capabilities = self._options.to_capabilities()
        self._capabilities["unexpectedAlertBehaviour"] = "accept"

        self._driver = webdriver.Firefox(
            firefox_profile=self._profile,
            firefox_options=self._options,
            executable_path=self._executable_path,
            capabilities=self._capabilities,
            service_log_path=self._service_log_path
        )

        with open(os.path.join(self._script_path, "navigator.js")) as script:
            self._driver.execute_script(script.read())

    def _check_installation(self):
        self.logger.info("Checking installed driver")

        try:
            with open(os.path.relpath(self.config["dotfile"]), "r") as f:
                self._executable_path = f.read()

        except FileNotFoundError:
            self.logger.info("Driver is not found, installing...")
            self._executable_path = GeckoDriverManager().install()
            with open(os.path.relpath(self.config["dotfile"]), "w") as f:
                f.write(self._executable_path)

        self.logger.info(f"Loading driver: {self._executable_path}")

    def get(self, url, cooldown=0, random_cooldown=0, remove_invisible=False):
        if not url:
            raise ValueError("Null url")

        self.logger.info(f"Going to {url}")

        timeout_error = 0
        net_error = 0
        captcha_error = 0
        while True:

            self.sleep(cooldown, random_cooldown)

            if net_error >= self.max_error_attempts \
                    or captcha_error >= self.max_captcha_attempts \
                    or timeout_error >= self.max_timeout_attempts:
                return None

            try:
                self._driver.get(url)

                try:
                    if self._driver.find_element_by_xpath(
                            "//iframe[contains(@src, 'recaptcha')]"):
                        captcha_error += 1
                except WebDriverException:
                    pass

                if remove_invisible:
                    self.remove_invisible()

                return self._driver.page_source

            except TimeoutException:
                self.logger.warning("Slow connection")
                timeout_error += 1

            except WebDriverException:
                self.logger.warning("Web driver exception, potentially net "
                                    "error")
                net_error += 1

            except CaptchaException:
                self.logger.warning("Captcha detected")
                captcha_error += 1

            finally:
                self.change_proxy()
                self.restart_session()
                self.change_useragent()
                self.clear_cookies()

    @classmethod
    def sleep(cls, cooldown, random_cooldown):
        sleep_(cooldown + random.random() * random_cooldown)

    def manage(self):
        return self._driver

    def source(self):
        return self._driver.page_source

    def wait(self, event, timeout=15):
        WebDriverWait(self._driver, timeout).until(event)

    def remove_invisible(self):
        with open(os.path.join(self._script_path, "sanitize.js")) as script:
            self._driver.execute_script(script.read())

    def clear_cookies(self):
        self._driver.delete_all_cookies()

    def change_useragent(self):
        self._profile.set_preference("general.useragent.override",
                                     random.choice(self.config['user_agents']))
        self._profile.update_preferences()

    def restart_session(self):
        self._driver.close()
        self._driver.start_session(capabilities=self._capabilities,
                                   browser_profile=self._profile)

    def change_proxy(self):
        if not self.config["use_proxy"]:
            return

        proxy = Proxy()
        p_str = proxy.get_proxy()
        http, port = parse_proxy(p_str)

        self.logger.info(f"Switching to {p_str} proxy")

        self._profile.set_preference("network.proxy.type", 1)
        self._profile.set_preference("network.proxy.http", http)
        self._profile.set_preference("network.proxy.http_port", port)
        self._profile.set_preference("network.proxy.ssl", http)
        self._profile.set_preference("network.proxy.ssl_port", port)
        self._profile.set_preference("network.proxy.ftp", http)
        self._profile.set_preference("network.proxy.ftp_port", port)
        self._profile.update_preferences()

    def __del__(self):
        if self._driver is None:
            return
        self._driver.quit()
        del self._driver
        self.logger.info("Driver has been closed")
