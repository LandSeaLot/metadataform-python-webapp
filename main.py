from modules.zenodo_uploader import upload_to_zenodo, update_zenodo_record
from modules.validate_inputs import validate_inputs
from modules.download import download_user_manual
from metadata.zenodo import build_zenodo_metadata
from modules.sections import envlogger_section
from metadata.builder import build_metadata
from modules.utils import img_to_base64
from modules.email import send_email
from metadata.xml import save_xml
from metadata.txt import save_txt
from parsers.envlogger import *
from datetime import datetime
import streamlit as st
from config import *
import logging
import shutil
import uuid


logger = logging.getLogger("landsealot_form")


user_type = None
creator_name = ""
creator_surname = ""
orcid= ""
associated_with_data = None
marinas = None
depth_mode = None
depth_value = None
min_depth = None
max_depth = None
latitude = None
longitude = None
min_lat = None
min_lon = None
max_lat = None
max_lon = None
uploaded_gpx_file = None
external_gps = None
plat_id_orig = None
plat_type_sdn_name = None
platform_type = None
ship_name = None
ship_call_sign = None
ship_imo = None
contributors_enabled = None
samplng_resolution = None
dfs_columns = {}
filename = None
sampling_resolution = None
success_counter = None
sensor_dirs = None

st.set_page_config(page_title='LandSeaLot', page_icon = FAVICON) 

if st.session_state.get("submission_completed"):
    st.title("Thank you for contributing")
    st.success(
        "Your data has been successfully uploaded and will contribute to the LandSeaLot project."
    )

    if st.button("Submit another dataset"):
        st.session_state.submission_completed = False
        st.rerun()

    st.stop()

###### FORM START 
# logo and title
st.iframe(
    f"""
    <link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">

    <div style="
        display:flex;
        align-items:center;
        gap:2px;
        font-family:'Source Sans 3', sans-serif;
        padding:0px;
    ">
        <img src="data:image/png;base64,{img_to_base64(LANDSEALOT_LOGO)}"
             style="height:100px;">

        <div style="
            font-size:25px;
            font-weight:600;
            color:#123A81;
            line-height:1;
        ">
            Land-Sea interface: Let's observe together!
        </div>
    </div>
    """,
    height=120,
)

# data and information on sensor deployment
st.markdown(
    "<h4 style='color:#123A81;'>DATA AND INFORMATION ON SENSOR DEPLOYMENT</h4>",
    unsafe_allow_html=True,
)

st.markdown("""
This form is designed to provide data and information describing how and when the data was collected.

The information you provide helps researchers, regulatory bodies, and decision-making systems to better understand the data, and to ensure its quality, reliability, traceability, and comparability.
""")

st.warning("Complete this form at the end of each measurement and instrument (device).")

