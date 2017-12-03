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

# Get all taxo groups
def get_taxo():

    # URL to GET taxo_groups
    protected_url = evn_base_url + 'api/taxo_groups/'
    logger.info("Getting data from '%s'",  protected_url)

    # GET taxo groups
    resp = requests.get(url=protected_url, auth=oauth, params=params)

    logger.debug(resp.url)
    logger.debug(resp.request.headers)
    logger.debug(resp.text)
    if resp.status_code != 200:
        print('GET status code = {}, for taxo_groups {}'.format(resp.status_code))
        return('')

    return(resp.text)

# Print usage message
def usage():
    print('GetObs -o|--output <taxo_file_basename>')

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
            taxo_file = arg
        else:
            assert False, 'Unknown option'
            return(2)

    # Get taxo_groups in json format
    taxo_list = get_taxo()

    # Save in json file
    taxo_json = str(Path.home()) + '/' + evn_file_store + '/json/' + taxo_file + '.json'
    logger.info("Storing json data to '%s'",  taxo_json)
    with open(taxo_json, 'w', newline='') as jsonfile:
        jsonfile.write(taxo_list)

    # Decode in dict
    data_decoded = json.loads(taxo_list)

    # pp = pprint.PrettyPrinter(indent=1, width=120)
    # pp.pprint(data_decoded)

    taxo_csv = str(Path.home()) + '/' + evn_file_store + '/csv/' + taxo_file + '.csv'
    logger.info("Storing csv data to '%s'",  taxo_csv)
    with open(taxo_csv, 'w', newline='') as csvout:
        fieldnames = ['id', 'latin_name', 'name', 'access_mode', 'name_constant']
        spamwriter = csv.DictWriter(csvout, fieldnames=fieldnames, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in data_decoded['data']:
            spamwriter.writerow(row)

# Main wrapper
if __name__ == "__main__":
    main(sys.argv[1:])
