#!/usr/bin/env python3
"""
Configure tests of biolovision_api module.

Add option --logging=LEVEL.
"""
import pytest

def pytest_addoption(parser):
    parser.addoption(
        '--logging', action='store',
        default='INFO', help='logging level: INFO, DEBUG'
    )

@pytest.fixture
def cmdopt(request):
    return request.config.getoption('--logging')
