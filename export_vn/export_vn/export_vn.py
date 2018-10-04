#!/usr/bin/env python3
"""
Program managing VisioNature export to Postgresql database


"""
import sys
import logging
import argparse
import json

from evnconf import EvnConf
from biolovision_api import BiolovisionAPI

# version of the program:
__version__ = "0.1.1" #VERSION#

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
        # conn = psycopg2.connect('dbname={} user={} ' +
        # 'password={}'.format(evn_db_name, evn_db_user, evn_db_pw))
        # # Open a cursor to perform database operations
        # cur = conn.cursor()
        # # Fetch last modification date
        # cur.execute('SELECT download_ts FROM {}.download_log ' + '
        # ORDER BY download_ts DESC LIMIT 1;'.format(evn_db_schema))
        # # retrieve the records from the database
        # records = cur.fetchall()
        # last_update = records[0][0]
        # logging.info('Getting updates since {}'.format(last_update))
        # # Close communication with the database
        # logging.info('Closing database {}'.format(evn_db_name))
        # cur.close()
        # conn.close()
        # params['date'] = self.from_date.strftime('%H:%M:%S %d.%m.%Y')

    @staticmethod
    def get_taxo_groups(api):
        """
        Get the taxo_groups from API and return the list of active taxo groups
        """
        taxo_groups = api.taxo_groups_list()
        taxo_groups_list = list()
        for taxo in taxo_groups['data']:
            if taxo['access_mode'] != 'none':
                taxo_groups_list.append(taxo)
        logging.info('Found %i active taxo_groups', len(taxo_groups_list))
        logging.debug(taxo_groups_list)
        return taxo_groups_list

    def get_changes(self):
        """
        Get incremental changes through observations/diff.
        Loop on taxo_groups
        """

        logging.info('Getting increment data from %s', self._config.site)
        evn_api = BiolovisionAPI(self._config, self._max_retry, self._max_requests)

        # Create range iterator based on taxo_groups
        taxo_groups = iter(self.get_taxo_groups(evn_api))

        nb_requests = 0
        try:
            while nb_requests < self._max_requests:
                if evn_api.transfer_errors == 0:
                    # No errors, moving to next item
                    nb_requests += 1
                    taxon = next(taxo_groups)
                elif evn_api.transfer_errors < self._max_retry:
                    # Errors, retrying same item
                    logging.info('Retrying transfer for %i time', evn_api.transfer_errors)
                else:
                    logging.error('Too many retries, quitting')
                    raise ConnectionError('Too many retries, quitting')

                # Get list of updates from API
                logging.info('Getting incremental data for taxo_group %s : %s',
                             taxon['id'], taxon['name'])
                resp_dict = evn_api.observations_diff(taxon['id'],
                                                      '10:58:40 14.09.2018')
                logging.debug(json.dumps(resp_dict, sort_keys=True,
                                         indent=4, separators=(',', ': ')))

                logging.info('Number of increments : %i', len(resp_dict))

                # Loop on list of changes and either insert/update or delete row in database
                for diff in resp_dict:
                    if diff['modification_type'] == 'updated':
                        logging.debug('Création ou mise à jour de %s', diff['id_sighting'])
                    elif diff['modification_type'] == 'deleted':
                        logging.debug('Suppression de %s', diff['id_sighting'])
                    else:
                        logging.error('Type de modification inconnu : %s', diff)


        except StopIteration:
            logging.info('End of loop for observations/diff API')

        return


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

    logging.info('Getting incremental data from %s', args.site)
    # Get incremental observations in json format
    if args.test:
        # Limit nb of taxo_groups API requests for quicker test
        config = EvnConf(args.site)
        t21 = UpdateObs(config, max_retry=1, max_requests=2)
        t21.get_changes()
    else:
        logging.warning('Seul --test est implémenté')

# Main wrapper
if __name__ == "__main__":
    main()
