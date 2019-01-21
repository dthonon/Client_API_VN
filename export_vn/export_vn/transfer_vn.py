#!/usr/bin/env python3
"""
Program managing VisioNature export to Postgresql database


"""
import sys
import logging
import argparse
import json
import shutil
from pathlib import Path
import pyexpander.lib as pyexpander
import pyexpander.parser as pyparser
import subprocess

from export_vn.download_vn import DownloadVn, DownloadVnException
from export_vn.download_vn import Entities, LocalAdminUnits, Observations, Places
from export_vn.download_vn import Species, TaxoGroup, TerritorialUnits
from export_vn.store_postgresql import StorePostgresql
from export_vn.evnconf import EvnConf

# version of the program:
from setuptools_scm import get_version
version = get_version(root='../..', relative_to=__file__)

def main():
    """
    Main.
    """

    # Get options
    parser = argparse.ArgumentParser()
    parser.add_argument('--version',
                        help='print version number',
                        action='store_true')
    parser.add_argument('-v', '--verbose',
                        help='increase output verbosity',
                        action='store_true')
    parser.add_argument('-q', '--quiet',
                        help='reduce output verbosity',
                        action='store_true')
    parser.add_argument('--vn_tables',
                        help='create or recreate vn colums based tables',
                        action='store_true')
    parser.add_argument('--init',
                        help='Delete if exists and create database and roles',
                        action='store_true')
    parser.add_argument('file',
                        help='file name, used to select config file')

    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.DEBUG)
        SQL_QUIET=""
        CLIENT_MIN_MESSAGE="debug1"

    else:
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
        SQL_QUIET="--quiet"
        CLIENT_MIN_MESSAGE="warning"

    # Get configuration
    logging.info('Getting configuration data from %s', args.file)
    cfg_list = EvnConf(args.file).site_list

    if args.init:
        logging.info('Delete if exists and create database and roles')
        cfg = list(cfg_list.values())[0]
        db_cfg = {
            'db_host': cfg.db_host,
            'db_port': cfg.db_port,
            'db_name': cfg.db_name,
            'db_schema_import': cfg.db_schema_import,
            'db_schema_vn': cfg.db_schema_vn,
            'db_group': cfg.db_group,
            'db_user': cfg.db_user,
            'db_pw': cfg.db_pw
            }
        filename = str(Path.home()) + '/Client_API_VN/sql/init-db.sql'
        with open(filename, 'r') as myfile:
            template = myfile.read()
        (cmd, exp_globals) = pyexpander.expandToStr(template,
                                                    external_definitions=db_cfg)
        filename = str(Path.home()) + '/tmp/init-db.sql'
        with open(filename, 'w') as myfile:
            myfile.write(cmd)
        try:
            subprocess.run('env PGOPTIONS="-c client-min-messages=' + CLIENT_MIN_MESSAGE + '" psql ' + SQL_QUIET + ' --dbname=postgres --file=' + filename, check=True, shell=True)
        except subprocess.CalledProcessError as err:
            print('ERROR:', err)

    if args.vn_tables:
        logging.info('Creating or recreating vn colums based files')
        cfg = list(cfg_list.values())[0]
        db_cfg = {
            'db_host': cfg.db_host,
            'db_port': cfg.db_port,
            'db_name': cfg.db_name,
            'db_schema_import': cfg.db_schema_import,
            'db_schema_vn': cfg.db_schema_vn,
            'db_group': cfg.db_group,
            'db_user': cfg.db_user,
            'db_pw': cfg.db_pw
            }
        filename = str(Path.home()) + '/Client_API_VN/sql/create-vn-tables.sql'
        with open(filename, 'r') as myfile:
            template = myfile.read()
        (cmd, exp_globals) = pyexpander.expandToStr(template,
                                                    external_definitions=db_cfg)
        filename = str(Path.home()) + '/tmp/create-vn-tables.sql'
        with open(filename, 'w') as myfile:
            myfile.write(cmd)
        try:
            subprocess.run('env PGOPTIONS="-c client-min-messages=' + CLIENT_MIN_MESSAGE + '" psql ' + SQL_QUIET + ' --dbname=' + cfg.db_name + ' --file=' + filename, check=True, shell=True)
        except subprocess.CalledProcessError as err:
            print('ERROR:', err)


    # Looping on sites
    for site, cfg in cfg_list.items():
        if cfg.enabled:
            logging.info('Working on site %s', site)

            store_pg = StorePostgresql(cfg)
            entities = Entities(cfg, store_pg.store)
            local_admin_units = LocalAdminUnits(cfg, store_pg.store)
            observations = Observations(cfg, store_pg.store)
            places = Places(cfg, store_pg.store)
            species = Species(cfg, store_pg.store)
            taxo_group = TaxoGroup(cfg, store_pg.store)
            territorial_unit = TerritorialUnits(cfg, store_pg.store)

            taxo_group.store()
            species.store()

            entities.store()

            territorial_unit.store()
            local_admin_units.store()
            places.store()

            observations.store()

        else:
            logging.info('Skipping site %s', site)

# Main wrapper
if __name__ == "__main__":
    main()
