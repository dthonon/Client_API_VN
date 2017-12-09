# -*- coding: utf-8 -*-
"""
"""

import sys, getopt
import json
import pprint
import csv
import requests

import logging
logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)  # __name__=projectA.moduleB

from Params import *

# Get all species
def get_species( species_file ):

    nb_xfer = 1 # Sequence number for transfers
    protected_url = evn_base_url + 'api/species/' # URL to GET species

    # Using OAuth1 auth helper
    oauth = OAuth1(evn_client_key, client_secret = evn_client_secret)

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
            response = resp.text # unzip TODO
        else:
            logger.info('No content_encoding')
            response = resp.text

        # Save in json file
        species_json = str(Path.home()) + '/' + evn_file_store + '/json/' + species_file + '_' + str(nb_xfer) + '.json'
        logger.info("Storing json data to '%s'",  species_json)
        with open(species_json, 'w', newline='') as jsonfile:
            jsonfile.write(response)

        # Is there more data to come?
        if (('transfer-encoding' in resp.headers) and (resp.headers['transfer-encoding'] == 'chunked')):
            logger.info('Chunked transfer => requesting for more')
        else:
            logger.info('Non-chunked transfer => finished requests')
            break

        logger.info(resp.headers['pagination_key'])
        # Mandatory parameters
        params = {'user_email': evn_user_email, 'user_pw': evn_user_pw, 'pagination_key': resp.headers['pagination_key']}
        nb_xfer += 1

    return(resp.status_code)

# Print usage message
def usage():
    print('GetObs -o|--output <species_file_basename>')

# Main
def main(argv):

    try:
        opts, args = getopt.getopt(argv, 'ho:', ['help', 'output='])
    except getopt.GetoptError:
        usage()
        return(2)

    sighting_number = ''
    for opt, arg in opts:
        # print(opt, arg)
        if opt in ('-h', '--help'):
            usage()
            return()
        elif opt in ('-o', '--output'):
            species_file = arg
        else:
            assert False, 'Unknown option'
            return(2)

    # Get species in json format
    return_code = get_species(species_file)

# Main wrapper
if __name__ == "__main__":
    main(sys.argv[1:])
