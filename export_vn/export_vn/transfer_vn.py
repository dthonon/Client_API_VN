#!/usr/bin/env python3
"""
Program managing VisioNature export to Postgresql database


"""
import sys
import logging
import argparse
import json

from export_vn.download_vn import DownloadVn, DownloadVnException
from export_vn.download_vn import Entities, LocalAdminUnits, Observations, Places
from export_vn.download_vn import Species, TaxoGroup, TerritorialUnits
from export_vn.store_postgresql import StorePostgresql
from export_vn.evnconf import EvnConf

# version of the program:
__version__ = "0.1.1" #VERSION#

def main():
    """
    Main.
    """

    # Get options
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose',
                        help='increase output verbosity',
                        action='store_true')
    parser.add_argument('-q', '--quiet',
                        help='reduce output verbosity',
                        action='store_true')
    parser.add_argument('-t', '--test',
                        help='test mode, with limited download volume',
                        action='store_true')
    parser.add_argument('site',
                        help='site name, used to select config file')

    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)

    logging.info('Getting data from %s', args.site)

    # Get configuration and instances
    cfg = EvnConf(args.site)
    store_pg = StorePostgresql(cfg)
    entities = Entities(cfg, store_pg.store)
    local_admin_units = LocalAdminUnits(cfg, store_pg.store)
    observations = Observations(cfg, store_pg.store)
    places = Places(cfg, store_pg.store)
    species = Species(cfg, store_pg.store)
    taxo_group = TaxoGroup(cfg, store_pg.store)
    territorial_unit = TerritorialUnits(cfg, store_pg.store)


# Main wrapper
if __name__ == "__main__":
    main()
