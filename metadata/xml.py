from pygeometa.schemas.iso19139_2 import ISO19139_2OutputSchema
from pygeometa.core import read_mcf
from config import *
import datetime


def clean_text(text):
    if not text:
        return ""

    return (
        str(text)
        .replace("<br />", "\n")
        .replace("<br/>", "\n")
        .replace("<br>", "\n")
        .strip()
    )


def build_spatial_extent(ga):
    required = (
        "geospatial_lon_min",
        "geospatial_lat_min",
        "geospatial_lon_max",
        "geospatial_lat_max",
    )

    if not all(
        ga.get(field)
        not in (
            None,
            "",
        )
        for field in required
    ):
        return [{"bbox": []}]

    return [
        {
            "bbox": [
                ga["geospatial_lon_min"],
                ga["geospatial_lat_min"],
                ga["geospatial_lon_max"],
                ga["geospatial_lat_max"],
            ],
            "crs": 4326,
        }
    ]


def build_temporal_extent(ga):
    start = ga.get("time_coverage_start")

    if not start:
        return []

    temporal = {
        "begin": start,
    }

    end = ga.get("time_coverage_end")

    if end:
        temporal["end"] = end

    return [temporal]


def build_keywords(ga):
    keywords = ga.get(
        "keywords",
        [],
    )

    if isinstance(
        keywords,
        str,
    ):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]

    return {"default": {"keywords": {"en": keywords}}}


def build_acquisition(ga):
    platform = ga.get("platform_type_sdn_name")

    if not platform:
        return {}

    return {
        "platforms": [
            {
                "identifier": (
                    ga.get("platform_id_orig") or ga.get("sensor_landsealot_id") or ""
                ),
                "description": platform,
                "instruments": [
                    {
                        "identifier": ga.get(
                            "sensor_landsealot_id",
                            "",
                        ),
                        "type": ga.get(
                            "sensor_sdn_name",
                            "",
                        ),
                    }
                ],
            }
        ]
    }


def build_content_info(
    variables,
):

    return {
        "type": "dataset",
        "attributes": [
            {
                "name": name,
                "title": variable.get(
                    "parameter_sdn_name",
                    "",
                ),
                "type": ("number" if variable.get("units") else "string"),
                "units": variable.get(
                    "units",
                    "",
                ),
                "url": variable.get(
                    "parameter_sdn_uri",
                    "",
                ),
            }
            for name, variable in variables.items()
        ],
    }


def build_main_mcf(
    mcf,
    parsed_metadata,
    used_fields,
):
    ga = parsed_metadata.get(
        "global_attributes",
        {},
    )

    variables = parsed_metadata.get(
        "variables",
        {},
    )

    now = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    used_fields.update(
        {
            "sensor_landsealot_id",
            "sensor_id",
            "title",
            "summary",
            "description",
            "data_version",
            "data_creation",
            "license",
            "license_url",
            "data_owner",
            "infoUrl",
            "time_coverage_start",
            "time_coverage_end",
            "geospatial_lat_min",
            "geospatial_lat_max",
            "geospatial_lon_min",
            "geospatial_lon_max",
            "geospatial_vertical_min",
            "geospatial_vertical_max",
            "variables",
        }
    )

    # MCF
    mcf["mcf"] = {
        "version": "1.0",
    }

    mcf["metadata"] = {
        "identifier": (
            ga.get("sensor_landsealot_id")
            or ga.get("sensor_id")
            or "dataset"
        ),
        "charset": "utf8",
        "hierarchylevel": "dataset",
        "datestamp": now,
    }

    mcf["spatial"] = {
        "datatype": "vector",
        "geomtype": "point",
    }

    mcf["identification"] = {
        "title": ga.get(
            "title",
            "no title",
        ),
        "abstract": clean_text(
                ga.get("summary") or ga.get("description")
            ),
        "edition": str(
            ga.get(
                "data_version",
                "1",
            )
        ),
        "dates": {
            "creation": ga.get(
                "data_creation",
                now,
            ),
            "publication": now,
        },
        "keywords": build_keywords(
            ga,
        ),
        "extents": {
            "spatial": build_spatial_extent(
                ga,
            ),
            "temporal": build_temporal_extent(
                ga,
            ),
        },
        "license": {
            "name": ga.get(
                "license",
                "",
            ),
            "url": ga.get(
                "license_url",
                "",
            ),
        },
        "rights": {
            "en": ga.get(
                "data_owner",
                "",
            )
        },
        "url": ga.get(
            "infoUrl",
            "",
        ),
    }

    mcf["content_info"] = build_content_info(
        variables,
    )

    mcf["acquisition"] = build_acquisition(
        ga,
    )

    mcf["distribution"] = {}

    mcf["dataquality"] = {}


