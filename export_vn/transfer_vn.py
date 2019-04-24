#!/usr/bin/env python3
"""
Program managing VisioNature export to Postgresql database

"""
import argparse
import gettext
import logging
import subprocess
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from pkg_resources import DistributionNotFound, get_distribution
from tabulate import tabulate

import pyexpander.lib as pyexpander
from export_vn.biolovision_api import TaxoGroupsAPI
from export_vn.download_vn import (Entities, LocalAdminUnits, Observations,
                                   Observers, Places, Species, TaxoGroup,
                                   TerritorialUnits)
from export_vn.evnconf import EvnConf
from export_vn.store_postgresql import PostgresqlUtils, StorePostgresql

try:
    __version__ = get_distribution('export_vn').version
except DistributionNotFound:
     __version__ = '0.0.0'

# Install gettext for any file in the application
localedir = Path(__file__).resolve().parent.parent / 'locale'
gettext.install('transfer_vn', str(localedir))


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
                        help=_('Print version number'),
                        action='version',
                        version='%(prog)s {version}'.
                        format(version=__version__))
    parser.add_argument('-v', '--verbose',
                        help=_('Increase output verbosity'),
                        action='store_true')
    parser.add_argument('-q', '--quiet',
                        help=_('Reduce output verbosity'),
                        action='store_true')
    parser.add_argument('--db_drop',
                        help=_('Delete if exists database and roles'),
                        action='store_true')
    parser.add_argument('--db_create',
                        help=_('Create database and roles'),
                        action='store_true')
    parser.add_argument('--json_tables_create',
                        help=_('Create or recreate json tables'),
                        action='store_true')
    parser.add_argument('--col_tables_create',
                        help=_('Create or recreate colums based tables'),
                        action='store_true')
    parser.add_argument('--full',
                        help=_('Perform a full download'),
                        action='store_true')
    parser.add_argument('--update',
                        help=_('Perform an incremental download'),
                        action='store_true')
    parser.add_argument('--count',
                        help=_('Count observations by site and taxo_group'),
                        action='store_true')
    parser.add_argument('file',
                        help=_('Configuration file name'))

    args = parser.parse_args()
    return args


def full_download(cfg_ctrl):
    """Performs a full download of all sites and controlers,
       based on configuration file."""
    logger = logging.getLogger('transfer_vn')
    cfg_crtl_list = cfg_ctrl.ctrl_list
    cfg_site_list = cfg_ctrl.site_list
    cfg = list(cfg_site_list.values())[0]
    # Looping on sites
    for site, cfg in cfg_site_list.items():
        with StorePostgresql(cfg) as store_pg:
            if cfg.enabled:
                logger.info(_('Working on site %s'), cfg.site)

                ctrl = 'taxo_group'
                if cfg_crtl_list[ctrl].enabled:
                    logger.info(_('Using controler %s on site %s'),
                                ctrl, cfg.site)
                    taxo_group = TaxoGroup(cfg, store_pg)
                    taxo_group.store()

                ctrl = 'observations'
                if cfg_crtl_list[ctrl].enabled:
                    logger.info(_('Using controler %s on site %s'),
                                ctrl, cfg.site)
                    observations = Observations(cfg, store_pg)
                    taxo_groups = TaxoGroupsAPI(cfg).api_list()['data']
                    taxo_groups_ex = cfg_crtl_list[ctrl].taxo_exclude
                    logger.info(_('Excluded taxo_groups: %s'), taxo_groups_ex)
                    taxo_groups_filt = []
                    for taxo in taxo_groups:
                        if (not taxo['name_constant'] in taxo_groups_ex) \
                                and (taxo['access_mode'] != 'none'):
                            taxo_groups_filt.append(taxo['id'])
                    logger.info(
                        _('Downloading from taxo_groups: %s'), taxo_groups_filt)
                    observations.store(
                        taxo_groups_filt, method='search', by_specie=False)

                ctrl = 'entities'
                if cfg_crtl_list[ctrl].enabled:
                    logger.info(_('Using controler %s on site %s'),
                                ctrl, cfg.site)
                    entities = Entities(cfg, store_pg)
                    entities.store()

                ctrl = 'territorial_unit'
                if cfg_crtl_list[ctrl].enabled:
                    logger.info(_('Using controler %s on site %s'),
                                ctrl, cfg.site)
                    territorial_unit = TerritorialUnits(cfg, store_pg)
                    territorial_unit.store()

                ctrl = 'local_admin_units'
                if cfg_crtl_list[ctrl].enabled:
                    logger.info(_('Using controler %s on site %s'),
                                ctrl, cfg.site)
                    local_admin_units = LocalAdminUnits(cfg, store_pg)
                    local_admin_units.store()

                ctrl = 'places'
                if cfg_crtl_list[ctrl].enabled:
                    logger.info(_('Using controler %s on site %s'),
                                ctrl, cfg.site)
                    places = Places(cfg, store_pg)
                    places.store()

                ctrl = 'species'
                if cfg_crtl_list[ctrl].enabled:
                    logger.info(_('Using controler %s on site %s'),
                                ctrl, cfg.site)
                    species = Species(cfg, store_pg)
                    species.store()

                ctrl = 'observers'
                if cfg_crtl_list[ctrl].enabled:
                    logger.info(_('Using controler %s on site %s'),
                                ctrl, cfg.site)
                    places = Observers(cfg, store_pg)
                    places.store()

            else:
                logger.info(_('Skipping site %s'), site)

    return None


