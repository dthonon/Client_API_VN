"""
Test update_vn main.
"""

import csv
import importlib.resources
import logging
import time
from pathlib import Path

import pytest
from click.testing import CliRunner
from dynaconf import Dynaconf

from biolovision.api import HTTPError, ObservationsAPI
from update_vn import update_vn

# Using faune-france site, that needs to be defined in .evn_test.toml
SITE = "tff"
FILE = ".evn_test.toml"

# Get configuration for test site
ref = str(importlib.resources.files("update_vn") / "data/evn_default.toml")
settings = Dynaconf(
    settings_files=[ref, FILE],
)
cfg_site_list = settings.sites
assert len(cfg_site_list) == 1, _("Only one site can be defined in configuration file")
for site, cfg in cfg_site_list.items():  # noqa: B007
    break

OBSERVATIONS_API = ObservationsAPI(
    user_email=cfg.user_email,
    user_pw=cfg.user_pw,
    base_url=cfg.site,
    client_key=cfg.client_key,
    client_secret=cfg.client_secret,
    max_retry=settings.tuning.max_retry,
    max_requests=settings.tuning.max_requests,
    max_chunks=settings.tuning.max_chunks,
    unavailable_delay=settings.tuning.unavailable_delay,
    retry_delay=settings.tuning.retry_delay,
)


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


def test_version(runner):
    """Check if version is defined."""
    result = runner.invoke(update_vn.main, ["--version"])
    assert result.exit_code == 0


def test_init(runner):
    """Check --init parameter."""
    name_toml = ".evn_pytest.toml"
    file_toml = str(Path.home()) + "/" + name_toml
    if Path(file_toml).is_file():
        Path(file_toml).unlink()
    result = runner.invoke(update_vn.main, ["--verbose", "init", name_toml])
    assert result.exit_code == 0
    assert Path(file_toml).is_file()
    Path(file_toml).unlink()


def test_files(runner):
    """Check errors if files missing or incorrect."""
    # Missing CONFIG file
    name_toml = ".evn_missing.toml"
    file_toml = str(Path.home()) + "/" + name_toml
    if Path(file_toml).is_file():
        Path(file_toml).unlink()
    name_input = ".evn_missing.csv"
    file_input = str(Path.home()) + "/" + name_input
    Path(file_input).touch()
    result = runner.invoke(update_vn.main, ["--verbose", "update", name_toml, name_input])
    assert result.exit_code == 1
    # Missing CSV file
    name_toml = ".evn_tst1.toml"
    file_toml = str(Path.home()) + "/" + name_toml
    name_input = ".evn_missing.csv"
    file_input = str(Path.home()) + "/" + name_input
    if Path(file_input).is_file():
        Path(file_input).unlink()
    result = runner.invoke(update_vn.main, ["--verbose", "update", name_toml, name_input])
    assert result.exit_code == 1
    # Incorrect CONFIG file
    name_toml = ".evn_tst3.toml"
    file_toml = str(Path.home()) + "/" + name_toml
    name_input = ".evn_missing.csv"
    file_input = str(Path.home()) + "/" + name_input
    Path(file_input).touch()
    result = runner.invoke(update_vn.main, ["--verbose", "update", name_toml, name_input])
    assert result.exit_code == 1
    # Cleanup
    if Path(file_input).is_file():
        Path(file_input).unlink()


