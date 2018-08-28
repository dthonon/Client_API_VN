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

# Convert mortality cause from text to biolovision code
def mortality_cause(text):
    xcode = {
        'Chasse / Tir': 'HUNTING',
        'Collision avec un moyen de transports': 'COLL_TRANS',
        'Dénichage': 'DENICHAGE',
        'Empoisonnement': 'POISON',
        'Inconnu': 'UNKNOWN',
        'Pêche': 'FISHING',
        'Piège': 'TRAP',
        'Pollution': 'POLLUTION',
        'Prédation': 'PREDATION',
        'Réseau électrique': 'ELECTRIC'
    }
    return xcode[text]

# Add mortality to 1 observation
def modify_obs(obs_num, mortality):

    pp = pprint.PrettyPrinter(indent=1, width=120)

    # GET observation
    resp = requests.get(url=protected_url + obs_num, auth=oauth, params=params)

    #print(resp.url)
    #print(resp.request.headers)
    #print(resp.text)
    if resp.status_code != 200:
        print('GET status code = {}, for observation {}'.format(resp.status_code, obs_num))
        return([obs_num, -1, resp.status_code, -1, -1])

    # Decode in dict
    data_decoded = json.loads(resp.text)

    # Save in json file
    with open('json/obs' + obs_num + '.json', 'w', newline='') as jsonfile:
        jsonfile.write(pp.pformat(data_decoded) + '\n')

    # Work only on sighting, and merge at the end
    if 'forms' in data_decoded['data']:
        obs_data = data_decoded['data']['forms'][0]
    else:
        obs_data = data_decoded['data']

    nb_sightings = len(obs_data['sightings'])
    if (nb_sightings == 1):
        nb_observer = len(obs_data['sightings'][0]['observers'])
    else:
        nb_observer = -1
        pp.pprint(obs_data)
    if (nb_observer == 1):
        if ('extended_info' in obs_data['sightings'][0]['observers'][0]) and (len(obs_data['sightings'][0]['observers'][0]['extended_info']) > 0):
            print('WARNING: extended_info already set => not modified')
            # print(obs_data['sightings'][0]['observers'][0]['extended_info'])
            ext_info = obs_data['sightings'][0]['observers'][0]['extended_info']
        else:
            ext_info = ''
            # Clean comment and hidden_comment: remove \n and replace '\u2019' by "'"
            if ('comment' in obs_data['sightings'][0]['observers'][0]):
                obs_data['sightings'][0]['observers'][0]['comment'] = obs_data['sightings'][0]['observers'][0]['comment'].replace('\n', ' ')
                obs_data['sightings'][0]['observers'][0]['comment'] = obs_data['sightings'][0]['observers'][0]['comment'].replace('\u2019', "'")
            if ('hidden_comment' in obs_data['sightings'][0]['observers'][0]):
                obs_data['sightings'][0]['observers'][0]['hidden_comment'] = obs_data['sightings'][0]['observers'][0]['hidden_comment'].replace('\n', ' ')
                obs_data['sightings'][0]['observers'][0]['hidden_comment'] = obs_data['sightings'][0]['observers'][0]['hidden_comment'].replace('\u2019', "'")

            # Make sure estimation_code is filled
            if (len(obs_data['sightings'][0]['observers'][0]['estimation_code']) == 0):
                obs_data['sightings'][0]['observers'][0]['estimation_code'] = 'EXACT_VALUE'

            # Add mortality
            obs_data['sightings'][0]['observers'][0]['has_death'] = '2'
            obs_data['sightings'][0]['observers'][0]['extended_info'] = {'mortality': {'cause': mortality, 'time_found': '', 'comment': ''}}
            # Work only on sighting, and merge at the end
            if 'forms' in data_decoded['data']:
                data_decoded['data']['forms'][0] = obs_data
            else:
                data_decoded['data'] = obs_data
            # print('Modifying observation')
            # pp = pprint.PrettyPrinter(indent=1, width=120)
            # pp.pprint(data_decoded)

            mod_data = json.dumps(data_decoded, ensure_ascii=False)
            # print(mod_data)
            resp = requests.put(url=protected_url + obs_num,
                                auth=oauth,
                                params=params,
                                data=mod_data
                                )
            if resp.status_code != 200:
                print('PUT status code = {} : {}, for observation {}'.format(resp.status_code, resp.text, obs_num))
                return([obs_num, -1, resp.status_code, resp.text, mortality])
    else:
        ext_info = '-1'

    return([obs_num, nb_sightings, nb_observer, ext_info, mortality])


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
            cause = mortality_cause(row[2])
            print('Line {:>5}, observation number {:>8}, cause {}'.format(row_num, sighting_number, cause))
            # Add to list
            obs_list += [modify_obs(sighting_number, cause)]
            row_num += 1

    # pp = pprint.PrettyPrinter(indent=1, width=120)
    # pp.pprint(obs_list)

    with open('nb_obs.csv', 'w', newline='') as csvout:
        spamwriter = csv.writer(csvout, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        print('Opened output')
        for row in obs_list:
            spamwriter.writerow(row)

# Main wrapper
if __name__ == "__main__":
    main(sys.argv[1:])
