"""
Test each method of store_file module.
"""

import gzip
import json
import logging
import shutil
from pathlib import Path

from dynaconf import Dynaconf

from export_vn.store_file import StoreFile

# Using faune-france site, that needs to be defined in .evn_test.yaml
SITE = "tff"
FILE = ".evn_test.toml"

# Get configuration for test site
settings = Dynaconf(
    settings_files=[FILE],
)
cfg_site_list = settings.site
assert len(cfg_site_list) == 1, _("Only one site can be defined in configuration file")
for site, cfg in cfg_site_list.items():  # noqa: B007
    break
STORE_FILE = StoreFile(settings.file.enabled, settings.file.file_store)


def test_version():
    """Check if version is defined."""
    logging.debug("package version: %s", STORE_FILE.version)


# ------------
# General data
# ------------
def test_general_data_file_store():
    """Store general items_dict to file."""
    assert len(settings.file.file_store) > 0
    dir_json = Path.home() / settings.file.file_store
    shutil.rmtree(dir_json, ignore_errors=True)
    file_json = dir_json / "general_data_1.json.gz"
    items_dict = {
        "data": [
            {
                "coord_lat": "44.888464632099",
                "coord_lon": "4.39188200157809",
                "id": "2096",
                "id_canton": "7",
                "insee": "07001",
                "name": "Accons",
            },
            {
                "coord_lat": "44.5978645499893",
                "coord_lon": "4.33293707873124",
                "id": "2097",
                "id_canton": "7",
                "insee": "07002",
                "name": "Ailhon",
            },
        ]
    }
    STORE_FILE.store("general_data", str(1), items_dict)
    assert Path(file_json).is_file()
    with gzip.open(file_json, "rb") as gziped:
        items_dict = json.loads(gziped.read().decode("utf-8"))
    assert len(items_dict["data"]) == 2
    STORE_FILE.delete_obs(None)
