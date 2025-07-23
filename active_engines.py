from crawler.engines.google import GoogleEngine


engines = [

    GoogleEngine(similarity_threshold=.7, cooldown=2., random_cooldown=2.)

]
