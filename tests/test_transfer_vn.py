"""
Test transfer_vn main.
"""
from pathlib import Path
from unittest.mock import patch

import pytest
from export_vn import transfer_vn


@pytest.mark.order(index=500)
def test_version():
    """Check if version is defined."""
    with patch("sys.argv", ["py.test", "--version"]):
        with pytest.raises(SystemExit):
            transfer_vn.run()


@pytest.mark.order(index=510)
def test_init():
    """Check --init parameter."""
    file_yaml = str(Path.home()) + "/" + ".evn_pytest.yaml"
    if Path(file_yaml).is_file():
        Path(file_yaml).unlink()
    with patch("sys.argv", ["py.test", "--init", ".evn_pytest.yaml"]):
        transfer_vn.run()
    assert Path(file_yaml).is_file()
    Path(file_yaml).unlink()


@pytest.mark.order(index=520)
def test_db_ops():
    """Check database management operations."""
    file_yaml = ".evn_test.yaml"
    with patch("sys.argv", ["py.test", "--db_drop", file_yaml]):
        transfer_vn.run()
    with patch("sys.argv", ["py.test", "--db_create", file_yaml]):
        transfer_vn.run()
    with patch("sys.argv", ["py.test", "--json_tables_create", file_yaml]):
        transfer_vn.run()
    with patch("sys.argv", ["py.test", "--col_tables_create", file_yaml]):
        transfer_vn.run()


@pytest.mark.order(index=530)
@pytest.mark.slow
def test_full():
    """Check database full download."""
    file_yaml = ".evn_test.yaml"
    with patch("sys.argv", ["py.test", "--full", file_yaml]):
        transfer_vn.run()


@pytest.mark.order(index=531)
def test_count():
    """Check database counting."""
    file_yaml = ".evn_test.yaml"
    with patch("sys.argv", ["py.test", "--count", file_yaml]):
        transfer_vn.run()


@pytest.mark.order(index=532)
def test_update():
    """Check database updating."""
    file_yaml = ".evn_test.yaml"
    with patch("sys.argv", ["py.test", "--schedule", file_yaml]):
        transfer_vn.run()
    with patch("sys.argv", ["py.test", "--update", file_yaml]):
        transfer_vn.run()


@pytest.mark.order(index=533)
def test_status():
    """Check database counting."""
    file_yaml = ".evn_test.yaml"
    with patch("sys.argv", ["py.test", "--status", file_yaml]):
        transfer_vn.run()
