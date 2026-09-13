import os
from dotenv import load_dotenv
load_dotenv()

USE_FAKES = os.getenv("USE_FAKES", "1") == "1"
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"
FAST_MODEL = os.getenv("FAST_MODEL", "claude-haiku-4-5-20251001")
SMART_MODEL = os.getenv("SMART_MODEL", "claude-sonnet-4-6")
CRM_PROVIDER = os.getenv("CRM_PROVIDER", "hubspot")
DB_PATH = os.getenv("DB_PATH", "agent.db")
MAX_STEPS = 12
CRITIC_THRESHOLD = 0.7