def increment_download(cfg_ctrl):
    """Performs an incremental download of observations from all sites
    and controlers, based on configuration file."""
    logger = logging.getLogger('transfer_vn')
    cfg_crtl_list = cfg_ctrl.ctrl_list
    cfg_site_list = cfg_ctrl.site_list
    cfg = list(cfg_site_list.values())[0]
    # Looping on sites
    for site, cfg in cfg_site_list.items():
        with StorePostgresql(cfg) as store_pg:
            if cfg.enabled:
                logger.info(_('Working on site %s'), site)

                ctrl = 'observations'
                if cfg_crtl_list[ctrl].enabled:
                    logger.info(_('Using controler %s'), ctrl)
                    observations = Observations(cfg, store_pg)
                    taxo_groups = TaxoGroupsAPI(cfg).api_list()['data']
                    taxo_groups_ex = cfg_crtl_list[ctrl].taxo_exclude
                    logger.info(_('Excluded taxo_groups: %s'), taxo_groups_ex)
                    taxo_groups_filt = []
                    for taxo in taxo_groups:
                        if (not taxo['name_constant'] in taxo_groups_ex)\
                                and (taxo['access_mode'] != 'none'):
                            taxo_groups_filt.append(taxo['id'])
                    logger.info(_('Downloading from taxo_groups: %s'),
                                taxo_groups_filt)
                    observations.update(taxo_groups_filt)

            else:
                logger.info(_('Skipping site %s'), site)

    return None


def count_observations(cfg_ctrl):
    """Count observations by site and taxo_group."""
    logger = logging.getLogger('transfer_vn')
    cfg_site_list = cfg_ctrl.site_list

    col_counts = None
    for site, cfg in cfg_site_list.items():
        try:
            if cfg.enabled:
                if col_counts is None:
                    manage_pg = PostgresqlUtils(cfg)
                    # print(tabulate(manage_pg.count_json_obs()))
                    col_counts = manage_pg.count_col_obs()

                logger.info(_('Getting counts from %s'), cfg.site)
                site_counts = list()
                if cfg.site == 'Haute-Savoie':
                    for r in col_counts:
                        if r[0] == 'Haute-Savoie':
                            site_counts.append([r[0], r[2], -1, r[3]])
                else:
                    url = cfg.base_url + 'index.php?m_id=23'
                    page = requests.get(url)
                    soup = BeautifulSoup(page.text, 'html.parser')

                    counts = soup.find_all('table')[2].contents[1].contents[3]
                    rows = counts.contents[5].contents[0].contents[0].contents[1:-1]
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
                                                int(rows[i].contents[0].contents[0].
                                                    replace(' ', '')),
                                                col_c])
                print(tabulate(site_counts,
                               headers=[_('Site'), _('TaxoName'),
                                        _('Remote count'), _('Local count')],
                               tablefmt='psql'))
        except:
            logger.error(_('Can not retrieve informations from %s'), cfg.site)

    return None


def main():
    """
    Main.
    """
    # Create $HOME/tmp directory if it does not exist
    Path(str(Path.home()) + '/tmp').mkdir(exist_ok=True)

    # Define logger format and handlers
    logger = logging.getLogger('transfer_vn')
    # create file handler which logs even debug messages
    fh = TimedRotatingFileHandler(str(Path.home()) + '/tmp/transfer_vn.log',
                                  when='midnight',
                                  interval=1,
                                  backupCount=100)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    # Get command line arguments
    args = arguments()

    # Define verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        sql_quiet = ""
        client_min_message = "debug1"
    else:
        logger.setLevel(logging.INFO)
        sql_quiet = "--quiet"
        client_min_message = "warning"

    logger.info(_('%s, version %s'), sys.argv[0], __version__)
    logger.info(_('Arguments: %s'), sys.argv[1:])

    # Get configuration from file
    if not Path(str(Path.home()) + '/' + args.file).is_file():
        logger.critical(_('File %s does not exist'),
                        str(Path.home()) + '/' + args.file)
        return None

    logger.info(_('Getting configuration data from %s'), args.file)
    cfg_ctrl = EvnConf(args.file)
    cfg_site_list = cfg_ctrl.site_list
    cfg = list(cfg_site_list.values())[0]

    manage_pg = PostgresqlUtils(cfg)
    db_cfg = db_config(cfg)
    if args.db_drop:
        logger.info(_('Delete if exists database and roles'))
        manage_pg.drop_database()

    if args.db_create:
        logger.info(_('Create database and roles'))
        manage_pg.create_database()

    if args.json_tables_create:
        logger.info(_('Create, if not exists, json tables'))
        manage_pg.create_json_tables()

    if args.col_tables_create:
        logger.info(_('Creating or recreating vn colums based files'))
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
            logger.error(err)

    if args.full:
        logger.info(_('Performing a full download'))
        full_download(cfg_ctrl)

    if args.update:
        logger.info(_('Performing an incremental download of observations'))
        increment_download(cfg_ctrl)

    if args.count:
        logger.info(_('Counting observations'))
        count_observations(cfg_ctrl)

    return None


# Main wrapper
if __name__ == '__main__':
    main()
