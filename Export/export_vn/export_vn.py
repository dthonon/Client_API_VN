#!/usr/bin/env python3
"""
Program managing VisioNature export to Postgresql database

Copyright (C) 2018, Daniel Thonon

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
import logging
from optparse import OptionParser
import json

from evnconf import EvnConf
from biolovision_api import BiolovisionAPI

# version of the program:
__version__= "0.1.1" #VERSION#

class UpdateObs:
    """
    Download incremental list of changes from site and update database.
    """

    def __init__(self, config, max_retry=5, max_requests=sys.maxsize):
        self._config = config
        self._max_retry = max_retry
        self._max_requests = max_requests

        # self.from_date = TODO
        # # Connect to evn database
        # conn = psycopg2.connect('dbname={} user={} password={}'.format(evn_db_name, evn_db_user, evn_db_pw))
        # # Open a cursor to perform database operations
        # cur = conn.cursor()
        # # Fetch last modification date
        # cur.execute('SELECT download_ts FROM {}.download_log ORDER BY download_ts DESC LIMIT 1;'.format(evn_db_schema))
        # # retrieve the records from the database
        # records = cur.fetchall()
        # last_update = records[0][0]
        # logging.info('Getting updates since {}'.format(last_update))
        # # Close communication with the database
        # logging.info('Closing database {}'.format(evn_db_name))
        # cur.close()
        # conn.close()
        # params['date'] = self.from_date.strftime('%H:%M:%S %d.%m.%Y')


    def get_taxo_groups(self, api):
        """
        Get the taxo_groups from API and return the list of active taxo groups
        """
        taxo_groups = api.taxo_groups_list()
        taxo_groups_list = list()
        for taxo in taxo_groups['data']:
            if (taxo['access_mode'] != 'none'):
                taxo_groups_list.append(taxo)
        logging.info('Found {} active taxo_groups'.format(len(taxo_groups_list)))
        logging.debug(taxo_groups_list)
        return taxo_groups_list


    def get_changes(self):
        """
        Get incremental changes through observations/diff.
        Loop on taxo_groups
        """

        logging.info('Getting increment data from {}'.format(self._config.site))
        evn_api = BiolovisionAPI(self._config, self._max_retry, self._max_requests)

        # Create range iterator based on taxo_groups
        taxo_groups = iter(self.get_taxo_groups(evn_api))

        ii = 0
        try:
            while ii < self._max_requests:
                if (evn_api.transfer_errors == 0):
                    # No errors, moving to next item
                    ii += 1
                    taxon = next(taxo_groups)
                elif (evn_api.transfer_errors < self._max_retry):
                    # Errors, retrying same item
                    logging.info('Retrying transfer for {} time'.format(evn_api.transfer_errors))
                else:
                    logging.error('Too many retries, quitting')
                    raise ConnectionError('Too many retries, quitting')

                # Get list of updates from API
                logging.info('Getting incremental data for taxo_group {} : {}'.format(taxon['id'], taxon['name']))
                resp_dict = evn_api.observations_diff(taxon['id'], '10:58:40 14.09.2018')
                logging.debug(json.dumps(resp_dict, sort_keys=True, indent=4, separators=(',', ': ')))

                logging.info('Number of increments : {}'.format(len(resp_dict)))

                # Loop on list of changes and either insert/update or delete row in database
                for diff in resp_dict:
                    if (diff['modification_type'] == 'updated'):
                        logging.debug('Création ou mise à jour de {}'.format(diff['id_sighting']))
                    elif (diff['modification_type'] == 'deleted'):
                        logging.debug('Suppression de {}'.format(diff['id_sighting']))
                    else:
                        logging.error('Type de modification inconnu : {}'.format(diff))


        except StopIteration:
            logging.info('End of loop for {} API'.format(self.table))

        return


def script_shortname():
    """return the name of this script without a path component."""
    return os.path.basename(sys.argv[0])

def print_usage():
    """print a short summary of the scripts function."""
    print(('%-20s: Téléchargement incrémental des données Biolovision '+\
           'Ecrit en python ...\n') % script_shortname())

def main(argv):
    """
    Main.
    """

    # Get options
    # command-line options and command-line help:
    usage = 'usage: %prog [options] {files}'

    parser = OptionParser(usage=usage,
                          version='%%prog %s' % __version__,
                          description='Téléchargement des données Biolovision.')
    parser.add_option('-v', '--verbose',
                      action='store_true',
                      dest='verbose',
                      help='Traces de mise au point.'
                     )
    parser.add_option('-s', '--site',
                      dest='site',
                      help='Nom du site, utilisé pour sélectionner le fichier de paramétrage.'
                     )
    parser.add_option('-t', '--test',
                      action='store_true',
                      dest='test',
                      help='Force le mode test pour mise au point, qui limite le volume de données téléchargé au départ.'
                     )

    (options, args) = parser.parse_args()

    if (options.verbose) :
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level = logging.DEBUG)
    else :
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level = logging.INFO)

    if (options.test) :
        MAX_REQUESTS = 2 # Limit nb of taxo_groups API requests for quicker test
        # Get incremental observations in json format
        config = EvnConf(options.site)
        t21 = UpdateObs(config, max_retry = 1, max_requests = MAX_REQUESTS)
        t21.get_changes()
    else:
        MAX_REQUESTS = sys.maxsize # No limit, for production
        logging.warn('Seul --test est implémenté')

# Main wrapper
if __name__ == "__main__":
    main(sys.argv[1:])
