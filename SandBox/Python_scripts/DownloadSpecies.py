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
import getopt
import requests
from requests_oauthlib import OAuth1
import json
import gzip
import logging
import configparser
from pathlib import Path

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


class DownloadTable:
    """
    Download from an API controler, named table (i.e. species).
    """

    # Constants for different lists of subqueries
    NO_LIST = 0  # No subquery, just request all data
    TAXO_GROUPS_LIST = 1  # Loop subquery on taxo_groups
    ADMIN_UNITS_LIST = 2  # Loop subquery on local_admin_units (communes)

    def __init__(self, site, user_email, user_pw, oauth, table, file_store,
                 by_list = NO_LIST, max_download=10):
      self.site = site
      self.user_email = user_email
      self.user_pw = user_pw
      self.oauth = oauth
      self.table = table
      self.file_store = file_store
      self.by_list = by_list
      self.max_download = max_download

    def get_table(self):
        """
        Get all date from one API controler.

        Loop on calling API for chunks of data and store result in compressed json files.
        """

        # Mandatory parameters.
        params = {'user_email': self.user_email, 'user_pw': self.user_pw}

        # Create range based on type of get_table
        if (self.by_list == self.NO_LIST):
            api_range = range(1, 2)
        elif (self.by_list == self.TAXO_GROUPS_LIST):
            api_range = range(1, self.max_download)
        elif (self.by_list ==  self.ADMIN_UNITS_LIST):
            api_range = range(1, self.max_download)
        else:
            logger.error('Unknown list {}'.format(self.by_list))
            return(self.by_list)

        for i in api_range:
            nb_xfer = 1  # Sequence number for transfers, restarting for each group

            # Add specific parameters if needed
            if (self.by_list == self.NO_LIST):
                logger.info('Getting data from table {} direct'.format(self.table))
            elif (self.by_list == self.TAXO_GROUPS_LIST):
                logger.info('Getting data from table {}, id_taxo_group {}'.format(self.table, i))
                params['id_taxo_group'] = str(i)
            elif (self.by_list ==  self.ADMIN_UNITS_LIST):
                logger.info('Getting data from table {}, id_commune {}'.format(self.table, i))
                params['id_commune'] = str(i)
            else:
                logger.error('Unknown list {}'.format(self.by_list))
                return(self.by_list)

            # Loop on data requests until end of transfer
            while True:

                # GET from API
                logger.debug('Params: {}'.format(params))
                resp = requests.get(url=self.site+self.table+'/', auth=self.oauth, params=params)
                logger.debug(resp.url)
                logger.debug(resp.request.headers)
                logger.debug(resp.headers)
                if resp.status_code != 200:
                    print('GET status code = {}, for table {}'.format(resp.status_code, self.table))
                    return(resp.status_code)

                # Is the content zipped or compressed?
                if ('content_encoding' in resp.headers):
                    logger.debug(resp.headers['content_encoding'])
                else:
                    logger.debug('No content_encoding')

                # Pretty print to string before store
                resp_dict = resp.json()
                resp_pretty = json.dumps(resp_dict, sort_keys=True, indent=4, separators=(',', ': '))

                # Save in json file, if not empty
                if (len(resp_dict['data']) > 0):
                    file_json = str(Path.home()) + '/' + self.file_store + '/json/' + \
                        self.table + '_' + str(i) + '_' + str(nb_xfer) + '.json.gz'
                    logger.info('Received {} elements, storing json data to {}'.format(len(resp_dict['data']), file_json))
                    with gzip.open(file_json, 'wb', 9) as g:
                        g.write(resp_pretty.encode())

                # Is there more data to come?
                if (('transfer-encoding' in resp.headers) and (resp.headers['transfer-encoding'] == 'chunked')):
                    logger.info('Chunked transfer => requesting for more, with key: {}'.format(resp.headers['pagination_key']))
                    # Update request parameters to get next chunk
                    params ['pagination_key'] = resp.headers['pagination_key']
                    nb_xfer += 1
                else:
                    logger.info('Non-chunked transfer => finished requests')
                    break

        return


def usage():
    """
    Print usage message.
    """
    print('DownloadSpecies')


def main(argv):
    """
    Main.
    """

    # Get options
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

    # Read configuration parameters
    config = configparser.ConfigParser()
    config.read(str(Path.home()) + '/.evn.ini')

    # Import parameters in local variables
    evn_client_key = config['faune-isere.org']['evn_client_key']
    evn_client_secret = config['faune-isere.org']['evn_client_secret']
    evn_user_email = config['faune-isere.org']['evn_user_email']
    evn_user_pw = config['faune-isere.org']['evn_user_pw']
    evn_base_url = config['faune-isere.org']['evn_site']
    evn_file_store = config['faune-isere.org']['evn_file_store']

    protected_url = evn_base_url + 'api/'  # URL to GET species
    logger.info('Getting data from {}'.format(protected_url))

    # Using OAuth1 auth helper
    oauth = OAuth1(evn_client_key, client_secret=evn_client_secret)

    # -------------------
    # Organizational data
    # -------------------
    # Get entities in json format
    t1 = DownloadTable(protected_url, evn_user_email, evn_user_pw, oauth, 'entities', evn_file_store, \
                       DownloadTable.NO_LIST, 5)
    t1.get_table()

    # Get export_organizations in json format
    t1 = DownloadTable(protected_url, evn_user_email, evn_user_pw, oauth, 'export_organizations', evn_file_store, \
                       DownloadTable.NO_LIST, 5)
    t1.get_table()

    # -------------------
    # Organizational data
    # -------------------
    # Get taxo_groups in json format
    t1 = DownloadTable(protected_url, evn_user_email, evn_user_pw, oauth, 'taxo_groups', evn_file_store, \
                       DownloadTable.NO_LIST, 5)
    t1.get_table()

    # Get species in json format
    t1 = DownloadTable(protected_url, evn_user_email, evn_user_pw, oauth, 'species', evn_file_store, \
                       DownloadTable.TAXO_GROUPS_LIST, 50)
    t1.get_table()


# Main wrapper
if __name__ == "__main__":
    main(sys.argv[1:])
