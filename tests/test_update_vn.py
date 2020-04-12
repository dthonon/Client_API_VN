"""
Test update_vn main.
"""
import csv
import logging
from pathlib import Path
from unittest.mock import patch

import pytest
from update import update_vn

from biolovision.api import (
    ObservationsAPI,
    HTTPError,
)
from export_vn.evnconf import EvnConf
from export_vn.store_file import StoreFile

# Using faune-ardeche or faune-isere site, that needs to be created first
# SITE = "t07"
SITE = "t38"
FILE = ".evn_test.yaml"

# Get configuration for test site
CFG = EvnConf(FILE).site_list[SITE]
OBSERVATIONS_API = ObservationsAPI(CFG)


def test_version():
    """Check if version is defined."""
    with patch("sys.argv", ["py.test", "--version"]):
        with pytest.raises(SystemExit):
            update_vn.run()


def test_init():
    """Check --init parameter."""
    name_yaml = ".evn_pytest.yaml"
    file_yaml = str(Path.home()) + "/" + name_yaml
    if Path(file_yaml).is_file():
        Path(file_yaml).unlink()
    name_input = ".evn_pytest.csv"
    file_input = str(Path.home()) + "/" + name_input
    Path(file_input).touch()
    with patch("sys.argv", ["py.test", "--init", name_yaml, name_input]):
        update_vn.run()
    assert Path(file_yaml).is_file()
    Path(file_yaml).unlink()
    Path(file_input).unlink()


@pytest.fixture(scope="function")
def sighting_for_test():
    # Create a specific sighting.
    data = {
        "data": {
            "sightings": [
                {
                    "date": {"@timestamp": "1577905620",},
                    "species": {"@id": "312",},
                    "observers": [
                        {
                            "@id": "33",
                            "altitude": "230",
                            "comment": "TEST API !!! à supprimer !!!",
                            "coord_lat": "45.18724",
                            "coord_lon": "5.735458",
                            "precision": "precise",
                            "count": "1",
                            "estimation_code": "MINIMUM",
                        }
                    ],
                }
            ]
        }
    }
    sighting = OBSERVATIONS_API.api_create(data)
    yield sighting
    # Finaly, check that sighting is deleted
    with pytest.raises(HTTPError):
        res = OBSERVATIONS_API.api_delete(str(sighting["id"][0]))


@pytest.mark.slow
def test_update(sighting_for_test):
    """Check Biolovision updating."""
    name_yaml = ".evn_aura.yaml"
    file_yaml = str(Path.home()) + "/" + name_yaml
    assert Path(file_yaml).is_file()
    name_input = ".evn_pytest.csv"
    file_input = str(Path.home()) + "/" + name_input

    logging.debug("Created", sighting_for_test)
    assert sighting_for_test["status"] == "saved"
    obs_1 = sighting_for_test["id"][0]
    assert isinstance(obs_1, int)

    # Update atlas_code
    with open(file_input, "w", newline="") as csvfile:
        inwriter = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        inwriter.writerow(["site", "id_universal", "path", "operation", "value"])
        inwriter.writerow(
            [
                "Isère",
                str(obs_1),
                "$['data']['sightings'][0]['observers'][0]['atlas_code']",
                "replace",
                "2",
            ]
        )
    with patch("sys.argv", ["py.test", name_yaml, "../" + name_input]):
        update_vn.run()
    sighting = OBSERVATIONS_API.api_get(str(obs_1))
    assert (
        sighting["data"]["sightings"][0]["observers"][0]["atlas_code"]["@id"] == "3_2"
    )

    # Update atlas_code
    with open(file_input, "w", newline="") as csvfile:
        inwriter = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        inwriter.writerow(["site", "id_universal", "path", "operation", "value"])
        inwriter.writerow(
            [
                "Isère",
                str(obs_1),
                "$['data']['sightings'][0]['observers'][0]['atlas_code']",
                "replace",
                "4",
            ]
        )
    with patch("sys.argv", ["py.test", name_yaml, "../" + name_input]):
        update_vn.run()
    sighting = OBSERVATIONS_API.api_get(str(obs_1))
    assert (
        sighting["data"]["sightings"][0]["observers"][0]["atlas_code"]["@id"] == "3_4"
    )

    # Remove atlas_code
    with open(file_input, "w", newline="") as csvfile:
        inwriter = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        inwriter.writerow(["site", "id_universal", "path", "operation", "value"])
        inwriter.writerow(
            [
                "Isère",
                str(obs_1),
                "$['data']['sightings'][0]['observers'][0]['atlas_code']",
                "delete_attribute",
                "",
            ]
        )
    with patch("sys.argv", ["py.test", name_yaml, "../" + name_input]):
        update_vn.run()
    sighting = OBSERVATIONS_API.api_get(str(obs_1))
    assert "atlas_code" not in sighting["data"]["sightings"][0]["observers"][0]

    # Update comment
    with open(file_input, "w", newline="") as csvfile:
        inwriter = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        inwriter.writerow(["site", "id_universal", "path", "operation", "value"])
        inwriter.writerow(
            [
                "Isère",
                str(obs_1),
                "$['data']['sightings'][0]['observers'][0]['comment']",
                "replace",
                "'API update test'",
            ]
        )
    with patch("sys.argv", ["py.test", name_yaml, "../" + name_input]):
        update_vn.run()
    sighting = OBSERVATIONS_API.api_get(str(obs_1))
    assert (
        sighting["data"]["sightings"][0]["observers"][0]["comment"] == "API update test"
    )

    # Remove observation
    with open(file_input, "w", newline="") as csvfile:
        inwriter = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        inwriter.writerow(["site", "id_universal", "path", "operation", "value"])
        inwriter.writerow(
            [
                "Isère",
                str(obs_1),
                "",
                "delete_observation",
                "",
            ]
        )
    with patch("sys.argv", ["py.test", name_yaml, "../" + name_input]):
        update_vn.run()

