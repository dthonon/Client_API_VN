=============
Client_API_VN
=============

Python application that transfers data from Biolovision/VisoNature
web sites and stores them to a Postgresql database.

Description
===========

Getting Started
---------------

Create a python virtual environment, activate it and update basic tools::

    python3 -m venv VN_env
    source VN_env/bin/activate
    python -m pip install --upgrade pip

Install from PyPI::

    pip install Client-API-VN

Initialize the sample YAML file in your HOME directory and edit with
your local details::

    transfer_vn --init .evn_your_site.yaml
    editor $HOME/.evn_your_site.yaml


You can then download data, as enabled in the YAML file.
Beware that, depending on the volume of observations,
this can take hours. We recommend starting with a small taxonomic group first::

    transfer_vn --db-create --json_tables_create --col_tables_create --full .evn_your_site.yaml


Once this is done, you can update the database with new observations::

    transfer_vn --update .evn_your_site.yaml

Note: this script should run hourly or dayly in a cron job.
It must run at least every week.

Prerequisites
-------------

Installation requires the following python module
* pip

All other dependencies are managed by pip install.

Running the application
-----------------------

The application runs as::

    transfer_vn  options file

where:
- options  command line options described below
- file     YAML file, located in $HOME directory, described in sample file

Command-line options
--------------------

-h, --help             Affiche l'aide et termine
--version              Affiche la version
-v, --verbose          Plus verbeux
-q, --quiet            Moins verbeux
--db_drop              Détruit la base de données et les rôles
--db_create            Crée la base de données et les rôle
--json_tables_create   Crée, si elles n'existent pas, les tables JSON
--col_tables_create    Crée ou recrée les tables en colonne
--full                 Réalise un téléchargement complet
--update               Réalise un téléchargement incrémental
--count                Statistiques des observations par site


Note
====

This project has been set up using PyScaffold 3.1. For details and usage
information on PyScaffold see https://pyscaffold.org/.
