"""
Test transfer_vn main.
"""
from pathlib import Path
from unittest.mock import patch

import pytest
from export_vn import transfer_vn


def test_version():
    """Check if version is defined."""
    with patch("sys.argv", ["py.test", "--version"]):
        with pytest.raises(SystemExit):
            transfer_vn.run()


def test_init():
    """Check --init parameter."""
    file_yaml = str(Path.home()) + "/" + ".evn_pytest.yaml"
    if Path(file_yaml).is_file():
        Path(file_yaml).unlink()
    with patch("sys.argv", ["py.test", "--init", ".evn_pytest.yaml"]):
        transfer_vn.run()
    assert Path(file_yaml).is_file()


@pytest.mark.slow
def test_db_ops():
    """Check database management parameters."""
    file_yaml = ".evn_test.yaml"
    with patch("sys.argv", ["py.test", "--db_drop", file_yaml]):
        transfer_vn.run()
    with patch("sys.argv", ["py.test", "--db_create", file_yaml]):
        transfer_vn.run()
    with patch("sys.argv", ["py.test", "--json_tables_create", file_yaml]):
        transfer_vn.run()
    with patch("sys.argv", ["py.test", "--col_tables_create", file_yaml]):
        transfer_vn.run()
    with patch("sys.argv", ["py.test", "--full", file_yaml]):
        transfer_vn.run()