st.markdown(
    """
<div style="line-height:1.3;">
A measurement is defined as a data collection activity that:
<ul>
<li>is carried out using the same instrument (device)</li>
<li>takes place at a specific point/area/transect in time</li>
<li>is performed by the same person or by the same group of people</li>
</ul>
The measurement could be:
<ul>
<li>Continuous measurement (set up the sensor and then leave)</li>
<li>Occasional measurement (take the measurement while present)</li>
</ul>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    "Consult the user manual to be guided through the process "
    "step by step, explaining what each field requires and why it matters."
)

st.download_button(
    label="↓ Download",
    data=download_user_manual(USER_MANUAL_PATH),
    file_name=USER_MANUAL_FILENAME,
    mime="application/pdf",
)

st.caption(
    "NOTE: according to geographical location of the sampling, "
    "the LIL and Partner are automatically determined."
)

# information about the user
st.markdown(
    "<h5 style='color:#123A81;'>INFORMATION ABOUT THE USER</h5>", unsafe_allow_html=True
)

# user type input
user_type = st.segmented_control(
    "What kind of user are you?",
    ["Citizen", "Scientist"],
    selection_mode="single",
    key="user_type",
)

if user_type:
    st.session_state._user_type_last_valid = user_type

if user_type == "Citizen":

    associated_with_data = st.segmented_control(
        "Do you want your name to be associated with this data?",
        ["Yes", "No"],
        selection_mode="single",
        key="associated_with_data",
    )

    if associated_with_data:
        st.session_state._associated_with_data_last_valid = associated_with_data

    st.caption(
        "If you select “Yes”, you consent to the processing of your personal data (first name and surname) in accordance with Regulation (EU) 2016/679 (GDPR), solely for project-related purposes linked to the collection of environmental data and their sharing with the scientific community through open access repositories for research and publication purposes."
    )

if (user_type == "Citizen" and associated_with_data == "Yes") or user_type == "Scientist":
    creator_surname = st.text_input(
        "Surname",
        key="creator_surname",
    )

    creator_name = st.text_input(
        "Name",
        key="creator_name",
    )

    orcid = st.text_input(
        "ORCID (e.g., 0000-0003-4020-2056)",
        key="creator_orcid",
    )

# contributors
if "contributors" not in st.session_state:
    st.session_state.contributors = {}

if user_type == "Scientist" or (user_type == "Citizen" and associated_with_data == "Yes"):
    contributors_enabled = st.segmented_control(
        "Are there any contributors to the data collection (i.e., people who helped collect the data)?",
        ["Yes", "No"],
        selection_mode="single",
        key="contributors_enabled",
    )

    if contributors_enabled:
        st.session_state._contributors_enabled_last_valid = contributors_enabled

    if contributors_enabled == "Yes":

        if not st.session_state.contributors:
            first_id = str(uuid.uuid4())
            st.session_state.contributors[first_id] = {
                "surname": "",
                "name": "",
                "orcid": "",
            }

        for cid, contributor in list(st.session_state.contributors.items()):

            col1, col2, col3, col4 = st.columns([3, 3, 3, 1])

            with col1:
                st.session_state.contributors[cid]["surname"] = st.text_input(
                    "Surname",
                    value=contributor["surname"],
                    key=f"surname_{cid}",
                )

            with col2:
                st.session_state.contributors[cid]["name"] = st.text_input(
                    "Name",
                    value=contributor["name"],
                    key=f"name_{cid}",
                )

            with col3:
                st.session_state.contributors[cid]["orcid"] = st.text_input(
                    "ORCID",
                    value=contributor["orcid"],
                    key=f"orcid_{cid}",
                )

            with col4:
                if st.button("❌", key=f"del_{cid}"):
                    del st.session_state.contributors[cid]
                    st.rerun()

        if st.button("Add another contributor"):
            new_id = str(uuid.uuid4())
            st.session_state.contributors[new_id] = {
                "surname": "",
                "name": "",
                "orcid": "",
            }
            st.rerun()

    elif contributors_enabled == "No":
        st.session_state.contributors = {}


default_sensor = next(iter(SENSORS))

if "selected_sensor" not in st.session_state:
    st.session_state.selected_sensor = st.session_state.get(
        "_selected_sensor_last_valid", default_sensor
    )

if "_selected_sensor_last_valid" not in st.session_state:
    st.session_state._selected_sensor_last_valid = default_sensor


st.markdown(
    "<h5 style='color:#123A81;'>DESCRIPTION OF THE DEVICE</h5>",
    unsafe_allow_html=True,
)

selected_sensor = st.segmented_control(
    "Select your device:",
    options=list(SENSORS.keys()),
    key="selected_sensor",
)

if selected_sensor is None:
    del st.session_state["selected_sensor"]
    st.rerun()
else:
    st.session_state._selected_sensor_last_valid = selected_sensor

# description of measurement 1
st.markdown(
    "<h5 style='color:#123A81;'>DESCRIPTION OF THE MEASUREMENT</h5>",
    unsafe_allow_html=True,
)

if selected_sensor == "EnvLogger":
    uploaded_file = st.file_uploader(
        "Upload the file downloaded from the EnvLogger APP", accept_multiple_files=False, key="uploaded_files"
    )

    envlogger_section()


summary = st.text_area(
    "Describe how you collect the data (what, how, where, who - "
    "e.g., The sampling took place in Loco Beach as part of a citizen "
    "science activity. The sensor was mounted on a rock face to continuously "
    "collect data at that specific location for 10 hours...)",
)

data_owner_country = st.selectbox(
    "Select the country where you collected the measurement",
    options=COUNTRIES,
    index=None,
    placeholder="Choose a country...",
    key="data_owner_country",
)

if data_owner_country == "UK":
    marinas = st.segmented_control(
        "Did you collect data inside a marina?",
        ["Yes", "No"],
        selection_mode="single",
        key="marinas",
    )

    if marinas:
        st.session_state._marinas_last_valid = marinas

# description of measurement 2

spatial_deployment = st.segmented_control(
    "Please specify the spatial deployment of the device",
    ["Fixed location", "Area", "Trajectory"],
    selection_mode="single",
    key="spatial_deployment"
)

if spatial_deployment:
    st.session_state._spatial_deployment_last_valid = spatial_deployment


if spatial_deployment == "Fixed location":
    latitude = st.text_input(
        "Enter the latitude in the WGS84 reference system (e.g., 44.7468391 - obtained from GPS or Google Maps)",
        placeholder="",
        key="latitude",
    )

    longitude = st.text_input(
        "Enter the longitude in the WGS84 reference system (e.g., 8.8564029 - obtained from GPS or Google Maps)",
        placeholder="",
        key="longitude",
    )

elif spatial_deployment in ["Area", "Trajectory"]:

    external_gps = st.segmented_control(
        "The device does not have an integrated GPS, do you use an external GPS source to collect geographical coordinates?",
        ["Yes", "No"],
        selection_mode="single",
        key="external_gps",
    )

    if external_gps:
        st.session_state._external_gps_last_valid = external_gps

    if external_gps == "Yes":
        uploaded_gpx_file = st.file_uploader(
            "Drop the GPX file below",
            accept_multiple_files=False,
            key="uploaded_gpx",
        )
    elif external_gps == "No":

        min_lat = st.text_input(
            "Enter the minimum latitude in the WGS84 reference system (e.g., 44.7468391 - obtained from GPS or Google Maps)",
            placeholder="",
            key="min_lat",
        )

        max_lat = st.text_input(
            "Enter the maximum latitude in the WGS84 reference system (e.g., 44.7468391 - obtained from GPS or Google Maps)",
            placeholder="",
            key="max_lat",
        )

        min_lon = st.text_input(
            "Enter the minimum longitude in the WGS84 reference system (e.g., 8.8564029 - obtained from GPS or Google Maps)",
            placeholder="",
            key="min_lon",
        )

        max_lon = st.text_input(
            "Enter the maximum longitude in the WGS84 reference system (e.g., 8.8564029 - obtained from GPS or Google Maps)",
            placeholder="",
            key="max_lon",
        )

# description of the measurement 3
depth_mode = st.segmented_control(
    "The measurements are taken along the water column at",
    ["One fixed depth", "Different depths"],
    selection_mode="single",
    key="depth_mode",
)

if depth_mode:
    st.session_state._depth_mode_last_valid = depth_mode

if depth_mode == "One fixed depth":
    depth_value = st.text_input(
        "Enter the depth in meters (positive value, e.g., 5.0)",
        placeholder="",
        key="depth_value",
    )

elif depth_mode == "Different depths":
    min_depth = st.text_input(
        "Enter the minimum depth in meters (positive value, e.g., 5.0)",
        placeholder="",
        key="min_depth",
    )

    max_depth = st.text_input(
        "Enter the maximum depth in meters (positive value, e.g., 5.0)",
        placeholder="",
        key="max_depth",
    )

if user_type == "Scientist":
    # description of the measurement 4
    platform_types_options = sorted([p for p in PLATFORM_TYPES.keys() if p != "Other"]) + ["Other"]
    platform_type = st.selectbox(
        "Select the platform type used to collect the data:",
        options=platform_types_options,
        index=None,
        placeholder="",
        key="platform_type",
    )

    st.caption(
        "A platform is any physical or technological system that supports and enables the collection of measurements in a given environment, such as vessels, fixed stations, structure, sampling point"
    )

    if platform_type == "Other":
        plat_type_sdn_name = st.text_input(
            "If other, please indicate which platform (NERC vocabulary L06 https://vocab.nerc.ac.uk/collection/L06/current/)",
            placeholder="",
            key="plat_type_sdn_name",
        )

    elif platform_type in [
        "naval vessel",
        "fishing vessel",
        "research vessel",
        "self-propelled boat vessel",
        "ship",
        "surface vessel",
        "vessel at fixed position",
        "vessel of opportunity",
        "vessel of opportunity on fixed route",
    ]:
        ship_name = st.text_input(
            "Indicate the name of the ship", placeholder="", key="ship_name"
        )

        ship_call_sign = st.text_input(
            "Indicate the maritime call sign (unique ship alphanumeric identifier - ask to the ship/vessel/boat crew)",
            placeholder="",
            key="ship_call_sign",
        )

        ship_imo = st.text_input(
            "Indicate the IMO number (unique ship identifier - ask to the ship/vessel/boat crew or see on https://www.marinevesseltraffic.com/2013/06/imo-number-search.html - report only the 7-digit number)"
        )

    plat_id_orig = st.text_input(
        "If applicable, enter the pre-existing platform identifier",
        placeholder="",
        key="plat_id_orig",
    )

notes = st.text_input(
    "Write here any additional information on deployment",
    placeholder="",
    key="notes",
)

# submit button
submit = st.button("Send")
###### FORM END 

if submit:
    # validation
    errors = validate_inputs(
        user_type,
        creator_surname,
        creator_name,
        orcid,
        associated_with_data,
        contributors_enabled,
        st.session_state.contributors,
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
    )

    if errors:
        for err in errors:
            st.error(err)
    else:
        user_metadata = {
            "user_type": user_type,
            "summary": summary,

            # creators
            "creator": {
                "name": creator_name,
                "surname": creator_surname,
                "orcid": orcid,
            },

            # contributors
            "contributors": list(st.session_state.contributors.values()),

            # spatial
            "spatial_deployment": spatial_deployment,
            "latitude": float(latitude) if latitude is not None else None, 
            "longitude": float(longitude) if longitude is not None else None, 

            "external_gps": external_gps, 

            "min_lat": float(min_lat) if min_lat is not None else None, 
            "max_lat": float(max_lat) if max_lat is not None else None, 
            "min_lon": float(min_lon) if min_lon is not None else None, 
            "max_lon": float(max_lon) if max_lon is not None else None, 

            # depth
            "depth_mode": depth_mode,
            "depth_value": depth_value, 
            "min_depth": min_depth, 
            "max_depth": max_depth, 

            # platform
            "platform_type": platform_type,
            "platform_id_orig": plat_id_orig, 
            "notes": notes,

            # vessel specific
            "ship_name": ship_name, 
            "ship_call_sign": ship_call_sign, 
            "ship_imo": ship_imo, 
            "marinas": marinas, 

            # custom platform
            "platform_custom_name": (
                plat_type_sdn_name,
            ),
        }

        epoch = str(datetime.datetime.now(tz=datetime.timezone.utc).timestamp()).replace(".", "").ljust(16, "0")
    
        temp_dir = os.path.join(DATA_PATH, epoch)
        os.makedirs(temp_dir, exist_ok=True)
        
        uploaded_files = [uploaded_file]
        if uploaded_gpx_file:
            uploaded_files += [uploaded_gpx_file]
        sensor_dirs = save_uploaded_files(
            uploaded_files,
            temp_dir,
        )

        if uploaded_gpx_file:
            gps_df = build_gpx_dataframe(
                os.path.join(temp_dir, "gps")
            )
        else:
            gps_df = pd.DataFrame()
    
        min_start_date = ""
    
        success_counter = 0
    
        for sensor_id, sensor_dir in sensor_dirs.items():
            warning = None
            upload_results = []
    
            try:
                workspace = SensorWorkspace(
                    sensor_id,
                    sensor_dir,
                )
    
                filenames_dfs = build_sensor_dataframes(
                    workspace
                )
                start_dates = []
                end_dates = []
                dfs_columns = {}
                for filename, file_data in filenames_dfs.items():
                    df = file_data.get("df")
                    sampling_resolution = file_data.get("sampling_resolution")
                    custom_name = file_data.get("custom_name")
                    if not gps_df.empty:
                        df = merge_coordinates(
                            df,
                            gps_df
                        )
                        # Determine latitude/longitude column names
                        lat_col = None
                        lon_col = None

                        if "latitude" in df.columns and "longitude" in df.columns:
                            lat_col = "latitude"
                            lon_col = "longitude"
                        elif "ALATZZ01" in df.columns and "ALONZZ01" in df.columns:
                            lat_col = "ALATZZ01"
                            lon_col = "ALONZZ01"

                        # Update global spatial extent
                        if lat_col and lon_col:
                            current_min_lat = df[lat_col].min()
                            current_max_lat = df[lat_col].max()
                            current_min_lon = df[lon_col].min()
                            current_max_lon = df[lon_col].max()

                            min_lat = (
                                current_min_lat
                                if min_lat is None
                                else min(min_lat, current_min_lat)
                            )

                            max_lat = (
                                current_max_lat
                                if max_lat is None
                                else max(max_lat, current_max_lat)
                            )

                            min_lon = (
                                current_min_lon
                                if min_lon is None
                                else min(min_lon, current_min_lon)
                            )

                            max_lon = (
                                current_max_lon
                                if max_lon is None
                                else max(max_lon, current_max_lon)
                            )
    
                    start_date = (
                        df["time"]
                        .min()
                        .strftime("%Y-%m-%dT%H:%M:%SZ")
                    )
                    start_dates.append(start_date)
                    end_date = (
                        df["time"]
                        .max()
                        .strftime("%Y-%m-%dT%H:%M:%SZ")
                    )
                    end_dates.append(end_date)
    
                    df_cols = save_processed_dataframe(
                        filename,
                        workspace,
                        df,
                    )

                    if sensor_id not in dfs_columns:
                        dfs_columns[sensor_id] = {}
                    dfs_columns[sensor_id][filename] = df_cols
    
                min_start_date = min(start_dates)
                max_end_date = max(end_dates)

            except Exception as e:
                warning = f"Error in data elaboration, unprocessed files will be uploaded: {str(e)}"
                logger.warning(warning)
                min_start_date, max_end_date = move_unprocessed_files(sensor_dir)
    
            # metadata building and saving
            parsed_metadata = build_metadata(
                country=data_owner_country,
                marinas=marinas,
                sensor_id=sensor_id,
                start_date=min_start_date,
                end_date=max_end_date,
                user_metadata=user_metadata,
                sampling_resolution=sampling_resolution,
                custom_name=custom_name
            )

            zenodo_payload = build_zenodo_metadata(
                parsed_metadata, min_start_date, max_end_date
            )

            success, json_response, doi, zenodo_id = upload_to_zenodo(
                sensor_dir,
                zenodo_payload,
            )

            parsed_metadata["global_attributes"]["data_doi"] = doi

            save_txt(
                parsed_metadata,
                os.path.join(
                    sensor_dir,
                    "processed",
                    "metadata.txt",
                ),
                dfs_columns.get(sensor_id, {}).get(filename, []),
            )

            save_xml(
                parsed_metadata,
                os.path.join(
                    sensor_dir,
                    "processed",
                    "metadata.xml",
                ),
            )

            success, json_response = update_zenodo_record(
                sensor_dir,
                zenodo_payload,
                doi, 
                zenodo_id
            )

            upload_results.append(
                {
                    "sensor_id": sensor_id,
                    "success": success,
                    "response": json_response,
                }
            )

            send_email(upload_results, warning)
    
            if success:
                logger.info(f"Upload of sensor {sensor_id} was successfull. Removing folder {sensor_dir}")
                shutil.rmtree(sensor_dir)
                success_counter += 1

            else:
                logger.warning(f"Upload of sensor {sensor_id} failed. Folder {sensor_dir} won't be deleted.")
    
        if success_counter == len(sensor_dirs.keys()):
            shutil.rmtree(temp_dir)
            logger.debug(
                f"All sensors were uploaded successfully. Removing folder {temp_dir}"
            )

            st.session_state.submission_completed = True
            st.rerun()