#!/usr/bin/env python3
"""Setup for export_vn package.
"""
from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='export_vn',
    packages=find_packages(),
    include_package_data=True,

    use_scm_version={'root': '.', 'relative_to': __file__},
    setup_requires=['setuptools_scm'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires=[
        'docutils',
        'beautifulsoup4',
        'psycopg2-binary',
        'pyexpander',
        'pyproj',
        'pyYAML',
        'requests',
        'requests-oauthlib',
        'setuptools_scm',
        'SQLAlchemy',
        'tabulate',
        'xmltodict'
    ],

    package_data={
     },

    # metadata to display on PyPI
    author='Daniel Thonon',
    author_email='d.thonon9@gmail.com',
    description='Transfer data from VisioNature web site to Postgresql database',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://framagit.org/lpo/Client_API_VN',
    license="GPL v3",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX :: Linux",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Topic :: Scientific/Engineering :: Bio-Informatics"
    ]
)
