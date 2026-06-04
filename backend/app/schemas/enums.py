from __future__ import annotations

from enum import Enum


class ProjectType(str, Enum):
    web_app = "web_app"
    mobile_app = "mobile_app"
    chrome_extension = "chrome_extension"


class Stage(str, Enum):
    mvp = "mvp"
    production = "production"


class ExpectedUsers(str, Enum):
    u100 = "100"
    u1000 = "1000"
    u10000 = "10000"
    u100000 = "100000+"
