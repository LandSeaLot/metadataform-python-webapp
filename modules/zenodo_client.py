from modules.metadata import Metadata
from pathlib import Path
import datetime
import requests
import logging
import time
import os


logger = logging.getLogger("landsealot_form")


def _prepare_new_version(old_version):
    # FIXME handle if original version wasn't a date
    new_version = datetime.datetime.today().strftime("%Y-%m-%d")
    if old_version == new_version:
        new_version += "-1"
    elif (
        old_version.startswith(new_version)
        and old_version[-2] == "-"
        and old_version[-1].isnumeric()
    ):
        new_version += "-" + str(
            1 + int(old_version[-1])
        )  # please don't do this more than 10 times a day
    return new_version


class Zenodo:
    """A wrapper around parts of the Zenodo API."""

    def __init__(self, access_token, sandbox) -> None:
        self.sandbox = sandbox
        if self.sandbox:
            self.base = "https://sandbox.zenodo.org"
            self.module = "zenodo:sandbox"
            self.access_token = access_token
        else:
            self.base = "https://zenodo.org"
            self.module = "zenodo"
            self.access_token = access_token

        # Base URL for the API
        self.api_base = self.base + "/api"
        logger.debug("using Zenodo API at %s", self.api_base)

        # Base URL for depositions, relative to the API base
        self.depositions_base = self.api_base + "/deposit/depositions"

    def ensure(self, deposition_id, data, paths, publish):
        """
        Ensure a Zenodo record exists for a given dataset.
        - If deposition_id is provided, update the existing record (metadata + files)
        - Otherwise, create a new record
        """
        if deposition_id:
            logger.debug(f"Updating existing Zenodo record {deposition_id}")
            res = self.update(
                deposition_id=deposition_id, data=data, paths=paths, publish=publish
            )

            return res

        res = self.create(data=data, paths=paths, publish=publish)
        return res

    def verify_deposition_id(self, deposition_id):
        """
        Verify whether a given Zenodo deposition ID exists and is accessible.
        Returns:
            "editable" if deposition exists in /deposit (draft or submitted)
            "published" if it exists in /records (public record)
            None if not found
        """
        if not deposition_id:
            return None

        try:
            # 1. Check deposit (editable or draft)
            res = requests.get(
                f"{self.depositions_base}/{deposition_id}",
                params={"access_token": self.access_token},
                timeout=10,
            )
            if res.status_code == 200:
                if res.json().get("submitted", False):
                    return "published"
                return "draft"

            # 2. Check records (published)
            res = requests.get(f"{self.api_base}/records/{deposition_id}", timeout=10)
            if res.status_code == 200:
                return "published"

            return None

        except requests.RequestException as e:
            logger.error(f"Error verifying deposition {deposition_id}: {e}")
            return None

    def create(self, data, paths, *, publish):
        """Create a record.

        :param data: The JSON data to send to the new data
        :param paths: Paths to local files to upload
        :param publish: Publish the deposit after creation
        :return: The response JSON from the Zenodo API
        :raises ValueError: if the response is missing a "bucket"
        """
        if isinstance(data, Metadata):
            logger.debug("serializing metadata")
            data = {
                "metadata": {
                    key: value
                    for key, value in data.model_dump(exclude_none=True).items()
                    if value
                },
            }

        res = requests.post(
            self.depositions_base,
            json=data,
            params={"access_token": self.access_token},
        )
        if res.status_code == 400:
            raise ValueError(res.text)
        res.raise_for_status()

        res_json = res.json()
        bucket = res_json.get("links", {}).get("bucket")
        if bucket is None:
            raise ValueError(f"No bucket in response. Got: {res_json}")

        logger.debug("uploading files to bucket %s", bucket)
        self._upload_files(bucket=bucket, paths=paths)

        deposition_id = res_json["id"]
        if not publish:
            return self._get_deposition(deposition_id)

        logger.debug("publishing files to deposition %s", deposition_id)
        return self.publish(deposition_id)

    def edit(self, deposition_id: str, sleep: bool = True) -> requests.Response:
        """Unlock already submitted deposition for editing, see https://developers.zenodo.org/#edit.

        :param deposition_id: The identifier of the deposition on Zenodo.
        :param sleep: Sleep for one second just in case of race conditions. If you're feeling lucky and rushed, you
            might be able to get away with disabling this.
        :return: The response JSON from the Zenodo API
        """
        return self._action(deposition_id=deposition_id, action="edit", sleep=sleep)

    def publish(self, deposition_id):
        """Publish a record that's in edit mode, see https://developers.zenodo.org/#publish.

        :param deposition_id: The identifier of the deposition on Zenodo.
        :param sleep: Sleep for one second just in case of race conditions. If you're feeling lucky and rushed, you
            might be able to get away with disabling this.
        :return: The response JSON from the Zenodo API
        """
        return self._action(deposition_id=deposition_id, action="publish", sleep=1)

    def new_version(self, deposition_id, sleep):
        """Create a new version of a deposition, see https://developers.zenodo.org/#new-version.

        :param deposition_id: The identifier of the deposition on Zenodo.
        :param sleep: Sleep for one second just in case of race conditions. If you're feeling lucky and rushed, you
            might be able to get away with disabling this.
        :return: The response JSON from the Zenodo API
        """
        return self._action(
            deposition_id=deposition_id, action="newversion", sleep=sleep
        )

    def _action(self, deposition_id, action, sleep):
        """Run an action on a record.

        :param deposition_id: The identifier of the deposition on Zenodo. It should be in edit mode.
        :param action: The action to perform
        :param sleep: Sleep for one second just in case of race conditions. If you're feeling lucky and rushed, you
            might be able to get away with disabling this.
        :return: The response JSON from the Zenodo API
        """
        if sleep:
            time.sleep(1)
        res = requests.post(
            f"{self.depositions_base}/{deposition_id}/actions/{action}",
            params={"access_token": self.access_token},
        )
        res.raise_for_status()
        return res

    def _get_deposition(self, deposition_id):
        """Get the metadata for a deposition."""
        url = f"{self.depositions_base}/{deposition_id}"
        res = requests.get(url, params={"access_token": self.access_token})
        res.raise_for_status()
        return res

    def update(self, deposition_id, data, paths, publish):
        """
        Update a record, including creating a new version if already submitted.
        """
        res = self._get_deposition(deposition_id)
        deposition_data = res.json()

        if deposition_data.get("submitted", False):
            new_deposition_id, new_deposition_data = (
                self._update_submitted_deposition_metadata(deposition_id)
            )
        else:
            new_deposition_id, new_deposition_data = deposition_id, deposition_data

        bucket = new_deposition_data["links"]["bucket"]

        if isinstance(data, Metadata):
            data = {
                "metadata": {
                    k: v for k, v in data.model_dump(exclude_none=True).items() if v
                }
            }
        if data:
            res = requests.put(
                f"{self.depositions_base}/{new_deposition_id}",
                json=data,
                params={"access_token": self.access_token},
            )
            res.raise_for_status()

        self._upload_files(bucket=bucket, paths=paths)

        if publish:
            return self.publish(new_deposition_id)
        return self._get_deposition(new_deposition_id)

    def _update_submitted_deposition_metadata(self, deposition_id):
        res = self._get_deposition(deposition_id)
        old_version = res.json()["metadata"]["version"]
        new_version = _prepare_new_version(old_version)

        res = self.new_version(deposition_id, sleep=False)
        # Parse out the new version (@zenodo please give this as its own field!)
        new_deposition_id = res.json()["links"]["latest_draft"].split("/")[-1]

        # Get all metadata associated with the new version (this has updated DOIs, etc.)
        # see: https://developers.zenodo.org/#retrieve
        res = requests.get(
            f"{self.depositions_base}/{new_deposition_id}",
            params={"access_token": self.access_token},
        )
        res.raise_for_status()
        new_deposition_data = res.json()
        # Update the version and date
        new_deposition_data["metadata"]["version"] = new_version
        new_deposition_data["metadata"][
            "publication_date"
        ] = datetime.datetime.today().strftime("%Y-%m-%d")

        # Update the deposition for the new version
        # see: https://developers.zenodo.org/#update
        res = requests.put(
            f"{self.depositions_base}/{new_deposition_id}",
            json={"metadata": new_deposition_data["metadata"]},
            params={"access_token": self.access_token},
        )
        res.raise_for_status()

        return new_deposition_id, new_deposition_data

    def _upload_files(self, *, bucket, paths):
        _paths = [paths] if isinstance(paths, (str, Path)) else paths
        rv = []
        # see https://developers.zenodo.org/#quickstart-upload
        for path in _paths:
            with open(path, "rb") as file:
                res = requests.put(
                    f"{bucket}/{os.path.basename(path)}",
                    data=file,
                    params={"access_token": self.access_token},
                )

            res.raise_for_status()
            rv.append(res)
        return rv

    def get_record(self, record_id):
        """Get the metadata for a given record."""
        res = requests.get(
            f"{self.api_base}/records/{record_id}",
            params={"access_token": self.access_token},
        )
        res.raise_for_status()
        return res
