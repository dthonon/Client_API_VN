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
from export_vn.store_postgresql import StorePostgresql, PostgresqlUtils
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

def arguments():
    """Define and parse command arguments."""
    # Get options
    parser = argparse.ArgumentParser()
    parser.add_argument('--version',
                        help='Print version number',
                        action='store_true')
    parser.add_argument('-v', '--verbose',
                        help='Increase output verbosity',
                        action='store_true')
    parser.add_argument('-q', '--quiet',
                        help='Reduce output verbosity',
                        action='store_true')
    parser.add_argument('--db_drop',
                        help='Delete if exists database and roles',
                        action='store_true')
    parser.add_argument('--db_create',
                        help='Create database and roles',
                        action='store_true')
    parser.add_argument('--json_tables_create',
                        help='Create or recreate json tables',
                        action='store_true')
    parser.add_argument('--col_tables_create',
                        help='Create or recreate colums based tables',
                        action='store_true')
    parser.add_argument('--full',
                        help='Perform a full download, according to configuration file',
                        action='store_true')
    parser.add_argument('--update',
                        help='Perform an incremental download, according to configuration file',
                        action='store_true')
    parser.add_argument('file',
                        help='Configuration file name, used to configure different processing')

    return parser.parse_args()

def full_download(cfg_ctrl):
    """Performs a full download of all sites and controlers, based on configuration file."""
    cfg_crtl_list = cfg_ctrl.ctrl_list
    cfg_site_list = cfg_ctrl.site_list
    cfg = list(cfg_site_list.values())[0]
    # Looping on sites
    for site, cfg in cfg_site_list.items():
        with StorePostgresql(cfg) as store_pg:
            if cfg.enabled:
                logging.info('Working on site %s', cfg.site)

                ctrl = 'entities'
                if cfg_crtl_list[ctrl].enabled:
                    logging.info('Using controler %s on site %s', ctrl, cfg.site)
                    entities = Entities(cfg, store_pg)
                    entities.store()

                ctrl = 'territorial_unit'
                if cfg_crtl_list[ctrl].enabled:
                    logging.info('Using controler %s on site %s', ctrl, cfg.site)
                    territorial_unit = TerritorialUnits(cfg, store_pg)
                    territorial_unit.store()

                ctrl = 'local_admin_units'
                if cfg_crtl_list[ctrl].enabled:
                    logging.info('Using controler %s on site %s', ctrl, cfg.site)
                    local_admin_units = LocalAdminUnits(cfg, store_pg)
                    local_admin_units.store()

                ctrl = 'places'
                if cfg_crtl_list[ctrl].enabled:
                    logging.info('Using controler %s on site %s', ctrl, cfg.site)
                    places = Places(cfg, store_pg)
                    places.store()

                ctrl = 'taxo_group'
                if cfg_crtl_list[ctrl].enabled:
                    logging.info('Using controler %s on site %s', ctrl, cfg.site)
                    taxo_group = TaxoGroup(cfg, store_pg)
                    taxo_group.store()

                ctrl = 'species'
                if cfg_crtl_list[ctrl].enabled:
                    logging.info('Using controler %s on site %s', ctrl, cfg.site)
                    species = Species(cfg, store_pg)
                    species.store()

                ctrl = 'observations'
                if cfg_crtl_list[ctrl].enabled:
                    logging.info('Using controler %s on site %s', ctrl, cfg.site)
                    observations = Observations(cfg, store_pg)
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

    return None

def increment_download(cfg_ctrl):
    """Performs an incremental download of observations from all sites and controlers, based on configuration file."""
    cfg_crtl_list = cfg_ctrl.ctrl_list
    cfg_site_list = cfg_ctrl.site_list
    cfg = list(cfg_site_list.values())[0]
    # Looping on sites
    for site, cfg in cfg_site_list.items():
        with StorePostgresql(cfg) as store_pg:
            if cfg.enabled:
                logging.info('Working on site %s', site)

                ctrl = 'observations'
                if cfg_crtl_list[ctrl].enabled:
                    logging.info('Using controler %s', ctrl)
                    observations = Observations(cfg, store_pg)
                    taxo_groups = TaxoGroupsAPI(cfg).api_list()['data']
                    taxo_groups_ex = cfg_crtl_list[ctrl].taxo_exclude
                    logging.info('Excluded taxo_groups: %s', taxo_groups_ex)
                    taxo_groups_filt = []
                    for taxo in taxo_groups:
                        if (not taxo['name_constant'] in taxo_groups_ex) and (taxo['access_mode'] != 'none'):
                            taxo_groups_filt.append(taxo['id'])
                    logging.info('Downloading from taxo_groups: %s', taxo_groups_filt)
                    observations.update(taxo_groups_filt)

            else:
                logging.info('Skipping site %s', site)

    return None

def main():
    """
    Main.
    """
    # Get command line arguments
    args = arguments()
    # Define verbosity
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

    # Get configuration from file
    logging.info('Getting configuration data from %s', args.file)
    cfg_ctrl = EvnConf(args.file)
    cfg_site_list = cfg_ctrl.site_list
    cfg = list(cfg_site_list.values())[0]

    manage_pg = PostgresqlUtils(cfg)
    db_cfg = db_config(cfg)
    if args.db_drop:
        logging.info('Delete if exists database and roles')
        manage_pg.drop_database()
        # Force tables creation and full download, even if not in args list
        args.db_create = True
        args.json_tables = True
        args.col_tables = True
        args.full = True

    if args.db_create:
        logging.info('Create database and roles')
        manage_pg.create_database()
        # Force tables creation and full download, even if not in args list
        args.json_tables = True
        args.col_tables = True
        args.full = True

    if args.json_tables:
        logging.info('Delete if exists and create json tables')
        manage_pg.create_json_tables()
        # Force tables creation and full download, even if not in args list
        args.col_tables = True
        args.full = True

    if args.col_tables:
        logging.info('Creating or recreating vn colums based files')
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

    if args.full:
        logging.info('Performing a full download')
        full_download(cfg_ctrl)

    if args.update:
        logging.info('Performing an incremental download of observations')
        increment_download(cfg_ctrl)

# Main wrapper
if __name__ == "__main__":
    main()