@pytest.fixture(scope="function")
def sighting_for_test():
    # Create a specific sighting.
    data = {
        "data": {
            "sightings": [
                {
                    "date": {"@timestamp": str(int(time.time()))},
                    "species": {"@id": "408"},
                    "observers": [
                        {
                            "@id": "57107",
                            "altitude": "230",
                            "comment": "TEST API !!! à supprimer !!!",
                            "coord_lat": "45.188302192726",
                            "coord_lon": "5.7364289068356",
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
        OBSERVATIONS_API.api_delete(str(sighting["id"][0]))


@pytest.mark.slow
def test_update(runner, sighting_for_test):
    """Check Biolovision updating."""
    name_toml = ".evn_test.toml"
    file_toml = str(Path.home()) + "/" + name_toml
    assert Path(file_toml).is_file()
    name_input = ".evn_pytest.csv"
    file_input = str(Path.home()) + "/" + name_input

    logging.debug("Created", sighting_for_test)
    assert sighting_for_test["status"] == "saved"
    obs_1 = sighting_for_test["id"][0]
    assert isinstance(obs_1, int)

    # Check handling of incorrect operation
    with open(file_input, "w", newline="") as csvfile:
        inwriter = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        inwriter.writerow([" site", "id_universal ", "path", "operation", " value "])
        inwriter.writerow([
            "tff",
            str(obs_1),
            "$['data']['sightings'][0]['observers'][0]['atlas_code']",
            "unknown",
            "2",
        ])
    result = runner.invoke(update_vn.main, ["--verbose", "update", name_toml, str(file_input)])
    assert result.exit_code == 0

    # Check handling of empty line
    with open(file_input, "w", newline="") as csvfile:
        inwriter = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        inwriter.writerow([" site", "id_universal ", "path", "operation", " value "])
        inwriter.writerow([])
        inwriter.writerow([
            "tff",
            str(obs_1),
            "$['data']['sightings'][0]['observers'][0]['atlas_code']",
            "unknown",
            "2",
        ])
    result = runner.invoke(update_vn.main, ["--verbose", "update", name_toml, str(file_input)])
    assert result.exit_code == 0

    # Update atlas_code
    with open(file_input, "w", newline="") as csvfile:
        inwriter = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        inwriter.writerow(["site", "id_universal", "path", "operation", "value"])
        inwriter.writerow([
            "tff",
            str(obs_1),
            "$['data']['sightings'][0]['observers'][0]['atlas_code']",
            "replace",
            "2",
        ])
    result = runner.invoke(update_vn.main, ["--verbose", "update", name_toml, str(file_input)])
    assert result.exit_code == 0
    sighting = OBSERVATIONS_API.api_get(str(obs_1))
    assert sighting["data"]["sightings"][0]["observers"][0]["atlas_code"]["@id"] == "3_2"

    # Update atlas_code
    with open(file_input, "w", newline="") as csvfile:
        inwriter = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        inwriter.writerow(["site", "id_universal", "path", "operation", "value"])
        inwriter.writerow([
            "tff",
            str(obs_1),
            "$['data']['sightings'][0]['observers'][0]['atlas_code']",
            "replace",
            "4",
        ])
    result = runner.invoke(update_vn.main, ["--verbose", "update", name_toml, str(file_input)])
    assert result.exit_code == 0
    sighting = OBSERVATIONS_API.api_get(str(obs_1))
    assert sighting["data"]["sightings"][0]["observers"][0]["atlas_code"]["@id"] == "3_4"

    # Remove atlas_code
    with open(file_input, "w", newline="") as csvfile:
        inwriter = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        inwriter.writerow(["site", "id_universal", "path", "operation", "value"])
        inwriter.writerow([
            "tff",
            str(obs_1),
            "$['data']['sightings'][0]['observers'][0]['atlas_code']",
            "delete_attribute",
            "",
        ])
    result = runner.invoke(update_vn.main, ["--verbose", "update", name_toml, str(file_input)])
    assert result.exit_code == 0
    sighting = OBSERVATIONS_API.api_get(str(obs_1))
    assert "atlas_code" not in sighting["data"]["sightings"][0]["observers"][0]

    # Update comment
    with open(file_input, "w", newline="") as csvfile:
        inwriter = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        inwriter.writerow(["site", "id_universal", "path", "operation", "value"])
        inwriter.writerow([
            "tff",
            str(obs_1),
            "$['data']['sightings'][0]['observers'][0]['comment']",
            "replace",
            "'API update test'",
        ])
    result = runner.invoke(update_vn.main, ["--verbose", "update", name_toml, str(file_input)])
    assert result.exit_code == 0
    sighting = OBSERVATIONS_API.api_get(str(obs_1))
    assert sighting["data"]["sightings"][0]["observers"][0]["comment"] == "'API update test'"

    # Remove observation
    with open(file_input, "w", newline="") as csvfile:
        inwriter = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        inwriter.writerow(["site", "id_universal", "path", "operation", "value"])
        inwriter.writerow(["tff", str(obs_1), "", "delete_observation", ""])
    result = runner.invoke(update_vn.main, ["--verbose", "update", name_toml, str(file_input)])
    assert result.exit_code == 0
