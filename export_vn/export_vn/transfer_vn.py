#!/usr/bin/env python3
"""
Program managing VisioNature export to Postgresql database


"""
import logging
import argparse
import subprocess
from pathlib import Path
import pyexpander.lib as pyexpander
import pyexpander.parser as pyparser
from setuptools_scm import get_version

from export_vn.download_vn import DownloadVn, DownloadVnException
from export_vn.download_vn import Entities, LocalAdminUnits, Observations, Places
from export_vn.download_vn import Species, TaxoGroup, TerritorialUnits
from export_vn.store_postgresql import StorePostgresql
from export_vn.evnconf import EvnConf
from export_vn.biolovision_api import TaxoGroupsAPI

# version of the program:
version = get_version(root='../..', relative_to=__file__)

def db_config(cfg):
    """Return database related parameters."""
    return {
        'db_host': cfg.db_host,
        'db_port': cfg.db_port,
        'db_name': cfg.db_name,
        'db_schema_import': cfg.db_schema_import,
        'db_schema_vn': cfg.db_schema_vn,
        'db_group': cfg.db_group,
        'db_user': cfg.db_user,
        'db_pw': cfg.db_pw
        }

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
        sql_quiet = ""
        client_min_message = "debug1"

    else:
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
        sql_quiet = "--quiet"
        client_min_message = "warning"

    # Get configuration
    logging.info('Getting configuration data from %s', args.file)
    cfg = EvnConf(args.file)
    cfg_crtl_list = cfg.ctrl_list
    cfg_site_list = cfg.site_list

    if args.init:
        logging.info('Delete if exists and create database and roles')
        cfg = list(cfg_site_list.values())[0]
        db_cfg = db_config(cfg)
        filename = str(Path.home()) + '/Client_API_VN/sql/init-db.sql'
        with open(filename, 'r') as myfile:
            template = myfile.read()
        (cmd, exp_globals) = pyexpander.expandToStr(template,
                                                    external_definitions=db_cfg)
        filename = str(Path.home()) + '/tmp/init-db.sql'
        with open(filename, 'w') as myfile:
            myfile.write(cmd)
        try:
            subprocess.run('env PGOPTIONS="-c client-min-messages=' + client_min_message +
                           '" psql ' + sql_quiet + ' --dbname=postgres --file=' + filename,
                           check=True, shell=True)
        except subprocess.CalledProcessError as err:
            logging.error(err)

    if args.vn_tables:
        logging.info('Creating or recreating vn colums based files')
        cfg = list(cfg_site_list.values())[0]
        db_cfg = db_config(cfg)
        filename = str(Path.home()) + '/Client_API_VN/sql/create-vn-tables.sql'
        with open(filename, 'r') as myfile:
            template = myfile.read()
        (cmd, exp_globals) = pyexpander.expandToStr(template,
                                                    external_definitions=db_cfg)
        filename = str(Path.home()) + '/tmp/create-vn-tables.sql'
        with open(filename, 'w') as myfile:
            myfile.write(cmd)
        try:
            subprocess.run('env PGOPTIONS="-c client-min-messages=' + client_min_message +
                           '" psql ' + sql_quiet + ' --dbname=' + cfg.db_name +
                           ' --file=' + filename,
                           check=True, shell=True)
        except subprocess.CalledProcessError as err:
            logging.error(err)

    # Looping on sites
    for site, cfg in cfg_site_list.items():
        if cfg.enabled:
            logging.info('Working on site %s', site)

            store_pg = StorePostgresql(cfg)

            ctrl = 'entities'
            if cfg_crtl_list[ctrl].enabled:
                logging.info('Using controler %s', ctrl)
                entities = Entities(cfg, store_pg.store)
                entities.store()

            ctrl = 'territorial_unit'
            if cfg_crtl_list[ctrl].enabled:
                logging.info('Using controler %s', ctrl)
                territorial_unit = TerritorialUnits(cfg, store_pg.store)
                territorial_unit.store()

            ctrl = 'local_admin_units'
            if cfg_crtl_list[ctrl].enabled:
                logging.info('Using controler %s', ctrl)
                local_admin_units = LocalAdminUnits(cfg, store_pg.store)
                local_admin_units.store()

            ctrl = 'places'
            if cfg_crtl_list[ctrl].enabled:
                logging.info('Using controler %s', ctrl)
                places = Places(cfg, store_pg.store)
                places.store()

            ctrl = 'taxo_group'
            if cfg_crtl_list[ctrl].enabled:
                logging.info('Using controler %s', ctrl)
                taxo_group = TaxoGroup(cfg, store_pg.store)
                taxo_group.store()

            ctrl = 'species'
            if cfg_crtl_list[ctrl].enabled:
                logging.info('Using controler %s', ctrl)
                species = Species(cfg, store_pg.store)
                species.store()

            ctrl = 'observations'
            if cfg_crtl_list[ctrl].enabled:
                logging.info('Using controler %s', ctrl)
                observations = Observations(cfg, store_pg.store)
                taxo_groups = TaxoGroupsAPI(cfg).api_list()['data']
                taxo_groups_ex = cfg_crtl_list[ctrl].taxo_exclude
                logging.info('Excluded taxo_groups: %s', taxo_groups_ex)
                taxo_groups_filt = []
                for taxo in taxo_groups:
                    if (not taxo['name_constant'] in taxo_groups_ex) and (taxo['access_mode'] != 'none'):
                        taxo_groups_filt.append(taxo['id'])
                logging.info('Downloading from taxo_groups: %s', taxo_groups_filt)
                observations.store(taxo_groups_filt)

        else:
            logging.info('Skipping site %s', site)

# Main wrapper
if __name__ == "__main__":
    main()