# new simpler version
# def build_contacts(
#     mcf,
#     parsed_metadata,
#     used_fields,
# ):
#     ga = parsed_metadata.get(
#         "global_attributes",
#         {},
#     )
# 
#     contacts = {}
# 
#     # ------------------------------------------------------------------
#     # Dataset owner
#     # ------------------------------------------------------------------
# 
#     if ga.get("data_owner"):
#         contacts["owner"] = {
#             "organization": ga.get("data_owner"),
#             "country": ga.get("data_owner_country"),
#             "url": ga.get("data_owner_ror_uri"),
#         }
# 
#         used_fields.update({
#             "data_owner",
#             "data_owner_country",
#             "data_owner_country_code",
#             "data_owner_edmo_code",
#             "data_owner_edmo_uri",
#             "data_owner_ror_code",
#             "data_owner_ror_uri",
#         })
# 
#     # ------------------------------------------------------------------
#     # Data curator
#     # ------------------------------------------------------------------
# 
#     if ga.get("data_curator"):
#         contacts["custodian"] = {
#             "organization": ga.get("data_curator"),
#             "url": ga.get("data_curator_ror_uri"),
#         }
# 
#         used_fields.update({
#             "data_curator",
#             "data_curator_edmo_code",
#             "data_curator_edmo_uri",
#             "data_curator_ror_code",
#             "data_curator_ror_uri",
#         })
# 
#     # ------------------------------------------------------------------
#     # Distributor
#     # ------------------------------------------------------------------
# 
#     if ga.get("distributor_name"):
#         contacts["distributor"] = {
#             "organization": ga.get("distributor_name"),
#             "url": ga.get("distributor_url"),
#         }
# 
#         used_fields.update({
#             "distributor_name",
#             "distributor_url",
#         })
# 
#     mcf["contact"] = contacts


def build_contacts(
    mcf,
    parsed_metadata,
    used_fields,
):
    ga = parsed_metadata.get(
        "global_attributes",
        {},
    )

    contacts = {}

    # Data owner

    if ga.get("data_owner"):
        contacts["owner"] = {
            "organization": ga.get("data_owner"),
            "country": ga.get("data_owner_country"),
            "url": ga.get("data_owner_ror_uri"),
        }

        used_fields.update(
            {
                "data_owner",
                "data_owner_country",
                "data_owner_country_code",
                "data_owner_edmo_code",
                "data_owner_edmo_uri",
                "data_owner_ror_code",
                "data_owner_ror_uri",
            }
        )

    # Distributor

    if ga.get("distributor_name"):
        contacts["distributor"] = {
            "organization": ga.get("distributor_name"),
            "url": ga.get("distributor_url"),
        }

        used_fields.update(
            {
                "distributor_name",
                "distributor_url",
            }
        )

    # Data curator

    if ga.get("data_curator"):
        contacts["custodian"] = {
            "organization": ga.get("data_curator"),
            "url": ga.get("data_curator_ror_uri"),
        }

        used_fields.update(
            {
                "data_curator",
                "data_curator_edmo_code",
                "data_curator_edmo_uri",
                "data_curator_ror_code",
                "data_curator_ror_uri",
            }
        )

    # Creators
    creators = ga.get(
        "creators",
        [],
    )

    if creators:

        creator = creators[0]

        contacts["creator"] = {
            "individualname": creator.get("name"),
        }

        used_fields.add("creators")

    # Contributors
    contributors = ga.get(
        "contributors",
        [],
    )

    if contributors:

        contributor = contributors[0]

        contacts["contributor"] = {
            "individualname": contributor.get("name"),
        }

        used_fields.add("contributors")

    mcf["contact"] = contacts


def add_remaining_keywords(
    mcf,
    parsed_metadata,
    used_fields,
):
    ga = parsed_metadata.get(
        "global_attributes",
        {},
    )

    keywords = mcf.setdefault(
        "identification",
        {},
    ).setdefault(
        "keywords",
        {},
    )

    for key, value in ga.items():

        if key in used_fields:
            continue

        if key in SKIP_META_FIELDS:
            continue

        keyword_values = _keyword_values(value)

        if not keyword_values:
            continue

        keywords[key] = {
            "keywords": keyword_values,
            "keywords_type": "theme",
            "vocabulary": {
                "name": _format_keyword_key(key),
            },
        }


def _format_keyword_key(key):
    return (
        str(key)
        .replace("_", " ")
        .strip()
        .capitalize()
    )


def _keyword_values(value):

    if value is None:
        return []

    if isinstance(value, str):
        value = value.strip()

        if not value or value.lower() == "null":
            return []

        return [value]

    if isinstance(value, (int, float, bool)):
        return [str(value)]

    if isinstance(value, list):

        values = []

        for item in value:

            if isinstance(item, dict):
                values.extend(
                    [
                        str(v).strip()
                        for v in item.values()
                        if v not in (
                            None,
                            "",
                            "null",
                        )
                    ]
                )

            elif item is not None:
                values.append(str(item))

        return values

    if isinstance(value, dict):

        return [
            str(v).strip()
            for v in value.values()
            if v not in (
                None,
                "",
                "null",
            )
        ]

    return [str(value)]


def generate_xml(parsed_metadata):
    mcf = {}
    used_fields = set()

    build_main_mcf(
        mcf,
        parsed_metadata,
        used_fields,
    )

    build_contacts(
        mcf,
        parsed_metadata,
        used_fields,
    )

    add_remaining_keywords(
        mcf,
        parsed_metadata,
        used_fields,
    )

    mcf = read_mcf(mcf)

    schema = ISO19139_2OutputSchema()

    return schema.write(mcf)


def save_xml(
    parsed_metadata,
    output_path,
):
    xml = generate_xml(parsed_metadata)

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as f:
        f.write(xml)

    return output_path