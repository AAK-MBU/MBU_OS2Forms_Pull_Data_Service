"""
Stores configuration settings for the service.
"""

import os

# Fetch interval in seconds (e.g., 5 minutes)
FETCH_INTERVAL = 300

# Heartbeat interval in seconds (e.g., 1 minute)
HEARTBEAT_INTERVAL = 60
SERVICE_CHECK_INTERVAL = 60

# Base API URL
BASE_API_URL = "https://selvbetjening.aarhuskommune.dk/da"

# API Key
API_KEY = f"{os.getenv('Os2ApiKey')}"
