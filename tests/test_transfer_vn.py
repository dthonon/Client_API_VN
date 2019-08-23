"""
Test transfer_vn main.
"""
import logging
from unittest.mock import patch

from export_vn import transfer_vn


def test_version():
    """Check if version is defined."""
    with patch("sys.argv", ["py.test", "--init", ".evn_pytest.yaml"]):
        transfer_vn.run()
