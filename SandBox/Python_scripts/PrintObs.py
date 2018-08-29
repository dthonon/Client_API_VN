#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import sys
# import getopt
import logging
from optparse import OptionParser
import configparser
from pathlib import Path

import requests
from requests_oauthlib import OAuth1
import json
import gzip
import pprint

# version of the program:
__version__= "0.1.1" #VERSION#

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level = logging.DEBUG)

def script_shortname():
    """return the name of this script without a path component."""
    return os.path.basename(sys.argv[0])

def print_usage():
    """print a short summary of the scripts function."""
    print(('%-20s: Affichage d''une observation '+\
           'Ecrit en python ...\n') % script_shortname())

# Main
def main(argv):

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
    parser.add_option('-o', '--observation',
                      dest='observation',
                      help='Numéro d''observation à afficher.',
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

    # Using OAuth1 auth helper
    oauth = OAuth1(evn_client_key, client_secret=evn_client_secret)
    # Mandatory parameters.
    params = {'user_email': evn_user_email, 'user_pw': evn_user_pw}

    protected_url = evn_base_url + 'api/observations/' + options.observation # URL to GET species
    logging.info('Getting data from {}'.format(protected_url))

    pp = pprint.PrettyPrinter(indent=1, width=120)
    resp = requests.get(url=protected_url, auth=oauth, params=params)
    logging.debug('Request URL = {}'.format(resp.url))
    logging.debug('Request header')
    pp.pprint(resp.request.headers)
    logging.debug('Response header')
    pp.pprint(resp.headers)
    if resp.status_code != 200:
        print('GET status code = {}'.format(resp.status_code))
        return([resp.status_code, 0])

    resp_dict = resp.json()
    #pp.pprint(resp_dict)

# Main wrapper
if __name__ == "__main__":
    main(sys.argv[1:])
