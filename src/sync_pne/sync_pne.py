#!/usr/bin/env python3
"""
Synchronize Parc National de Ecrins database to faune-xxx.


"""
import argparse
import csv
import json
import logging
import shutil
import subprocess
import sys
import urllib
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import pkg_resources
import requests
from biolovision.api import ObservationsAPI
from export_vn.evnconf import EvnConf
from strictyaml import YAMLValidationError

import petl as etl
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    create_engine,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, insert
from sqlalchemy.engine.url import URL
from sqlalchemy.sql import and_

from . import _, __version__

APP_NAME = "sync_pne"

logger = logging.getLogger(APP_NAME)


def arguments(args):
    """Define and parse command arguments.

    Args:
        args ([str]): command line parameters as list of strings

    Returns:
        :obj:`argparse.Namespace`: command line parameters namespace
    """
    # Get options
    parser = argparse.ArgumentParser(
        description="Sample Biolovision API client application."
    )
    parser.add_argument(
        "--version",
        help=_("Print version number"),
        action="version",
        version="%(prog)s {version}".format(version=__version__),
    )
    out_group = parser.add_mutually_exclusive_group()
    out_group.add_argument(
        "--verbose", help=_("Increase output verbosity"), action="store_true"
    )
    out_group.add_argument(
        "--quiet", help=_("Reduce output verbosity"), action="store_true"
    )
    parser.add_argument(
        "--init", help=_("Initialize the YAML configuration file"), action="store_true"
    )
    parser.add_argument("config", help=_("Configuration file name"))
    download_group = parser.add_mutually_exclusive_group()
    download_group.add_argument(
        "--full", help=_("Perform a full synchronisation"), action="store_true"
    )
    download_group.add_argument(
        "--update",
        help=_("Perform an incremental synchronisation"),
        action="store_true",
    )

    return parser.parse_args(args)


def init(config: str):
    """Copy template YAML file to home directory."""
    logger = logging.getLogger(APP_NAME + ".init")
    yaml_src = pkg_resources.resource_filename(__name__, "data/evn_template.yaml")
    yaml_dst = str(Path.home() / config)
    logger.info(_("Creating YAML configuration file %s, from %s"), yaml_dst, yaml_src)
    shutil.copyfile(yaml_src, yaml_dst)
    logger.info(_("Please edit %s before running the script"), yaml_dst)


def fetch_data(cfg_ctrl):
    """Download dataset from PNE site."""
    logger = logging.getLogger(APP_NAME + ".fetch_data")
    cfg_site_list = cfg_ctrl.site_list
    cfg = list(cfg_site_list.values())[0]

    logger.info(_("Downloading data from %s"), cfg.pne_data_url)
    try:
        subprocess.run(
            "curl -o $HOME/tmp/pne.zip " + cfg.pne_data_url + "?id=1",
            check=True,
            shell=True,
        )
        subprocess.run(
            "unzip -p $HOME/tmp/pne.zip > $HOME/tmp/pne.csv", check=True, shell=True
        )

    except subprocess.CalledProcessError as err:
        logger.error(err)


def _create_table(cfg, metadata, db, name, *cols):
    """Check if table exists, and create it if not

    Parameters
    ----------
    cfg : dict
        configuration parameters
    metadata :
        sqlalchemy metadata
    db :
        sqlalchemy database engine
    name : str
        Table name.
    cols : list
        Data returned from API call.

    """
    if (cfg.pne_db_schema + "." + name) not in metadata.tables:
        logger.info(_("Table %s not found => Creating it"), name)
        table = Table(name, metadata, *cols)
        table.create(db)
    else:
        logger.info(_("Table %s already exists => Keeping it"), name)
    return None


