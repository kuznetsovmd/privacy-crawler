from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class PathConfig:
    resources: Path
    data: Path
    html: Path
    explicit: Path
    descriptor: Path
    
    
@dataclass
class WebDriverSettings:
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
    proxies: List[str] = field(default_factory=list)
    user_agents: List[str] = field(default_factory=list)

@dataclass
class Config:
    path: PathConfig
    sub_proc_count: int
    webdriver_settings: WebDriverSettings
    

def load_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")
    