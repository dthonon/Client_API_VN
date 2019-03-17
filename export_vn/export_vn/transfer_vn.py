#!/usr/bin/env python3
"""
Program managing VisioNature export to Postgresql database


"""
import argparse
import logging
import subprocess
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from setuptools_scm import get_version
from tabulate import tabulate

import pyexpander.lib as pyexpander
from export_vn.biolovision_api import TaxoGroupsAPI
from export_vn.download_vn import (Entities, LocalAdminUnits, Observations,
                                   Places, Species, TaxoGroup,
                                   TerritorialUnits)
from export_vn.evnconf import EvnConf
from export_vn.store_postgresql import PostgresqlUtils, StorePostgresql

# version of the program:
__version__ = get_version(root='../..', relative_to=__file__)


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
                        action='version',
                        version='%(prog)s {version}'.
                        format(version=__version__))
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
                        help='Perform a full download',
                        action='store_true')
    parser.add_argument('--update',
                        help='Perform an incremental download',
                        action='store_true')
    parser.add_argument('--count',
                        help='Count observations by site and taxo_group',
                        action='store_true')
    parser.add_argument('file',
                        help='Configuration file name')

    args = parser.parse_args()
    return args


def full_download(cfg_ctrl):
    """Performs a full download of all sites and controlers,
       based on configuration file."""
    cfg_crtl_list = cfg_ctrl.ctrl_list
    cfg_site_list = cfg_ctrl.site_list
    cfg = list(cfg_site_list.values())[0]
    # Looping on sites
    for site, cfg in cfg_site_list.items():
        with StorePostgresql(cfg) as store_pg:
            if cfg.enabled:
                logging.info('Working on site %s', cfg.site)

                ctrl = 'taxo_group'
                if cfg_crtl_list[ctrl].enabled:
                    logging.info('Using controler %s on site %s',
                                 ctrl, cfg.site)
                    taxo_group = TaxoGroup(cfg, store_pg)
                    taxo_group.store()

                ctrl = 'observations'
                if cfg_crtl_list[ctrl].enabled:
                    logging.info('Using controler %s on site %s',
                                 ctrl, cfg.site)
                    observations = Observations(cfg, store_pg)
                    taxo_groups = TaxoGroupsAPI(cfg).api_list()['data']
                    taxo_groups_ex = cfg_crtl_list[ctrl].taxo_exclude
                    logging.info('Excluded taxo_groups: %s', taxo_groups_ex)
                    taxo_groups_filt = []
                    for taxo in taxo_groups:
                        if (not taxo['name_constant'] in taxo_groups_ex) \
                                and (taxo['access_mode'] != 'none'):
                            taxo_groups_filt.append(taxo['id'])
                    logging.info(
                        'Downloading from taxo_groups: %s', taxo_groups_filt)
                    observations.store(
                        taxo_groups_filt, method='search', by_specie=False)

                ctrl = 'entities'
                if cfg_crtl_list[ctrl].enabled:
                    logging.info('Using controler %s on site %s',
                                 ctrl, cfg.site)
                    entities = Entities(cfg, store_pg)
                    entities.store()

                ctrl = 'territorial_unit'
                if cfg_crtl_list[ctrl].enabled:
                    logging.info('Using controler %s on site %s',
                                 ctrl, cfg.site)
                    territorial_unit = TerritorialUnits(cfg, store_pg)
                    territorial_unit.store()

                ctrl = 'local_admin_units'
                if cfg_crtl_list[ctrl].enabled:
                    logging.info('Using controler %s on site %s',
                                 ctrl, cfg.site)
                    local_admin_units = LocalAdminUnits(cfg, store_pg)
                    local_admin_units.store()

                ctrl = 'places'
                if cfg_crtl_list[ctrl].enabled:
                    logging.info('Using controler %s on site %s',
                                 ctrl, cfg.site)
                    places = Places(cfg, store_pg)
                    places.store()

                ctrl = 'species'
                if cfg_crtl_list[ctrl].enabled:
                    logging.info('Using controler %s on site %s',
                                 ctrl, cfg.site)
                    species = Species(cfg, store_pg)
                    species.store()

            else:
                logging.info('Skipping site %s', site)

    return None


def increment_download(cfg_ctrl):
    """Performs an incremental download of observations from all sites and controlers,
    based on configuration file."""
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
                        if (not taxo['name_constant'] in taxo_groups_ex)\
                                and (taxo['access_mode'] != 'none'):
                            taxo_groups_filt.append(taxo['id'])
                    logging.info(
                        'Downloading from taxo_groups: %s', taxo_groups_filt)
                    observations.update(taxo_groups_filt)

            else:
                logging.info('Skipping site %s', site)

    return None


def count_observations(cfg_ctrl):
    """Count observations by site and taxo_group."""
    cfg_site_list = cfg_ctrl.site_list

    col_counts = None
    for site, cfg in cfg_site_list.items():
        if cfg.site == 'Haute-Savoie':
            continue

        if col_counts is None:
            manage_pg = PostgresqlUtils(cfg)
            # print(tabulate(manage_pg.count_json_obs()))
            col_counts = manage_pg.count_col_obs()

        url = cfg.base_url + 'index.php?m_id=23'
        logging.info('Getting counts from %s', url)
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')

        counts = soup.find_all('table')[2].contents[1].contents[3]
        rows = counts.contents[5].contents[0].contents[0].contents[1:-1]
        site_counts = list()
        for i in range(0, len(rows)):
            if i % 5 == 0:
                taxo = rows[i].contents[0]['title']
            elif i % 5 == 4:
                col_c = 0
                for r in col_counts:
                    if r[0] == site and r[2] == taxo:
                        col_c = r[3]
                site_counts.append([cfg.site,
                                    taxo,
                                    int(rows[i].contents[0].contents[0].replace(
                                        ' ', '')),
                                    col_c])
        print(tabulate(site_counts,
                       headers=['Site', 'TaxoName',
                                'Remote count', 'Local count'],
                       tablefmt='psql'))

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

    logging.info('%s, version %s', sys.argv[0], __version__)
    logging.info('Arguments: %s', sys.argv[1:])

    # Get configuration from file
    if not Path(str(Path.home()) + '/' + args.file).is_file():
        logging.critical('File %s does not exist',
                         str(Path.home()) + '/' + args.file)
        return None

    logging.info('Getting configuration data from %s', args.file)
    cfg_ctrl = EvnConf(args.file)
    cfg_site_list = cfg_ctrl.site_list
    cfg = list(cfg_site_list.values())[0]

    manage_pg = PostgresqlUtils(cfg)
    db_cfg = db_config(cfg)
    if args.db_drop:
        logging.info('Delete if exists database and roles')
        manage_pg.drop_database()

    if args.db_create:
        logging.info('Create database and roles')
        manage_pg.create_database()

    if args.json_tables_create:
        logging.info('Create, if not exists, json tables')
        manage_pg.create_json_tables()

    if args.col_tables_create:
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
            subprocess.run('env PGOPTIONS="-c client-min-messages=' +
                           client_min_message +
                           '" psql ' + sql_quiet + ' --dbname=' + 
                           cfg.db_name +
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

    if args.count:
        logging.info('Counting observations')
        count_observations(cfg_ctrl)

    return None


# Main wrapper
if __name__ == '__main__':
    main()
