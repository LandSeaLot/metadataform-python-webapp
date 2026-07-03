from config import *
import logging


logger = logging.getLogger("landsealot_form")


def download_user_manual(filepath):
    try:
        with open(filepath, "rb") as f:
            return f.read()
    except Exception as e:
        logger.error(
            f"Error in download button for file {filepath}: {e}"
        )
        return None