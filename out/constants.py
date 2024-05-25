
#!/bin/env python
"""
This module contains configuration settings and utility functions for the Claude CLI.
"""

from pathlib import Path
from xdg_base_dirs import xdg_config_home
from typing import Dict, Tuple

# Define type aliases for better readability and maintainability
ConnectionOptions = Dict[str, str]
Address = Tuple[str, int]
Server = Tuple[Address, ConnectionOptions]

# Define paths for configuration and history files
BASE = Path(xdg_config_home(), "codetechnician")
CONFIG_FILE = BASE / "config.yaml"
ENV_VAR_ANTHROPIC = "ANTHROPIC_API_KEY"

VERSION = "0.0.1"

DEFAULT_CONFIG = {
    "supplier": "anthropic",
    "anthropic-api-key": "<INSERT YOUR ANTHROPIC API KEY HERE>",
    "anthropic_api_url": "https://api.anthropic.com",
    "anthropic_model": "claude-3-haiku-20240307",
    "temperature": 1,
    "markdown": True,
    "easy_copy": True,
    "non_interactive": False,
    "json_mode": False,
    "use_proxy": False,
    "proxy": "socks5://127.0.0.1:2080",
}

# ---- Remaining code unchanged. ----
    