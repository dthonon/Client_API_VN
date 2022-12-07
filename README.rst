=============
Client_API_VN
=============

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
.. image:: https://img.shields.io/pypi/status/Client-API-VN
    :alt: PyPI - Status
.. image:: https://img.shields.io/pypi/pyversions/Client-API-VN
    :alt: PyPI - Python Version
.. image:: https://img.shields.io/pypi/l/Client-API-VN
    :alt: PyPI - License
.. image:: https://codecov.io/gh/dthonon/Client_API_VN/branch/develop/graph/badge.svg
    :target: https://codecov.io/gh/dthonon/Client_API_VN


Presentation
============

Python applications that use Biolovision/VisioNature (VN) API to:

- download data from VN sites and stores it to a Postgresql database.
- update sightings directly in VN site

Applications are available either as:

- Python modules from PyPI
- Docker images from Docker Hub

They are tested under Linux Ubuntu >20 or Debian 10. Other Linux
distributions could work. Windows is not tested at all and will
probably not work.

See `Documentation <https://client-api-vn.readthedocs.io/en/stable/>`_
for more informations.

A thin Python layer on top of Biolovision API is provided, as described in
`API Manual <https://client-api-vn.readthedocs.io/en/stable/api/modules.html>`_.

Installation - Python
---------------------

These instructions present the steps required to install the
Python applications.

Windows:

    Install Python from Microsoft store
    
    Add python script directory to Path, as described in
    `How to add Python to Windows PATH <https://datatofish.com/add-python-to-windows-path/>`_.

Linux: add the following debian packages::

    sudo apt -y install build-essential python3-dev python3-venv

Create a python virtual environment, activate it and update basic tools::

    python3 -m venv env_VN
    source env_VN/bin/activate
    python -m pip install --upgrade pip

Install from PyPI::

    pip install Client-API-VN

Installation - Docker
---------------------

These instructions present the steps required to install the
Docker applications::

    docker pull dthonon/client-api-vn
    docker run --name xfer_vn \
               --mount source=xfer_vn,target=/root \
               --workdir /root \
               --tty --interactive \
               dthonon/client-api-vn bash

The following steps are the common to both Python and Docker installation.

Getting Started - transfer_vn
-----------------------------

See `Documentation <https://client-api-vn.readthedocs.io/en/latest/apps/transfer_vn.html>`__
for more informations.


Getting Started - update_vn
---------------------------

See `Documentation <https://client-api-vn.readthedocs.io/en/latest/apps/update_vn.html>`__
for more informations.


Prerequisites
-------------

For Linux and Postgresql installation, refer to
`Server installation <https://client-api-vn.readthedocs.io/en/latest/apps/server_install.html>`_.

Installation requires the following python module::

    pip

All other python dependencies are managed by pip install.


