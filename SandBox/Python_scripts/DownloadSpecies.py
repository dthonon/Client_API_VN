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


def get_species():
    """
    Get all species.

    Loop on calling API for chunks os species data and store result in compressed json files.

    :returns:
        HTTP return code.
    :rtype:
        str
    """

    species_file = 'species'

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

    nb_xfer = 1  # Sequence number for transfers
    protected_url = evn_base_url + 'api/species/'  # URL to GET species

    # Using OAuth1 auth helper
    oauth = OAuth1(evn_client_key, client_secret=evn_client_secret)

    # Mandatory parameters
    params = {'user_email': evn_user_email, 'user_pw': evn_user_pw}

    # Loop on data requests until end of transfer
    while (nb_xfer < 5):
        # GET species
        logger.info('Getting data from %s',  protected_url)
        resp = requests.get(url=protected_url, auth=oauth, params=params)
        logger.debug(resp.url)
        logger.debug(resp.request.headers)
        logger.debug(resp.headers)
        logger.debug(resp.text[1:50])
        if resp.status_code != 200:
            print('GET status code = {}, for species {}'.format(resp.status_code))
            return('')

        # Is the content zipped or compressed?
        if ('content_encoding' in resp.headers):
            logger.info(resp.headers['content_encoding'])
            response = resp.text  # unzip TODO
        else:
            logger.info('No content_encoding')
            response = resp.text

        # Pretty print
        resp_dict = json.loads(response)
        resp_pretty = json.dumps(resp_dict, sort_keys=True, indent=4, separators=(',', ': '))

        # Save in json file
        species_json = str(Path.home()) + '/' + evn_file_store + '/json/' + \
            species_file + '_' + str(nb_xfer) + '.json.gz'
        logger.info("Storing json data to '%s'",  species_json)
        g = gzip.open(species_json, 'wb', 9)
        g.write(resp_pretty.encode())
        g.close()
        # with gzip.open(species_json, 'w') as jf:
        #     jf.write(resp_pretty)

        # Is there more data to come?
        if (('transfer-encoding' in resp.headers) and (resp.headers['transfer-encoding'] == 'chunked')):
            logger.info('Chunked transfer => requesting for more')
        else:
            logger.info('Non-chunked transfer => finished requests')
            break

        logger.info(resp.headers['pagination_key'])
        # Update request parameters to get next chunk
        params = {'user_email': evn_user_email, 'user_pw': evn_user_pw,
                  'pagination_key': resp.headers['pagination_key']}
        nb_xfer += 1

    return(resp.status_code)


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

    # Get species in json format
    get_species()


# Main wrapper
if __name__ == "__main__":
    main(sys.argv[1:])
