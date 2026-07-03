from modules.utils import validate_float
import re


def valid_orcid(o):
    if not o:
        return True
    o = o.strip()
    return o if re.match(r"^\d{4}-\d{4}-\d{4}-[\dX]{4}$", o) else False


def validate_inputs(
        user_type,
        creator_surname,
        creator_name,
        orcid,
        associated_with_data,
        contributors_enabled,
        contributors,
        summary,
        data_owner_country,
        uploaded_file,
        marinas,
        spatial_deployment,
        external_gps,
        uploaded_gpx_file,
        latitude,
        longitude,
        min_lat,
        min_lon,
        max_lat,
        max_lon,
        depth_mode,
        depth_value,
        min_depth,
        max_depth,
        platform_type,
        plat_type_sdn_name,
        ship_name,
        ship_imo
):
    errors = []
    if not user_type:
        errors.append("Please specify what kind of user are you.")

    if (user_type == "Scientist" and not creator_surname.strip()) or (user_type == "Citizen" and associated_with_data == "Yes" and not creator_surname.strip()):
        errors.append("Surname is required.")
    
    if (user_type == "Scientist" and not creator_name.strip()) or (user_type == "Citizen" and associated_with_data == "Yes" and not creator_name.strip()):
        errors.append("Name is required.")

    if (user_type == "Citizen" and associated_with_data == "Yes" and not contributors_enabled) or (user_type =="Scientist" and not contributors_enabled):
        errors.append("Please specify if there are contributors.")

    if orcid and not valid_orcid(orcid):
        errors.append(f"ORCID {orcid} doesn't match the format xxxx-xxxx-xxxx-xxxx")

    if contributors:
        for cid, contrib in contributors.items():
            contrib_orcid = contrib.get("orcid", "").strip()

            if contrib_orcid and not valid_orcid(contrib_orcid):
                errors.append(
                    f"Contributor ORCID '{contrib_orcid}' doesn't match the format xxxx-xxxx-xxxx-xxxx"
                )

    if not summary:
        errors.append("A description on how you collected the data is required.")

    if not data_owner_country:
        errors.append("Country is required.")

    if not uploaded_file:
        errors.append("At least one data file must be uploaded.")

    if data_owner_country == "UK" and not marinas:
        errors.append("Please specify whether the data was collected inside a marina.")

    if uploaded_file and not uploaded_file.name.lower().endswith(".csv"):
        errors.append(f"Uploaded file {uploaded_file.name} is not a csv file.")
    
    if not spatial_deployment:
        errors.append("Please specify the spatial deployment of the device.")
    
    elif spatial_deployment in ["Area", "Trajectory"] and not external_gps:
        errors.append("Please specify whether you used an external GPS source.")

    if spatial_deployment == "Fixed location":
        if not latitude:
            errors.append("Latitude is required.")
        elif validate_float(latitude) is None:
            errors.append("Latitude is not a valid number.")

        if not longitude:
            errors.append("Longitude is required.")
        elif validate_float(longitude) is None:
            errors.append("Longitude is not a valid number.")

    elif spatial_deployment in ["Area", "Trajectory"] and external_gps == "No":
        if not min_lat:
            errors.append("Minimum latitude is required.")
        elif validate_float(min_lat) is None:
            errors.append("Minimum latitude is not a valid number.")

        if not max_lat:
            errors.append("Maximum latitude is required.")
        elif validate_float(max_lat) is None:
            errors.append("Maximum latitude is not a valid number.")

        if not min_lon:
            errors.append("Minimum longitude is required.")
        elif validate_float(min_lon) is None:
            errors.append("Minimum longitude is not a valid number.")

        if not max_lon:
            errors.append("Maximum longitude is required.")
        elif validate_float(max_lon) is None:
            errors.append("Maximum longitude is not a valid number.")

    elif spatial_deployment in ["Area", "Trajectory"] and external_gps == "Yes":
        if not uploaded_gpx_file:
            errors.append("Please provide a GPX file.")
        else:
            if not uploaded_gpx_file.name.lower().endswith(".gpx"):
                errors.append(f"Coordinate file '{uploaded_gpx_file.name}' is not a GPX file.")

    if not depth_mode:
        errors.append("Please specify if the measurements have one fixed depth or different depths.")

    elif depth_mode == "One fixed depth":
        if not depth_value:
            errors.append("Depth is required.")
        elif depth_value != 0  and validate_float(depth_value) is None:
            errors.append("Depth is not a valid number.")

    elif depth_mode == "Different depths":
        if not min_depth:
            errors.append("Minimum depth value is required.")
        elif validate_float(min_depth) is None:
            errors.append("Minumum depth value is not a valid number.")

        if not max_depth:
            errors.append("Maximum depth value is required.")
        elif validate_float(max_depth) is None:
            errors.append("Maximum depth value is not a valid number.")
    
    if user_type == "Scientist" and not platform_type:
        errors.append("Please choose a platform type.")

    if user_type == "Scientist" and platform_type in [
                                                    "naval vessel",
                                                    "fishing vessel",
                                                    "research vessel",
                                                    "self-propelled boat vessel",
                                                    "ship",
                                                    "surface vessel",
                                                    "vessel at fixed position",
                                                    "vessel of opportunity",
                                                    "vessel of opportunity on fixed route",
                                                ] and not ship_name:
        errors.append("Please specify the ship's name")

    if user_type == "Scientist" and platform_type in [
                                                    "naval vessel",
                                                    "fishing vessel",
                                                    "research vessel",
                                                    "self-propelled boat vessel",
                                                    "ship",
                                                    "surface vessel",
                                                    "vessel at fixed position",
                                                    "vessel of opportunity",
                                                    "vessel of opportunity on fixed route",
                                                ] and (ship_imo  and validate_float(ship_imo) is None):
        errors.append("Ship's IMO is not a valid number")

    if user_type == "Scientist" and platform_type == "Other" and not plat_type_sdn_name:
        errors.append("Please provide a platform type from NERC vocabulary L06")
    
    return errors