def store_data(cfg_ctrl):
    """Store PNE data in Postgresql table."""
    logger = logging.getLogger(APP_NAME + ".fetch_data")
    cfg_site_list = cfg_ctrl.site_list
    cfg = list(cfg_site_list.values())[0]
    logger.info(_("Storing data to %s"), "tbd")
    # Initialize interface to Postgresql DB
    db_url = {
        "drivername": "postgresql+psycopg2",
        "username": cfg.db_user,
        "password": cfg.db_pw,
        "host": cfg.db_host,
        "port": cfg.db_port,
        "database": cfg.db_name,
    }
    # Connect to database
    logger.info(_("Connecting to %s database"), cfg.db_name)
    db = create_engine(URL(**db_url), echo=False)
    conn = db.connect()
    # Create import schema
    text = "CREATE SCHEMA IF NOT EXISTS {} AUTHORIZATION {}".format(
        cfg.pne_db_schema, cfg.db_group
    )
    conn.execute(text)
    # Drop input table, if exists
    text = "DROP TABLE IF EXISTS {}.{}".format(cfg.pne_db_schema, cfg.pne_db_in_table)
    conn.execute(text)
    # Set path to include PNE import schema
    dbschema = cfg.pne_db_schema
    metadata = MetaData(schema=dbschema)
    metadata.reflect(db)

    # Check if tables exist or else create them
    _create_table(
        cfg,
        metadata,
        db,
        cfg.pne_db_in_table,
        Column("id_synthese", Integer, nullable=False, index=True),
        Column("nom_lot", String, nullable=False, index=True),
        Column("protocole_new", String, nullable=False, index=True),
        Column("protocole_old", String, nullable=False, index=True),
        Column("nom_precision", String, nullable=False, index=True),
        Column("cd_nom", Integer, nullable=False, index=True),
        Column("nom_latin", String, nullable=False, index=True),
        Column("nom_francais", String, nullable=False, index=True),
        Column("insee", Integer, nullable=False, index=True),
        Column("dateobs", DateTime, nullable=False, index=True),
        Column("observateurs", String, nullable=False, index=True),
        Column("altitude", Integer, nullable=False, index=True),
        Column("critere", String, nullable=False, index=True),
        Column("effectif_total", String, nullable=False, index=True),
        Column("remarques", String, nullable=False, index=True),
        Column("derniere_action", String, nullable=False, index=True),
        Column("date_insert", DateTime, nullable=False, index=True),
        Column("date_update", DateTime, nullable=False, index=True),
        Column("supprime", String, nullable=False, index=True),
        Column("x", Integer, nullable=False, index=True),
        Column("y", Integer, nullable=False, index=True),
        PrimaryKeyConstraint("id_synthese"),
    )

    # Open CSV file stream
    tbl_0 = etl.fromcsv("../tmp/pne.csv", encoding="latin_1", delimiter=";")
    logger.debug(tbl_0)
    # Sort for faster deduplication
    tbl_1 = etl.head(tbl_0, 1000)
    tbl_2 = etl.sort(tbl_1, key="id_synthese")
    # Print and remove conflicting rows
    tbl_3 = etl.conflicts(tbl_2, "id_synthese", presorted=True)
    nb_dup = etl.nrows(tbl_3)
    if nb_dup > 0:
        dup_file = "../tmp/pne_conflicts.csv"
        logger.error(_("Input data contains %s conflicting rows. See %s"), nb_dup, dup_file)
        etl.tocsv(tbl_3, dup_file)
    tbl_f = etl.unique(tbl_2, key="id_synthese", presorted=True)
    # Push to database
    etl.todb(tbl_f, conn, cfg.pne_db_in_table, schema=cfg.pne_db_schema)

    conn.close()
    db.dispose()


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    # Create $HOME/tmp directory if it does not exist
    (Path.home() / "tmp").mkdir(exist_ok=True)

    # Define logger format and handlers
    logger = logging.getLogger(APP_NAME)
    # create file handler which logs even debug messages
    fh = TimedRotatingFileHandler(
        str(Path.home()) + "/tmp/" + APP_NAME + ".log",
        when="midnight",
        interval=1,
        backupCount=100,
    )
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    # Get command line arguments
    args = arguments(args)

    # Define verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.info(_("%s, version %s"), sys.argv[0], __version__)
    logger.info(_("Arguments: %s"), sys.argv[1:])

    # If required, first create YAML file
    if args.init:
        logger.info(_("Creating YAML configuration file"))
        init(args.config)
        return None

    # Get configuration from file
    if not (Path.home() / args.config).is_file():
        logger.critical(
            _("Configuration file %s does not exist"), str(Path.home() / args.config)
        )
        return None
    logger.info(_("Getting configuration data from %s"), args.config)
    try:
        cfg_ctrl = EvnConf(args.config)
    except YAMLValidationError as error:
        logger.critical(_("Incorrect content in YAML configuration %s"), args.config)
        sys.exit(0)

    # # Fetch data from PNE site and store to file
    # fetch_data(cfg_ctrl)

    # Store data to Postgresql database
    store_data(cfg_ctrl)

    return None


def run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


# Main wrapper
if __name__ == "__main__":
    run()
