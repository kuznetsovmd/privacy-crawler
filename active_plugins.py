from env import config
from crawler.plugins.amazon import Amazon
from crawler.plugins.mail import Mail
from crawler.plugins.rambler import Rambler
from crawler.plugins.walmart import Walmart


analytic_plugins = [

    Rambler(2, config.path.descriptor, cooldown=1., random_cooldown=4.),
    Mail(["Cars"], 1, config.path.descriptor, cooldown=1., random_cooldown=4.)

]


market_plugins = [

    # Walmart(["voice controller", "outdoor camera", "indoor camera",
    #          "tracking device", "tracking sensor", "gps tracking device",
    #          "smart air purifier", "robot vacuum cleaner",
    #          "smart video doorbell", "smart air conditioner",
    #          "smart thermometer", "smart speaker", "smart tv",
    #          "smart light switch", "smart plug", "smart thermostat",
    #          "smart alarm clock", "smart navigation system", "smart bulb",
    #          "smart lock", "smart bracelet", "smart watch", "smart scale"],
    #         1, config.path.descriptor, cooldown=1., random_cooldown=5.),

    Amazon(["voice controller", "outdoor camera", "indoor camera",
            "tracking device", "tracking sensor", "gps tracking device",
            "smart air purifier", "robot vacuum cleaner",
            "smart video doorbell", "smart air conditioner",
            "smart thermometer", "smart speaker", "smart tv",
            "smart light switch", "smart plug", "smart thermostat",
            "smart alarm clock", "smart navigation system", "smart bulb",
            "smart lock", "smart bracelet", "smart watch", "smart scale"],
           1, config.path.descriptor, cooldown=1., random_cooldown=5.),

]
