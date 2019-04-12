#!/usr/bin/env python3
"""Setup for export_vn package.
"""
from setuptools import setup, find_packages

with open("../README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="export_vn",
    packages=find_packages(),
    include_package_data=True,

    use_scm_version={'root': '..', 'relative_to': __file__},
    setup_requires=['setuptools_scm'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires=[
        'beautifulsoup4>=4.5',
        'pyexpander>=1.8'
        'pyproj>=1.9',
        'requests>=2.12',
        'requests-oauthlib>=0.7',
        'SQLAlchemy>=1.0',
        'tabulate>=0.7',
        'xmltodict>=0.10'
    ],

    package_data={
     },

    # metadata to display on PyPI
    author="Daniel Thonon",
    author_email="d.thonon9@gmail.com",
    description="Transfer data from VisioNature web site to Postgresql database",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GPL",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL",
        "Operating System :: OS Independent",
    ],
)
