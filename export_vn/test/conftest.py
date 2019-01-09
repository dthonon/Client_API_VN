#!/usr/bin/env python3
"""
Configure tests of biolovision_api module.

Add option --logging=LEVEL.
"""
import pytest
import logging

def pytest_addoption(parser):
    parser.addoption(
        '--logging', action='store',
        default='INFO', help='logging level: INFO, DEBUG'
    )

@pytest.fixture
def cmdopt(request):
    return request.config.getoption('--logging')

@pytest.fixture(scope="session", autouse=True)
def setup_logging(request):
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level = logging.INFO)
    logging.debug('Running with info logging level')
    if request.config.getoption('--logging') == 'DEBUG':
        logging.getLogger().setLevel(logging.DEBUG)
    logging.debug('Running with debug logging level')
