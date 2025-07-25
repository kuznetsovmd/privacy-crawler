from env import config
from active_engines import engines
from crawler.modules.websites import Websites
from crawler.modules.downloader import Downloader
from crawler.modules.policies import Policies
from crawler.modules.urls import Urls
from crawler.product import Product
from crawler.website import Website
from tools.link_matcher import LinkMatcher
from active_plugins import analytic_plugins, market_plugins


analytic_modules = [

    Urls(analytic_plugins),

    Policies(
        Website,
        config.path.descriptor,
        LinkMatcher((r"политика конфиденциальности",
                     r"пользовательское соглашение",
                     r"политика безопасности",
                     r"правовая информация",
                     r"конфиденциальность",
                     r"условия обработки персональных данных",
                     r"правовая информация")),
    ),

    Downloader(
        Website,
        config.path.descriptor,
        config.path.explicit,
        config.path.html,
    )

]


market_modules = [

    Urls(market_plugins),

    Websites(
        config.path.descriptor,
        engines,
    ),

    Policies(
        Product,
        config.path.descriptor,
        LinkMatcher((r"privacy policy",)),
    ),

    Downloader(
        Product,
        config.path.descriptor,
        config.path.explicit,
        config.path.html,
    )

]


active_modules = analytic_modules
