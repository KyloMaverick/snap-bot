"""
SNAP v1.0 - Configuration Settings
"""

import os

# ============ BOT MODE ============
# Options: "PAPER", "DRY_RUN", "LIVE"
BOT_MODE = "PAPER"

# ============ MODAL & RISK ============
INITIAL_BALANCE = 20.0
MAX_DAILY_LOSS_PCT = -6.0
MAX_CONSECUTIVE_LOSSES = 3
MAX_OPEN_POSITIONS = 2

# ============ TRADE PARAMETERS ============
DEFAULT_EDGE_THRESHOLD = 3.0

POSITION_SIZE = {
    "HIGH": 0.25,
    "MEDIUM": 0.15,
    "LOW": 0.10,
}

MODE_MULTIPLIER = {
    "SAFE": 0.7,
    "AGGRESSIVE": 1.0,
}

# ============ EXIT RULES ============
TAKE_PROFIT_PCT = 3.0
STOP_LOSS_PCT = -3.0
MAX_HOLD_HOURS = 48
SLOW_PROFIT_HOURS = 12

# ============ SCAN & FILTERING ============
SCAN_INTERVAL = 2
MIN_VOLUME = 10000
MIN_LIQUIDITY = 500
MAX_SPREAD_PCT = 2.0

# ============ API ENDPOINTS ============
POLYMARKET_GAMMA_API = "https://gamma-api.polymarket.com"
POLYMARKET_CLOB_API = "https://clob.polymarket.com"

# ============ LEARNING PARAMETERS ============
MIN_THRESHOLD = 2.5
MAX_THRESHOLD = 5.5
LEARNING_UPDATE_INTERVAL = 21600

# ============ LOGGING ============
LOG_LEVEL = "INFO"
LOG_FILE = "logs/snap_bot.log"