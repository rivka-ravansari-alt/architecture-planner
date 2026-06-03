"""Fixed project types shown in the wizard."""

from __future__ import annotations

PROJECT_TYPES: list[dict[str, str]] = [
    {
        "type": "web_app",
        "label": "Web App",
        "description": "Browser-based application accessed over the web.",
    },
    {
        "type": "mobile_app",
        "label": "Mobile App",
        "description": "Native or cross-platform app installed on a device.",
    },
    {
        "type": "chrome_extension",
        "label": "Chrome Extension",
        "description": "Browser extension running inside Chrome.",
    },
]
