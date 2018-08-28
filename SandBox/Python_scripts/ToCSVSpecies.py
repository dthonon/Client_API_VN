# -*- coding: utf-8 -*-
"""
DownloadSpecies: retrieves all species from VisioNature website and store to json files.

Copyright (C) 2017, Daniel Thonon

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import os
import getopt
import json
import gzip
import csv
import logging
import configparser
from pathlib import Path

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)  # __name__=projectA.moduleB


def outputCSV():
    """
    Get all species files and export to CSV.

    Loop on loading compressed json files, convert to CSV and export.

    """

    # Read configuration parameters
    config = configparser.ConfigParser()
    config.read(str(Path.home()) + '/.evn.ini')

    # Import parameters in local constants
    EVN_FILE_STORE = config['faune-isere.org']['evn_file_store']

    SPECIES_FILE = 'species'

    nb_xfer = 1  # Sequence number for transfers

    logger.info('Storing species in CSV file')
    fieldnames = [
        'id',
        'id_taxo_group',
        'latin_name',
        'french_name',
        'french_name_plur',
        'sys_order',
        'sempach_id_family',
        'is_used',
        'category_1',
        'rarity',
        'atlas_start',
        'atlas_end'
        ]
    species_csv = str(Path.home()) + '/' + EVN_FILE_STORE + '/csv/' + \
        SPECIES_FILE + '.csv'
    with open(species_csv, 'w', newline='') as csvout:
        spamwriter = csv.DictWriter(csvout,
                                    fieldnames=fieldnames,
                                    delimiter=';',
                                    quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)
        spamwriter.writeheader()

        while True:
            # Loop on json files
            species_json = str(Path.home()) + '/' + EVN_FILE_STORE + '/json/' + \
                SPECIES_FILE + '_' + str(nb_xfer) + '.json.gz'

            if not os.path.isfile(species_json):
                break
            logger.info('Loading json file {}'.format(species_json))
            with gzip.open(species_json, 'rb') as g:
                species_list = g.read()

            # Decode in dict and merge with full list
            data_decoded = json.loads(species_list)

            if (nb_xfer == 1):
                merged_species = data_decoded['data']
                logger.debug(merged_species[0])
                logger.debug(merged_species[-1:])
            else:
                if (len(data_decoded['data']) > 0):
                    merged_species.extend(data_decoded['data'])
                logger.debug(merged_species[0])
                logger.debug(merged_species[-1:])

            nb_xfer += 1

        logger.info('Storing csv data to {}'.format(species_csv))
        for row in merged_species:
            spamwriter.writerow(row)

    return()


def usage():
    """
    Print usage message.
    """
    print('ToCSVSpecies')


def main(argv):
    """
    Main.
    """

    try:
        opts, args = getopt.getopt(argv, 'h:', ['help'])
    except getopt.GetoptError:
        usage()
        return(2)

    for opt, arg in opts:
        # print(opt, arg)
        if opt in ('-h', '--help'):
            usage()
            return()
        else:
            assert False, 'Unknown option'
            return(2)

    # Convert json to CSV
    outputCSV()


# Main wrapper
if __name__ == "__main__":
    main(sys.argv[1:])
