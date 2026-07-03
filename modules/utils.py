from datetime import datetime, timezone
from config import *
import pandas as pd
import logging
import base64
import shutil
import json
import os


logger = logging.getLogger("landsealot_form")


def img_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def validate_float(value):
    try:
        if "," in str(value):
            value = str(value).replace(",", ".")
        value = float(value)
        return value
    except Exception as e:
        return None


# def get_lil_metadata(country, marinas, sensor_serial, start_date):
#     with open(os.path.join('resources', 'lil_config.json'), 'r', encoding='utf-8') as f:
#         LIL_CONFIG = json.load(f)
# 
#     if marinas is None:
#         marinas = "null"
#     cfg = LIL_CONFIG[f"{country}|{marinas}"]
# 
#     return {
#         "research_infrastructure": cfg["research_infrastructure"],
#         "data_owner": cfg["data_owner"],
#         "data_owner_country": country,
#         "data_owner_country_code": cfg["country_code"],
#         "data_owner_edmo_code": cfg["edmo_code"],
#         "data_owner_edmo_uri": cfg["edmo_uri"],
#         "data_owner_ror_code": cfg["ror_code"],
#         "data_owner_ror_uri": cfg["ror_uri"],
#         "sensor_landsealot_id":
#             f"landsealot_{cfg['short_code']}_envlogger_{sensor_serial.replace(' ', '')}",
#         "title":
#             f"LIL {cfg['research_infrastructure']} - EnvLogger sensor - "
#             f"Temperature data (sensor id: {sensor_serial}) - {start_date}",
#     }


# def get_start_date(sensor_dir):
#     min_dt = None
# 
#     for file in os.listdir(sensor_dir):

#         if not file.startswith("processed_"):
#             continue
# 
#         df = pd.read_csv(os.path.join(sensor_dir, file))
# 
#         current_min = pd.to_datetime(df["time"], utc=True).min()
# 
#         if min_dt is None or current_min < min_dt:
#             min_dt = current_min
# 
#     return min_dt.strftime("%Y-%m-%dT%H:%M:%SZ")