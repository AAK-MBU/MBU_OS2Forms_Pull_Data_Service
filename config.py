"""
Stores configuration settings for the service.
"""

import os

# Fetch interval in seconds
FETCH_INTERVAL = 300
SERVICE_CHECK_INTERVAL = 60

# Heartbeat interval in seconds
HEARTBEAT_INTERVAL = 60

# Base API URL
BASE_API_URL = "https://selvbetjening.aarhuskommune.dk/da"

# API Key
API_KEY = f"{os.getenv('Os2ApiKey')}"
