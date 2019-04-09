#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup for export_vn package.
"""
from setuptools import find_packages, setup
from setuptools_scm import get_version

setup_requires = []
install_requires = [
    'docutils>=0.3'
    "requests",
]
test_requires = [
    "pytest",
    "pylint",
    "coverage",
    "setuptools_scm",
    "pytest-pylint",
    "pytest-cov",
]
docs_requires = [
    "sphinx"
]
dev_requires = docs_requires + test_requires

setup(
    name="export_vn",
    python_requires=">=3.6",

    setup_requires=setup_requires,
    install_requires=install_requires,

    use_scm_version={'root': '..', 'relative_to': __file__},
    version=get_version(root='..', relative_to=__file__),

    packages=find_packages(),
    include_package_data=True,
    extras_require={"docs": docs_requires,
                    "tests": test_requires,
                    "dev": dev_requires},

    package_data={
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst'],
        # And include any *.msg files too:
        'export_vn': ['*.msg'],
    },

    # metadata to display on PyPI
    author="Daniel Thonon",
    author_email="d.thonon9@gmail.com",
    description="Download data from VisioNature and store to postgresql database",
    license="GPL",

    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: Debian 9',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
    ],
)
