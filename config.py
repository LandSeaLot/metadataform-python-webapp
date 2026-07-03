from datetime import timedelta
from dotenv import load_dotenv
import logging.config
import yaml
import os


load_dotenv()


# ZENODO CONFIGURATION
SANDBOX = True
DEFAULT_ZENODO_TOKEN = os.getenv("ZENODO_TOKEN")
PUBLISH = False

# DATA
DATA_PATH = "data"
MAX_FILES_SIZE = 50 * 1024 * 1024 * 1024 # 50gb
ALLOWED_FILES_EXTENSIONS = {
    "EnvLogger": ["csv"]
}

# CACHE
CACHE_PATH = "cache"
CACHE_FILENAME = "zenodo_records.json"

# METADATA FILES
ZENODO_METADATA_FILENAME = "zenodo_metadata.json"
XML_METADATA_FILENAME = "metadata_iso19115.xml"
TXT_METADATA_FILENAME = "metadata.txt"

# XML generation
# fields not to be inserted as descriptive keywords in the iso19139 xml
SKIP_META_FIELDS = [] 

# ASSETS
USER_MANUAL_FILENAME = "LandSeaLot_Metadata_manual.pdf"
USER_MANUAL_PATH = os.path.join("static", "assets", "LandSeaLot_Metadata_manual.pdf")
LANDSEALOT_LOGO = os.path.join("static", "assets", "LandSeaLot_logo.png")
FAVICON = os.path.join("static", 'assets', 'LOGO_small.png')

# EMAIL
EMAIL_CREDENTIALS = {
    'smtp_server': 'smtp.s4oceandata.eu',
    'smtp_port': 587,
    'email': 'landsealot@s4oceandata.eu',
    'username': 'landsealot@s4oceandata.eu',
    'password': 'clear140Fea$t'
}

EMAIL_RECIPIENTS = [
    "pietro.viglino@dedagroup.it"
]

# ENVLOGGER
ENVLOGGER_IMAGE_PATH = os.path.join("static", "assets", "EnvLogger_data_download_file.png")
MAX_TIMEDELTA = timedelta(minutes=30)

# LOGGING

LOGS_PATH = "logs"
os.makedirs(LOGS_PATH, exist_ok=True)

LOG_CONFIG_PATH = 'log_config.yaml'
with open(LOG_CONFIG_PATH, "r") as f:
    log_config = yaml.safe_load(f)
    logging.config.dictConfig(log_config)


# GLOBAL VARS
SENSORS = {
    "EnvLogger": {},
}

COUNTRIES = [
    "France",
    "Greece",
    "Portugal",
    "Romania",
    "Sweden",
    "The Netherlands",
    "UK",
]

PLATFORM_TYPES = {
"beach/intertidal zone structure": {},
"offshore structure": {},
"coastal structure": {},
"research vessel": {},
"fishing vessel": {},
"river station": {},
"float": {},
"self-propelled boat": {},
"ship": {},
"land or seafloor": {},
"subsurface mooring": {},
"land/onshore structure": {},
"surface vessel": {},
"man-powered boat": {},
"vessel at fixed position": {},
"moored surface buoy": {},
"vessel of opportunity": {},
"fixed subsurface vertical profiler": {},
"vessel of opportunity on fixed route": {},
"mooring": {},
"naval vessel": {},
"Other": {},
}

# datetime version fix
import datetime

if not hasattr(datetime, "UTC"):
    datetime.UTC = datetime.timezone.utc