from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class PathConfig:
    resources: Path
    data: Path
    html: Path
    explicit: Path
    descriptor: Path


@dataclass
class WebDriversettings:
    temp_dir: Path
    dotfile: str
    log_level: int
    private: bool
    no_cache: bool
    headless: bool
    use_proxy: bool
    page_load_timeout: int
    max_error_attempts: int
    max_captcha_attempts: int
    max_timeout_attempts: int
    sanitizejs: str
    navigatorjs: str
    log_path: Path
    profile_path: str = None
    proxies_from_conf: bool = False
    proxies: list[str] = field(default_factory=list)
    user_agents: list[str] = field(default_factory=list)

@dataclass
class Config:
    path: PathConfig
    sub_proc_count: int
    webdriver_settings: WebDriversettings


def load_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")
