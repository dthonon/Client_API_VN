#!/usr/bin/env python3
"""
UpdateFromVN: retrieves incremental data from VisioNature website and update database

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
import configparser
from pathlib import Path

import requests
from requests_oauthlib import OAuth1
import json
import gzip

import psycopg2

from bisect import bisect_left, bisect_right
from operator import itemgetter
from pprint import pprint

# version of the program:
__version__= "0.1.1" #VERSION#

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level = logging.DEBUG)

def getTaxoGroups(file_store):
    """
    Read the taxo_groups files and return the list of taxo groups
    """
    # TODO: loop on all possible files
    file_json = str(Path.home()) + '/' + file_store + \
        'taxo_groups_1_1.json.gz'
    logging.debug('Reading taxo_groups file {}'.format(file_json))
    with gzip.open(file_json, 'rb') as g:
        taxo_groups = json.loads(g.read().decode('utf-8'))

    taxo_groups_list = list()
    for taxo in taxo_groups['data']:
        if (taxo['access_mode'] != 'none'):
            taxo_groups_list.append(taxo['id'])
    logging.info('Found {} taxo_groups in downloaded files'.format(len(taxo_groups_list)))
    logging.debug(taxo_groups_list)
    return taxo_groups_list


class DownloadTable:
    """
    Download from an API controler, named table (i.e. species).
    """

    def __init__(self, site, user_email, user_pw, oauth, file_store,
                 from_date, max_retry=5, max_requests=sys.maxsize):
      self.site = site
      self.user_email = user_email
      self.user_pw = user_pw
      self.oauth = oauth
      self.table = 'observations'
      self.file_store = file_store
      self.from_date = from_date
      self.max_retry = max_retry
      self.max_requests = max_requests

    def get_table(self):
        """
        Get all date from one API controler.

        Loop on calling API for chunks of data and store result in compressed json files.
        """

        # Mandatory parameters.
        params = {'user_email': self.user_email, 'user_pw': self.user_pw}

        # Create range based on type of get_table
        # api_range = getTaxoGroups(self.file_store)
        api_range = list('1')

        ii = 0
        r = iter(api_range)
        transferError = 0
        try:
            while ii < self.max_requests:
                nb_xfer = 1  # Sequence number for transfers, restarting for each group
                if (transferError == 0):
                    # No errors, moving to next item
                    ii += 1
                    i = next(r)
                elif (transferError < self.max_retry):
                    # Errors, retrying same item
                    logging.info('Retrying transfer for {} time'.format(transferError))
                else:
                    logging.error('Too many retries, quitting')
                    raise ConnectionError('Too many retries, quitting')

                # Add specific parameters if needed
                logging.info('Getting data from table {}, id_taxo_group {}'.format(self.table, i))
                params['id_taxo_group'] = str(i)
                params['modification_type'] = 'all'
                params['date'] = self.from_date.strftime('%H:%M:%S %d.%m.%Y')

                # Loop on data requests until end of transfer
                # With retry on error
                transferError = 0
                while True:
                    # GET from API
                    logging.debug('Params: {}'.format(params))
                    resp = requests.get(url=self.site, auth=self.oauth, params=params)
                    logging.debug(resp.url)
                    logging.debug(resp.request.headers)
                    logging.debug(resp.headers)
                    if resp.status_code != 200:
                        logging.error('GET status code = {}, for table {}'.format(resp.status_code, self.table))
                        transferError += 1
                        break

                    # Is the content zipped or compressed?
                    if ('content_encoding' in resp.headers):
                        logging.debug(resp.headers['content_encoding'])
                    else:
                        logging.debug('No content_encoding')

                    # Pretty print to string before store
                    resp_dict = resp.json()
                    resp_pretty = json.dumps(resp_dict, sort_keys=True, indent=4, separators=(',', ': '))

                    # Save in json file, if not empty
                    if (len(resp_dict['data']) > 0):
                        file_json_gz = str(Path.home()) + '/' + self.file_store + \
                            self.table + '_' + str(i) + '_' + str(nb_xfer) + '.json.gz'
                        logging.info('Received data, storing json to {}'.format(file_json_gz))
                        with gzip.open(file_json_gz, 'wb', 9) as g:
                            g.write(resp_pretty.encode())

                    # Is there more data to come?
                    if (('transfer-encoding' in resp.headers) and (resp.headers['transfer-encoding'] == 'chunked')):
                        logging.info('Chunked transfer => requesting for more, with key: {}'.format(resp.headers['pagination_key']))
                        # Update request parameters to get next chunk
                        params['pagination_key'] = resp.headers['pagination_key']
                        nb_xfer += 1
                    else:
                        logging.info('Non-chunked transfer => finished requests')
                        if ('pagination_key' in params):
                            del params['pagination_key']
                        break

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
                      help='Traces de mise au point.',
                     )

    parser.add_option('-s', '--site',
                      dest='site',
                      help='Nom du site, utilisé pour sélectionner le fichier de paramétrage.',
                     )

    (options, args) = parser.parse_args()

    # Read configuration parameters
    config = configparser.ConfigParser()
    config.read(str(Path.home()) + '/.evn_' + options.site + '.ini')

    # Import parameters in local variables
    evn_client_key = config['site']['evn_client_key']
    evn_client_secret = config['site']['evn_client_secret']
    evn_user_email = config['site']['evn_user_email']
    evn_user_pw = config['site']['evn_user_pw']
    evn_base_url = config['site']['evn_site']
    evn_file_store = config['site']['evn_file_store'] + '/' + options.site + '/'
    evn_db_host = config['database']['evn_db_host']
    evn_db_port = config['database']['evn_db_port']
    evn_db_name = config['database']['evn_db_name']
    evn_db_schema = config['database']['evn_db_schema']
    evn_db_group = config['database']['evn_db_group']
    evn_db_user = config['database']['evn_db_user']
    evn_db_pw = config['database']['evn_db_pw']
    evn_sql_scripts = config['database']['evn_sql_scripts']

    # Connect to evn database
    conn = psycopg2.connect('dbname={} user={} password={}'.format(evn_db_name, evn_db_user, evn_db_pw))
    # Open a cursor to perform database operations
    cur = conn.cursor()
    # Fetch last modification date
    cur.execute('SELECT download_ts FROM {}.download_log ORDER BY download_ts DESC LIMIT 1;'.format(evn_db_schema))
    # retrieve the records from the database
    records = cur.fetchall()
    last_update = records[0][0]
    logging.info('Getting updates since {}'.format(last_update))
    # Close communication with the database
    logging.info('Closing database {}'.format(evn_db_name))
    cur.close()
    conn.close()

    protected_url = evn_base_url + 'api/observations/diff/'  # URL to GET species
    logging.info('Getting data from {}'.format(protected_url))

    # Using OAuth1 auth helper
    oauth = OAuth1(evn_client_key, client_secret=evn_client_secret)

    MAX_REQUESTS = 10 # Limit nb of API requests for quicker test
    # MAX_REQUESTS = sys.maxsize # No limit, for production
    # ----------------
    # Observation data
    # ----------------
    # Get observations in json format
    t21 = DownloadTable(protected_url, evn_user_email, evn_user_pw, oauth, evn_file_store, \
                        last_update, max_retry = 1, max_requests = MAX_REQUESTS)
    t21.get_table()

# Main wrapper
if __name__ == "__main__":
    main(sys.argv[1:])
