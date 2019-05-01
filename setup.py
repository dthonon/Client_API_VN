#!/usr/bin/env python
"""Setup for export_vn package.
"""
import os
from setuptools import setup, find_packages

import setuptools

if __name__ == "__main__":
    setuptools.setup(
        use_scm_version={'relative_to': os.path.dirname(__file__)}
    )