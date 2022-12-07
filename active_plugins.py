from config import paths
from crawler.plugins.amazon import Amazon
from crawler.plugins.mail_top import MailTop
from crawler.plugins.rambler_top import RamblerTop

# Plugins for mining privacy policies in Russian
plugins = [

#     MailTop(["Cars", "World", "State", "Business", "House", "Internet",
#              "Job", "Computers", "Culture", "Science", "Mysterious", "Rest",
#              "Industry", "MassMedia", "Sport", "References", "Humor",
#              "WapSites"], paths.json.websites, cooldown=0., random_cooldown=0.)

    RamblerTop(paths.json.websites, 2080, cooldown=4., random_cooldown=4.)

]

# Plugins for mining IoT privacy policies
# plugins = [
#
#     Walmart(["voice controller", "outdoor camera", "indoor camera",
#              "tracking device", "tracking sensor", "gps tracking device",
#              "smart air purifier", "robot vacuum cleaner",
#              "smart video doorbell", "smart air conditioner",
#              "smart thermometer", "smart speaker", "smart tv",
#              "smart light switch", "smart plug", "smart thermostat",
#              "smart alarm clock", "smart navigation system", "smart bulb",
#              "smart lock", "smart bracelet", "smart watch", "smart scale"],
#             50, paths.json.products,
#             cooldown=2., random_cooldown=2.),
#
#     Amazon(["voice controller", "outdoor camera", "indoor camera",
#             "tracking device", "tracking sensor", "gps tracking device",
#             "smart air purifier", "robot vacuum cleaner",
#             "smart video doorbell", "smart air conditioner",
#             "smart thermometer", "smart speaker", "smart tv",
#             "smart light switch", "smart plug", "smart thermostat",
#             "smart alarm clock", "smart navigation system", "smart bulb",
#             "smart lock", "smart bracelet", "smart watch", "smart scale"],
#            50, paths.json.products,
#            cooldown=2., random_cooldown=2.),
#
# ]
