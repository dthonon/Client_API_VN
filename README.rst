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


Description
===========

Python applications that use Biolovision/VisioNature (VN) API to:

- download data from VN sites and stores it to a Postgresql database.
- update sightings directly in VN site

Applications are available either as:

- Python modules from PyPI
- Docker images from Docker Hub

They are tested under Linux Ubuntu >20 or Debian 10. Other Linux
distributions could work. Windows is not tested at all and will
probably not work.

See `Documentation <https://client-api-vn1.readthedocs.io/en/stable/>`_
for more informations.

A thin Python layer on top of Biolovision API is provided, as described in
`API Documentation <https://client-api-vn1.readthedocs.io/en/stable/api/modules.html>`_.

Installation - Python
---------------------

These instructions present the steps required to install the
Python applications.

Add the following debian packages::

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

Initialize the sample YAML file in your HOME directory and edit with
your local details. The YAML file is self documented::

    transfer_vn --init .evn_your_site.yaml
    editor $HOME/.evn_your_site.yaml

Create the database and tables::

    transfer_vn --db_create --json_tables_create --col_tables_create .evn_your_site.yaml

You can then download data, as enabled and filtered in the YAML file.
Beware that, depending on the volume of observations,
this can take several hours. We recommend starting with a small taxonomic
group first::

    transfer_vn --full .evn_your_site.yaml

After this full download, data can be updated. For observations, only new,
modified or deleted observations are downloaded. For other controlers, a full
download is always performed. Each controler runs on its own schedule,
defined in the YAML configuration file. This step needs to be performed
after each ``--full`` execution or YAML file modification. To create or update,
after modifying the configuration file, the schedule::

    transfer_vn --schedule .evn_your_site.yaml

Once this is done, you can update the database with new observations::

    transfer_vn --update .evn_your_site.yaml

This can be done by cron, every hour for example. At each run, all scheduled
tasks are performed. Note: you must wait until the first scheduled task has
expired for a transfer to be carried out. With the default schedule, you must
therefore wait for the next round hour ``--schedule``. It must run at least
once a week. The virtual environment must be activated in the cron job, for
example::

    0 * * * * echo 'source client_api_vn/env_VN/bin/activate;cd client_api_vn/;transfer_vn --update .evn_your_site.yaml --verbose'| /bin/bash > /dev/null


Getting Started - update_vn
---------------------------

Initialize the sample YAML file in your HOME directory and edit with
your local details. The YAML file is self documented::

    update_vn --init .evn_your_site.yaml
    editor $HOME/.evn_your_site.yaml


Prerequisites
-------------

For Linux and Postgresql installation, refer to
`server installation <https://client-api-vn1.readthedocs.io/en/stable/apps/server_install.html>`_.

Installation requires the following python module::

    pip

All other python dependencies are managed by pip install.

Command-line options - transfer_vn
----------------------------------

The application runs as::

    transfer_vn options config

where::

    options  command line options described below
    config   YAML file, located in $HOME directory, described in sample file

-h, --help             Prints help and exits
--version              Print version number
--verbose              Increase output verbosity
--quiet                Reduce output verbosity
--init                 Initialize the YAML configuration file
--db_drop              Delete if exists database and roles
--db_create            Create database and roles
--json_tables_create   Create or recreate json tables
--col_tables_create    Create or recreate colums based tables
--full                 Perform a full download
--update               Perform an incremental download
--schedule             Create or update the incremental update schedule
--status               Print downloading status (schedule, errors...)
--count                Count observations by site and taxo_group
--profile              Gather and print profiling times

Command-line options - update_vn
--------------------------------

The application runs as::

    update_vn options config input

where::

    options  command line options described below
    config   YAML file, located in $HOME directory, described in sample file
    input    CSV file listing sightings to be updated

-h, --help             Prints help and exits
--version              Print version number
--verbose              Increase output verbosity
--quiet                Reduce output verbosity
--init                 Initialize the YAML configuration file

CSV input file must contain the following columns:

- site, as defined in YAML site section
- id_universal of the sighting to modify
- path to the attribute to modify, in JSONPath syntax, unused if operation is delete_observation
- operation:
  - replace: add if not present or update a sighting attribute
  - delete_attribute: to keep the observation and remove the attribute with the given path
  - delete_observation, to remove completely the observation
- value: if operation is replace, new value inserted or updated

Note: each operation is logged in hidden_comment, as a JSON message.
It is not possible to replace hidden_comment, as logging is appended.

For example::

    site;id_universal;path;operation;value
    Isère;2246086;$['data']['sightings'][0]['observers'][0]['atlas_code'];replace;4
    Isère;2246086;$['data']['sightings'][0]['observers'][0]['atlas_code'];delete_attribute;
    Isère;2246086;;delete_observation;

