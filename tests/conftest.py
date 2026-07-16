"""Pytest configuration shared by the whole test suite.

Safety guard for remote-write tests
------------------------------------
A few tests actually create / update / delete observations on the *live*
VisioNature site (they are marked with ``@pytest.mark.write``). To make sure
they can never run by accident, they are skipped unless the environment variable
``VN_ENABLE_WRITE_TESTS`` is explicitly set to ``"1"``.

Because the guard is applied at collection time (not through a ``-m`` marker
expression), no command-line flag alone can trigger these tests: enabling them
requires deliberately exporting ``VN_ENABLE_WRITE_TESTS=1``.
"""

import os

import pytest

WRITE_TESTS_ENABLED = os.environ.get("VN_ENABLE_WRITE_TESTS") == "1"


def pytest_collection_modifyitems(config, items):
    """Skip every ``write`` test unless writes are explicitly enabled."""
    if WRITE_TESTS_ENABLED:
        return
    skip_write = pytest.mark.skip(
        reason="remote-write test: modifies the live VisioNature site; set VN_ENABLE_WRITE_TESTS=1 to enable",
    )
    for item in items:
        if "write" in item.keywords:
            item.add_marker(skip_write)
