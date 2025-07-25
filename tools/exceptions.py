

class CaptchaException(Exception):
    def __str__(self):
        return f"The website have gave out a captcha"
