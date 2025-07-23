from env import config
from crawler.modules.downloader import Downloader
from crawler.modules.policies import Policies
from crawler.modules.urls import Urls
from crawler.website import Website
from tools.link_matcher import LinkMatcher
from active_plugins import analytics_plugins, marketing_plugins


modules = [

    Urls(analytics_plugins),

    Policies(
        Website,
        config.path.descriptor,
        LinkMatcher((r"политика конфиденциальности",
                     r"пользовательское соглашение",
                     r"политика безопасности",
                     r"правовая информация",
                     r"конфиденциальность",
                     r"условия обработки персональных данных",
                     r"правовая информация",
                     r"privacy policy")),
    ),

    Downloader(
        Website,
        config.path.descriptor,
        config.path.explicit,
        config.path.html,
    )

]
