from config import MAX_TIMEDELTA #, ENVLOGGER_RENAME
import pandas as pd
import zipfile
import logging
import shutil
import gpxpy
import math
import json
import re
import os

logger = logging.getLogger("landsealot_form")


class SensorWorkspace:

    def __init__(self, sensor_id, sensor_dir):

        self.sensor_id = sensor_id
        self.sensor_dir = sensor_dir
        self.processed_dir = os.path.join(sensor_dir, "processed")

    def csv_files(self):

        return [
            os.path.join(self.sensor_dir, f)
            for f in os.listdir(self.sensor_dir)
            if f.endswith(".csv")
        ]


# FUNCTIONS

SENSOR_REGEX = re.compile(
    r"[0-9A-Fa-f]{4}[_ ][0-9A-Fa-f]{4}[_ ][0-9A-Fa-f]{4}[_ ][0-9A-Fa-f]{2}"
)


def get_sensor_id_from_file(file_path):
    sensor_id = "not found"
    with open(file_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith("serial number"):
            sensor_id = line.split(",")[-1].strip()
            break
    return sensor_id


def get_sensor_id(filepath, filename):
    match = SENSOR_REGEX.search(filename)

    if match:
        return match.group(0)

    return get_sensor_id_from_file(filepath)


def save_uploaded_files(uploaded_files, temp_dir):
    """
    Saves uploaded CSV/ZIP files directly into:

        temp_dir/
            sensor_id/
                file1.csv
                file2.csv

    Returns:

        {
            sensor_id: sensor_dir
        }
    """

    sensor_dirs = {}

    def save_csv_content(filename, content):
        tmp_file = os.path.join(temp_dir, filename)

        # temporary save only to determine sensor id
        with open(tmp_file, "wb") as f:
            f.write(content)

        sensor_id = get_sensor_id(tmp_file, filename)

        if not sensor_id:
            logger.error(f"Could not determine sensor id for {filename}")
            # os.remove(tmp_file)
            # return

        sensor_dir = os.path.join(temp_dir, sensor_id)
        os.makedirs(sensor_dir, exist_ok=True)

        final_path = os.path.join(sensor_dir, filename)
        os.replace(tmp_file, final_path)

        sensor_dirs[sensor_id] = sensor_dir

    def save_gpx_content(filename, content):
        gps_dir = os.path.join(temp_dir, "gps")
        os.makedirs(gps_dir, exist_ok=True)

        with open(os.path.join(gps_dir, filename), "wb") as f:
            f.write(content)

    for uploaded_file in uploaded_files:

        filename = uploaded_file.name

        if filename.lower().endswith(".csv"):

            save_csv_content(
                filename,
                uploaded_file.getbuffer(),
            )

        elif filename.lower().endswith(".zip"):

            with zipfile.ZipFile(uploaded_file) as z:

                for member in z.namelist():

                    if not member.lower().endswith(".csv"):
                        continue

                    filename = os.path.basename(member)

                    if not filename:
                        continue

                    with z.open(member) as src:

                        save_csv_content(
                            filename,
                            src.read(),
                        )

        elif filename.lower().endswith(".gpx"):
            filename = uploaded_file.name

            save_gpx_content(
                filename,
                uploaded_file.getbuffer(),
            )

    return sensor_dirs


def parse_envlogger_csv(filepath):
    sampling_resolution = None
    custom_name = None

    with open(filepath, "r") as f:

        content = f.read()

    # sampling resolution and custom name extraction
    for l in content.split("\n"):
        if "sampling resolution," in l:
            sampling_resolution = l.split(",")[-1].strip()
        if "custom name," in l:
            custom_name = l.split(",")[-1].strip()

    data_rows = content.split("------------------------------,--------------------")[-1]

    meta_rows = content.split("------------------------------,--------------------")[-2]

    lines = data_rows.strip().split("\n")

    data = [line.split(",") for line in lines]

    df = pd.DataFrame(
        data[1:],
        columns=data[0],
    )

    for line in meta_rows.split("\n"):

        parts = line.split(",")

        if len(parts) < 2:
            continue

    df["latitude"] = math.nan
    df["longitude"] = math.nan

    return df, sampling_resolution, custom_name


def build_sensor_dataframes(workspace):

    filenames_dfs = {}

    for csv_file in workspace.csv_files():

        df, sampling_resolution, custom_name = parse_envlogger_csv(csv_file)

        if not isinstance(df, pd.DataFrame):
            continue

        df["time"] = pd.to_datetime(
            df["time"],
            utc=True,
        )

        df.sort_values(
            "time",
            inplace=True,
        )

        filenames_dfs[csv_file] = {"df": df, "sampling_resolution": sampling_resolution, "custom_name": custom_name}

    return filenames_dfs


def build_gpx_dataframe(gps_dir):

    dfs = []
    if not os.path.exists(gps_dir):
        return pd.DataFrame()

    for filename in os.listdir(gps_dir):

        if not filename.endswith(".gpx"):
            continue

        with open(
            os.path.join(gps_dir, filename),
            "r",
        ) as g:

            gpx = gpxpy.parse(g)

        rows = []

        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:

                    rows.append(
                        {
                            "time": point.time,
                            "latitude": point.latitude,
                            "longitude": point.longitude,
                        }
                    )

        if rows:

            dfs.append(pd.DataFrame(rows))

    if not dfs:
        return None

    gps_df = pd.concat(
        dfs,
        ignore_index=True,
    )

    gps_df["time"] = pd.to_datetime(
        gps_df["time"],
        utc=True,
    )

    gps_df.sort_values(
        "time",
        inplace=True,
    )

    return gps_df


def merge_coordinates(df_csv, times_coords_df):
    if not df_csv["latitude"].hasnans and not df_csv["longitude"].hasnans:
        return
    df_csv["time"] = pd.to_datetime(df_csv["time"], utc=True)
    df_csv.sort_values("time", inplace=True)
    merged_df = pd.merge_asof(
        df_csv, times_coords_df, on="time", direction="nearest", tolerance=MAX_TIMEDELTA
    )
    merged_df.drop(columns=["latitude_x", "longitude_x"], inplace=True)
    merged_df.rename(
        columns={"latitude_y": "latitude", "longitude_y": "longitude"}, inplace=True
    )
    if not merged_df["latitude"].hasnans and not merged_df["longitude"].hasnans:
        # sort columns order
        cols = merged_df.columns.tolist()
        columns_order = [
            "time",
            "latitude",
            "longitude",
            "depth",
        ]
        columns_order = [c for c in columns_order if c in merged_df.columns]
        other_cols = [col for col in cols if col not in columns_order]
        cols = columns_order + other_cols
        merged_df = merged_df[cols]

    return merged_df


def save_processed_dataframe(
    filename,
    workspace,
    df,
):
    try:
        with open(os.path.join("resources", "variables_metadata.json"), "r", encoding="utf-8") as f:
            variables_meta = json.load(f)
    except Exception as e:
        variables_meta = {}
        logger.error(f"Error loading variables metadata file to add units: {str(e)}")

    out_df = df.copy()

    out_df["time"] = out_df["time"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    os.makedirs(workspace.processed_dir, exist_ok=True)

    basename = os.path.basename(filename)

    if "latitude" in out_df.columns and all(pd.isna(out_df['latitude'])):
        out_df.drop(columns=["latitude"], inplace=True)
    if "longitude" in out_df.columns and all(pd.isna(out_df['longitude'])):
        out_df.drop(columns=["longitude"], inplace=True)

    rename_map = {c: variables_meta.get(c, {}).get("code") for c in out_df.columns if variables_meta.get(c, {}).get("code")} 
    units = [variables_meta.get(c, {}).get("units", "") for c in out_df.columns]

    out_df.rename(columns=rename_map, inplace=True)
    cols = out_df.columns

    output_file = os.path.join(workspace.processed_dir, basename)

    if any(units):

        units_df = pd.DataFrame([units], columns=cols)

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            f.write(",".join(cols) + "\n")

            units_df.to_csv(
                f,
                index=False,
                header=False,
            )

            out_df.to_csv(
                f,
                index=False,
                header=False,
            )
    else:
        out_df.to_csv(
            output_file,
            index=False,
        )

    return list(out_df.columns)


def move_unprocessed_files(sensor_dir):
    processed_dir = os.path.join(sensor_dir, "processed")
    os.makedirs(processed_dir, exist_ok=True)
    for f in os.listdir(sensor_dir):
        if f.endswith('.csv'):
            shutil.move(os.path.join(sensor_dir,f), os.path.join(processed_dir, f))
    return None, None

