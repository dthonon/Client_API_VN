"""
Test each method of store_file module.
"""
import gzip
import json
import logging
import shutil
from pathlib import Path

from export_vn.evnconf import EvnConf
from export_vn.store_file import StoreFile

# Using faune-ardeche or faune-isere site, that needs to be created first
# SITE = "t07"
SITE = 't38'
FILE = ".evn_test.yaml"

# Get configuration for test site
CFG = EvnConf(FILE).site_list[SITE]
STORE_FILE = StoreFile(CFG)


def test_version():
    """Check if version is defined."""
    logging.debug("package version: %s", STORE_FILE.version)


# ------------
# General data
# ------------
def test_general_data_file_store():
    """Store general items_dict to file."""
    assert len(CFG.file_store) > 0
    dir_json = str(Path.home()) + "/" + CFG.file_store
    shutil.rmtree(dir_json, ignore_errors=True)
    file_json = dir_json + "general_data_1.json.gz"
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
