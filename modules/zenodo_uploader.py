from modules.zenodo_client import Zenodo
from datetime import datetime
# from modules.cache import save_cache
from modules.models import Metadata
from config import *
import logging
import os


logger = logging.getLogger("landsealot_form")


def upload_to_zenodo(folder_to_process, zenodo_meta):
    try:
        folder_name = os.path.basename(folder_to_process)

        # updating publication date:
        publication_date_yyyy_mm_dd = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d")
        zenodo_meta["metadata"]["publication_date"] = publication_date_yyyy_mm_dd

        if not zenodo_meta:
            return False, {"error": "No metadata provided"}, None, None

        # metadata validation using pydantic model
        zenodo_meta_to_upload = Metadata.model_validate(zenodo_meta.get("metadata", {}))
        zenodo_meta_to_upload = zenodo_meta_to_upload.model_dump(exclude_none=True)

        # files_to_upload = [
        #     os.path.join(folder_to_process, "processed", f)
        #     for f in os.listdir(os.path.join(folder_to_process, "processed"))
        # ]

        zenodo_token = zenodo_meta.get("config", {}).get(
            "zenodo_token", DEFAULT_ZENODO_TOKEN
        )
        zen = Zenodo(access_token=zenodo_token, sandbox=SANDBOX)
        logger.debug(
            f"Initialized Zenodo client. Using token {zenodo_token}. Sandbox: {SANDBOX}"
        )
        publish = zenodo_meta.get("config", {}).get("publish", False)
        if isinstance(publish, str):
            try:
                publish = eval(publish.capitalize())
            except:
                pass

        logger.info(f"Uploading {folder_name} to Zenodo...")

        res = zen.ensure(
            deposition_id=None,
            data={"metadata": zenodo_meta_to_upload},
            # paths=files_to_upload,
            paths=[],
            publish=publish,
        )
        if 300 > res.status_code >= 200:
            logger.debug(f"{folder_name} uploaded successfully to Zenodo")

        res_json = res.json()
        
        reserved = (
            res_json
            .get("metadata", {})
            .get("prereserve_doi")
        )
        doi = None
        if reserved:
            doi = reserved["doi"]

        zenodo_id = res_json.get("id")

        return True, res_json, doi, zenodo_id

    except Exception as e:
        logger.error(f"Error uploading {folder_name} to Zenodo: {str(e)}")
        return False, {"error": str(e)}, None, None


def update_zenodo_record(folder_to_process, zenodo_meta, doi, zenodo_id):
    try:
        folder_name = os.path.basename(folder_to_process)

        # updating publication date:
        publication_date_yyyy_mm_dd = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d")
        zenodo_meta["metadata"]["publication_date"] = publication_date_yyyy_mm_dd

        if not zenodo_meta:
            return False, {"error": "No metadata provided"}

        files_to_upload = [
            os.path.join(folder_to_process, "processed", f)
            for f in os.listdir(os.path.join(folder_to_process, "processed"))
        ]

        # metadata validation using pydantic model
        zenodo_meta_to_upload = Metadata.model_validate(zenodo_meta.get("metadata", {}))
        zenodo_meta_to_upload = zenodo_meta_to_upload.model_dump(exclude_none=True)

        zenodo_meta_to_upload["doi"] = doi

        zenodo_token = zenodo_meta.get("config", {}).get(
            "zenodo_token", DEFAULT_ZENODO_TOKEN
        )
        zen = Zenodo(access_token=zenodo_token, sandbox=SANDBOX)
        logger.debug(
            f"Initialized Zenodo client. Using token {zenodo_token}. Sandbox: {SANDBOX}"
        )
        publish = zenodo_meta.get("config", {}).get("publish", False)
        if isinstance(publish, str):
            try:
                publish = eval(publish.capitalize())
            except:
                pass

        logger.info(f"Uploading {folder_name} to Zenodo...")

        res = zen.update(
            deposition_id=zenodo_id,
            data={
                "metadata": zenodo_meta_to_upload
            },
            paths=files_to_upload,
            publish=publish
        )
        res_json = res.json()

        return True, res_json

    except Exception as e:
        logger.error(f"Error uploading {folder_name} to Zenodo: {str(e)}")
        return False, {"error": str(e)}