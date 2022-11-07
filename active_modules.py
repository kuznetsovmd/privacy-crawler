from html_sanitizer import Sanitizer

from config import paths
from config import max_error_attempts
from config import sanitizer_settings
from crawler.modules.converter import Converter
from crawler.modules.efficiency import Efficiency
from crawler.modules.policies import Policies
from crawler.modules.urls import Urls
from crawler.modules.sanitizer import Sanitization
from crawler.modules.downloader import Downloader
from crawler.modules.websites import Websites
from crawler.modules.pack import Pack

# Modules for mining privacy policies in Russian
modules = [

    Urls(),

    Policies(
        paths.json.websites,
        paths.json.policies,
        (r"политика конфиденциальности",
         r"пользовательское соглашение",
         r"политика безопасности",
         r"правовая информация"),
    ),

    Downloader(
        paths.json.policies,
        paths.explicit,
        paths.json.downloaded,
        paths.dir.original
    ),

    Sanitization(
         paths.json.downloaded,
         paths.json.sanitized,
         paths.dir.processed,
         sanitizer_settings=sanitizer_settings
    ),

    Converter(
         paths.json.sanitized,
         paths.json.plain,
         paths.dir.plain
    ),

    Pack(paths.resources, paths.deploy, paths.json.downloaded, paths.json.sanitized, paths.json.plain, paths.archive)

]

# Modules for IoT mining
# modules = [
#
#     Urls(),
#
#     Websites(
#         paths.json.products,
#         paths.json.websites,
#     ),
#
#     Policies(
#         paths.json.websites,
#         paths.json.policies,
#         (r"privacy(policy)?",),
#     ),
#
#     Downloader(
#         paths.json.policies,
#         paths.explicit,
#         paths.json.downloaded,
#         paths.dir.original,
#         max_error_attempts=max_error_attempts
#     ),
#
#     Sanitization(
#          paths.json.downloaded,
#          paths.json.sanitized,
#          paths.dir.processed,
#          sanitizer_settings=sanitizer_settings
#     ),
#
#     Converter(
#          paths.json.sanitized,
#          paths.json.plain,
#          paths.dir.plain
#     ),
#
#     Efficiency(
#          paths.json.plain,
#          paths.metrics
#     ),
#
#     # Pack(),
#
# ]
