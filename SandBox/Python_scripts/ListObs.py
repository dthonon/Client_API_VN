#!/usr/bin/env python3
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

# Get 1 observation and print
def get_obs(obs_num):
    # GET observation
    resp = requests.get(url=protected_url + obs_num, auth=oauth, params=params)

    #print(resp.url)
    #print(resp.request.headers)
    #print(resp.text)
    if resp.status_code != 200:
        print('GET status code = {}, for observation {}'.format(resp.status_code, obs_num))
        return([obs_num, -1, resp.status_code, 0])

    # Decode in dict
    data_decoded = json.loads(resp.text)

    # Save in json file
    with open('json/obs' + obs_num + '.json', 'w', newline='') as jsonfile:
        jsonfile.write(resp.text)

    if 'forms' in data_decoded['data']:
        obs_data = data_decoded['data']['forms'][0]
    else:
        obs_data = data_decoded['data']
    nb_sightings = len(obs_data['sightings'])
    if (nb_sightings == 1):
        nb_observer = len(obs_data['sightings'][0]['observers'])
    else:
        nb_observer = -1
        pp = pprint.PrettyPrinter(indent=1, width=120)
        pp.pprint(obs_data)
    if (nb_observer == 1):
        if 'extended_info' in obs_data['sightings'][0]['observers'][0]:
            ext_info = obs_data['sightings'][0]['observers'][0]['extended_info']
        else:
            ext_info = ''
    else:
        ext_info = '-1'

    return([obs_num, nb_sightings, nb_observer, ext_info])


# Print usage message
def usage():
    print('GetObs -i|--input <list of observations>')

# Main
# Parse arguments and call site_list for each Oracle DC
def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'hi:', ['help', 'input='])
    except getopt.GetoptError:
        usage()
        return(2)

    sighting_number = ''
    for opt, arg in opts:
        # print(opt, arg)
        if opt in ('-h', '--help'):
            usage()
            return()
        elif opt in ('-i', '--input'):
            sighting_list = arg
        else:
            assert False, 'Unknown option'
            return(2)

    if (len(sighting_list) == 0):
        print('ERROR: sighting is mandatory')
        usage()
        return(2)

    with open(sighting_list, newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter='\t')
        print('Opened input')
        row_num = 0
        obs_list = []
        for row in spamreader:
            sighting_number = row[1]
            print('Line {:>5}, observation number {:>6}'.format(row_num, sighting_number))
            # Add to list
            obs_list += [get_obs(sighting_number)]
            row_num += 1

    pp = pprint.PrettyPrinter(indent=1, width=120)
    pp.pprint(obs_list)

    with open('nb_obs.csv', 'w', newline='') as csvout:
        spamwriter = csv.writer(csvout, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        print('Opened output')
        for row in obs_list:
            spamwriter.writerow(row)


# Main wrapper
if __name__ == "__main__":
    main(sys.argv[1:])
