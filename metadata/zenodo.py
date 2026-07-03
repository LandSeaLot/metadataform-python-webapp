from datetime import datetime
from config import PUBLISH
import json
import re
import os


def build_zenodo_metadata(parsed_metadata, start_date, end_date):

    with open(os.path.join("resources", "zenodo_config.json"), "r", encoding="utf-8") as f:
        config = json.load(f)
    config["publish"] = PUBLISH

    g = parsed_metadata["global_attributes"]

    def clean(v):
        return str(v).strip() if v is not None else None

    def valid_orcid(o):
        if not o:
            return None
        o = o.strip()
        return o if re.match(r"^\d{4}-\d{4}-\d{4}-[\dX]{4}$", o) else None

    # license
    license_value = clean(g.get("license")) or "CC-BY-4.0"
    if license_value == "CC-BY 4.0":
        license_value = "CC-BY-4.0"

    # creators (no role)
    creators = []
    for c in g.get("creators", []):
        entry = {"name": c.get("name")}

        orcid = valid_orcid(c.get("orcid"))
        if orcid:
            entry["orcid"] = orcid
        
        # wont end up in zenodo, will be ignored
        if c.get("type"):
            entry["type"] = c.get("role")

        creators.append(entry)

    # contributors from fe as contributors
    contributors = []
    for c in g.get("contributors", []):
        entry = {"name": c.get("name")}

        orcid = valid_orcid(c.get("orcid"))
        if orcid:
            entry["orcid"] = orcid

        ctype = c.get("type") or c.get("role") or "Other"
        entry["type"] = ctype

        contributors.append(entry)
    
    # project contributors (from json file)
    for c in config.get("contributors", []):
        entry = {"name": c.get("name")}

        if c.get("affiliation"):
            entry["affiliation"] = c["affiliation"]

        orcid = valid_orcid(c.get("orcid"))
        if orcid:
            entry["orcid"] = orcid

        ctype = c.get("type") or c.get("role") or "Other"
        entry["type"] = ctype

        contributors.append(entry)

    metadata = {
        "upload_type": "dataset",
        "title": clean(g.get("title")),
        "description": clean(g.get("summary")) or clean(g.get("project_statement")),
        "creators": creators,
        "contributors": contributors,
        "access_right": "open",
        "license": license_value,
        "keywords": g.get("keywords").split(","),
        # "publication_date": clean(g.get("data_creation")),
    }
    if g.get("notes"):
        metadata["notes"] = g.get("notes")

    # dates
    dates = []
    start_date = g.get("time_coverage_start")
    end_date = g.get("time_coverage_end")

    if start_date or end_date:

        start = None
        end = None

        if start_date:
            start = (
                datetime.fromisoformat(
                    start_date.replace("Z", "+00:00")
                )
                .date()
                .isoformat()
            )

        if end_date:
            end = (
                datetime.fromisoformat(
                    end_date.replace("Z", "+00:00")
                )
                .date()
                .isoformat()
            )

        dates.append(
            {
                "start": start,
                "end": end,
                "type": "Collected",
            }
        )

    if dates:
        metadata["dates"] = dates

    if config.get("community_identifier"):
        metadata["communities"] = [{"identifier": config["community_identifier"]}]

    # if g.get("project_DOI"):
        # metadata["grants"] = [{"id": clean(g["project_DOI"])}]
    if 'grant_agreement' in config:
        metadata["grants"] = [{"id": config.get("grant_agreement")}]
    
    metadata["prereserve_doi"] = True
    config["prereserve_doi"] = True

    return {"metadata": metadata, "config": config}