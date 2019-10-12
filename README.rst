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

Python application that transfers data from Biolovision/VisoNature
web sites and stores them to a Postgresql database.

Description
===========

Getting Started
---------------

Installation - Python
---------------------

These instructions present the steps required to install the
Python application.

Create a python virtual environment, activate it and update basic tools::

    python3 -m venv VN_env
    source VN_env/bin/activate
    python -m pip install --upgrade pip

Install from PyPI::

    pip install Client-API-VN

Installation - Docker
---------------------

These instructions present the steps required to install the
Docker application::

    docker pull dthonon/client-api-vn
    docker run --name xfer_vn \
               --mount source=xfer_vn,target=/root \
               --workdir /root \
               --tty --interactive \
               dthonon/client-api-vn bash

Getting Started - Common
------------------------

The following steps are the common to both Python and Docker installation.

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
defined in the YAML configuration file. To create or update, after
modifying the configuration file, the schedule::

    transfer_vn --schedule .evn_your_site.yaml

Once this is done, you can update the database with new observations::

    transfer_vn --update .evn_your_site.yaml

Note: this script should run hourly or dayly in a cron job.
It must run at least every week.


Prerequisites
-------------

Installation requires the following python module::

    pip

All other dependencies are managed by pip install.

Running the application
-----------------------

The application runs as::

    transfer_vn options file

where:

- options  command line options described below
- file     YAML file, located in $HOME directory, described in sample file

Command-line options
--------------------

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


Note
====

This project has been set up using PyScaffold 3.1. For details and usage
information on PyScaffold see https://pyscaffold.org/.
