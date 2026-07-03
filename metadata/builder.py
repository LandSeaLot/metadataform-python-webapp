from datetime import datetime, timezone
import json
from pathlib import Path

RESOURCES_DIR = Path(__file__).parent.parent / "resources"


def load_json(filename):
    with open(RESOURCES_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def build_creators(default_creators, extra_creators=None):
    creators = list(default_creators or [])

    if extra_creators:
        creators.extend(extra_creators)

    return creators


def build_metadata(
    country,
    marinas,
    sensor_id,
    start_date,
    end_date,
    user_metadata,
    sampling_resolution,
    custom_name,
):
    global_project = load_json("global_project_metadata.json")
    envlogger_global = load_json("envlogger_global.json")
    variables_metadata = load_json("variables_metadata.json")
    lil_config = load_json("lil_config.json")
    platforms = load_json("platforms.json")

    if marinas is None:
        marinas = "null"
    lil_key = f"{country}|{marinas}"

    if lil_key not in lil_config:
        raise ValueError(f"No LIL configuration found for '{lil_key}'")

    lil = lil_config[lil_key]

    global_attributes = {}

    # Base metadata
    global_attributes.update(global_project)
    global_attributes.update(envlogger_global)

    # sampling resolution
    if sampling_resolution:
        global_attributes["sampling_resolution"] = sampling_resolution
    # sensor_custom_name
    if custom_name:
        global_attributes["sensor_custom_name"] = custom_name
    
    if sensor_id:
        global_attributes["sensor_serial_number"] = sensor_id

    global_attributes["data_owner_marinas"] = marinas if marinas else "No"

    global_attributes["user_type"] = user_metadata.get("user_type")
    if user_metadata.get("user_type") == "Citizen":
        global_attributes["platform_type_sdn_name"] = "human"
        global_attributes["platform_type_sdn_uri"] = "SDN:L06::71"
        global_attributes["platform_type_sdn_urn"] = "https://vocab.nerc.ac.uk/collection/L06/current/71/"

    # LIL metadata
    global_attributes["research_infrastructure"] = lil["research_infrastructure"]
    global_attributes["data_owner"] = lil["data_owner"]
    global_attributes["data_owner_country"] = country
    global_attributes["data_owner_country_code"] = lil.get("country_code")
    global_attributes["data_owner_edmo_code"] = lil.get("edmo_code")
    global_attributes["data_owner_edmo_uri"] = lil.get("edmo_uri")
    global_attributes["data_owner_ror_code"] = lil.get("ror_code")
    global_attributes["data_owner_ror_uri"] = lil.get("ror_uri")

    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    global_attributes["data_creation"] = now
    global_attributes["data_update"] = now

    global_attributes["sensor_landsealot_id"] = (
        f"landsealot_" f"{lil['short_code']}_envlogger_" f"{sensor_id.replace(' ', '')}"
    )

    global_attributes["time_coverage_start"] = start_date
    global_attributes["time_coverage_end"] = end_date

    if start_date:
        global_attributes["title"] = (
            f"LIL {lil['research_infrastructure']} "
            f"- EnvLogger sensor "
            f"- Temperature data "
            f"(sensor id: {sensor_id}) "
            f"- {start_date}"
        )
    else:
        global_attributes["title"] = (
            f"LIL {lil['research_infrastructure']} "
            f"- EnvLogger sensor "
            f"- Temperature data "
            f"(sensor id: {sensor_id}) "
        )

    # User metadata
    if user_metadata.get("summary"):
        if (
            not user_metadata["summary"].endswith(".")
            or not user_metadata["summary"].endswith("!")
            or not user_metadata["summary"].endswith("?")
            or not user_metadata["summary"].endswith(";")
            or not user_metadata["summary"].endswith('"')
            or not user_metadata["summary"].endswith("'")
        ):
            user_metadata["summary"] += "."

    global_attributes["summary"] = (
        user_metadata.get("summary")
        + "<br> This dataset is part of the LandSeaLot project outcomes.<br> "
        + global_project.get("project_statement", "")
    )

    global_attributes["notes"] = user_metadata.get("notes")
    global_attributes["geospatial_deployment"] = user_metadata.get("spatial_deployment")

    # Spatial metadata
    if user_metadata.get("spatial_deployment") == "Fixed location":

        lat = user_metadata.get("latitude")
        lon = user_metadata.get("longitude")

        global_attributes["geospatial_lat_min"] = lat
        global_attributes["geospatial_lat_max"] = lat

        global_attributes["geospatial_lon_min"] = lon
        global_attributes["geospatial_lon_max"] = lon

    else:
        global_attributes["geospatial_lat_min"] = user_metadata.get("min_lat")
        global_attributes["geospatial_lat_max"] = user_metadata.get("max_lat")
        global_attributes["geospatial_lon_min"] = user_metadata.get("min_lon")
        global_attributes["geospatial_lon_max"] = user_metadata.get("max_lon")

    global_attributes["geospatial_lat_units"] = "degrees_north"
    global_attributes["geospatial_lon_units"] = "degrees_east"

    # Depth metadata
    global_attributes["geospatial_vertical_type"] = user_metadata.get("depth_mode")
    global_attributes["geospatial_vertical_positive"] = "down"
    global_attributes["geospatial_vertical_units"] = "meters"

    if user_metadata.get("depth_mode") == "One fixed depth":
        depth = user_metadata.get("depth_value")

        global_attributes["geospatial_vertical_min"] = depth
        global_attributes["geospatial_vertical_max"] = depth

    else:
        global_attributes["geospatial_vertical_min"] = user_metadata.get("min_depth")
        global_attributes["geospatial_vertical_max"] = user_metadata.get("max_depth")

    # Creators
    creators = []

    creator = user_metadata.get(
        "creator",
        {},
    )

    if creator.get("name") and creator.get("surname"):
        creators.append(
            {
                "name": (f"{creator['surname']}, " f"{creator['name']}"),
                "orcid": creator.get(
                    "orcid",
                    "",
                ),
                # "type": "DataCollector",
                "role": "DataCollector",
            }
        )

    # lil creators
    if user_metadata.get("user_type") != "Scientist":
        for dc in lil.get("default_creators", []):
            dc_name = dc.get("name")
            dc_orcid = dc.get("orcid")
            dc_role = dc.get("role")
            if dc_name not in [c.get("name", "") for c in creators]:
                creators.append({"name": dc_name, "orcid": dc_orcid, "role": dc_role})

    # contributors
    contributors = []

    for contributor in user_metadata.get(
        "contributors",
        [],
    ):

        if contributor.get("name") and contributor.get("surname"):
            contributors.append(
                {
                    "name": (f"{contributor['surname']}, " f"{contributor['name']}"),
                    "orcid": contributor.get(
                        "orcid",
                        "",
                    ),
                    # "type": "DataCollector",
                    "role": "DataCollector",
                }
            )

    global_attributes["creators"] = creators

    if contributors:
        global_attributes["contributors"] = contributors

    # Platform metadata
    platform_name = user_metadata.get("platform_type")

    if platform_name:
        platform_meta = platforms.get(platform_name)

        if platform_meta:
            global_attributes.update(platform_meta)

    global_attributes["platform_id_orig"] = user_metadata.get("platform_id_orig")
    global_attributes["ship_name"] = user_metadata.get("ship_name")
    global_attributes["ship_call_sign"] = user_metadata.get("ship_call_sign")
    global_attributes["ship_imo"] = user_metadata.get("ship_imo")

    return {"global_attributes": global_attributes, "variables": variables_metadata}
