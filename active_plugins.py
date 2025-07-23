from env import config
from crawler.plugins.amazon import Amazon
from crawler.plugins.mail import Mail
from crawler.plugins.rambler import Rambler
from crawler.plugins.walmart import Walmart


analytics_plugins = [

    Rambler(2, config.path.descriptor, cooldown=3., random_cooldown=3.),
    Mail(["Cars"], 1, config.path.descriptor, cooldown=3., random_cooldown=3.)

]


marketing_plugins = [

    Walmart(["voice controller", "outdoor camera", ],
            1, config.path.descriptor, cooldown=2., random_cooldown=2.),

    Amazon(["voice controller", "outdoor camera", ],
           1, config.path.descriptor, cooldown=2., random_cooldown=2.),

    # Walmart(["voice controller", "outdoor camera", "indoor camera",
    #          "tracking device", "tracking sensor", "gps tracking device",
    #          "smart air purifier", "robot vacuum cleaner",
    #          "smart video doorbell", "smart air conditioner",
    #          "smart thermometer", "smart speaker", "smart tv",
    #          "smart light switch", "smart plug", "smart thermostat",
    #          "smart alarm clock", "smart navigation system", "smart bulb",
    #          "smart lock", "smart bracelet", "smart watch", "smart scale"],
    #         50, config.path.descriptor, cooldown=2., random_cooldown=2.),

    # Amazon(["voice controller", "outdoor camera", "indoor camera",
    #         "tracking device", "tracking sensor", "gps tracking device",
    #         "smart air purifier", "robot vacuum cleaner",
    #         "smart video doorbell", "smart air conditioner",
    #         "smart thermometer", "smart speaker", "smart tv",
    #         "smart light switch", "smart plug", "smart thermostat",
    #         "smart alarm clock", "smart navigation system", "smart bulb",
    #         "smart lock", "smart bracelet", "smart watch", "smart scale"],
    #        50, config.path.descriptor, cooldown=2., random_cooldown=2.),

]
