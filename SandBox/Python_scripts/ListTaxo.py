# -*- coding: utf-8 -*-
"""
"""

import sys, getopt
import json
import pprint
import csv
from beautifultable import BeautifulTable
import requests

from Params import *

# Get all taxo groups
def get_taxo():
    # URL to GET taxo_groups
    protected_url = 'http://www.faune-isere.org/api/taxo_groups/'

    # GET taxo groups
    resp = requests.get(url=protected_url, auth=oauth, params=params)

    # print(resp.url)
    # print(resp.request.headers)
    # print(resp.text)
    if resp.status_code != 200:
        print('GET status code = {}, for taxo_groups {}'.format(resp.status_code))
        return('')

    return(resp.text)

# Print usage message
def usage():
    print('GetObs -i|--input <list of observations>')

# Main
# Parse arguments and call site_list for each Oracle DC
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
    with open(taxo_file + '.json', 'w', newline='') as jsonfile:
        jsonfile.write(taxo_list)

    # Decode in dict
    data_decoded = json.loads(taxo_list)

    # pp = pprint.PrettyPrinter(indent=1, width=120)
    # pp.pprint(data_decoded)

    with open(taxo_file + '.csv', 'w', newline='') as csvout:
        fieldnames = ['id', 'latin_name', 'name', 'access_mode', 'name_constant']
        spamwriter = csv.DictWriter(csvout, fieldnames=fieldnames, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        print('Opened output')
        for row in data_decoded['data']:
            spamwriter.writerow(row)

# Main wrapper
if __name__ == "__main__":
    main(sys.argv[1:])
