"""
Test update_vn main.
"""
import csv
from pathlib import Path
from unittest.mock import patch

import pytest
from update import update_vn


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


@pytest.mark.slow
def test_update():
    """Check Biolovision updating."""
    name_yaml = ".evn_aura.yaml"
    file_yaml = str(Path.home()) + "/" + name_yaml
    assert Path(file_yaml).is_file()
    name_input = ".evn_pytest.csv"
    file_input = str(Path.home()) + "/" + name_input
    with open(file_input, "w", newline="") as csvfile:
        inwriter = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        inwriter.writerow(["site", "id_universal", "path", "operation", "value"])
        inwriter.writerow(
            [
                "Isère",
                "2246086",
                "$['data']['sightings'][0]['observers'][0]['atlas_code']",
                "replace",
                "2",
            ]
        )
    with patch("sys.argv", ["py.test", name_yaml, "../" + name_input]):
        update_vn.run()
    with open(file_input, "w", newline="") as csvfile:
        inwriter = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        inwriter.writerow(["site", "id_universal", "path", "operation", "value"])
        inwriter.writerow(
            [
                "Isère",
                "2246086",
                "$['data']['sightings'][0]['observers'][0]['atlas_code']",
                "replace",
                "4",
            ]
        )
    with patch("sys.argv", ["py.test", name_yaml, "../" + name_input]):
        update_vn.run()
    with open(file_input, "w", newline="") as csvfile:
        inwriter = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        inwriter.writerow(["site", "id_universal", "path", "operation", "value"])
        inwriter.writerow(
            [
                "Isère",
                "2246086",
                "$['data']['sightings'][0]['observers'][0]['comment']",
                "replace",
                "'API update test'",
            ]
        )
    with patch("sys.argv", ["py.test", name_yaml, "../" + name_input]):
        update_vn.run()
