#!/usr/bin/env python3
"""
InsertInDB: stores json sightings in PG database.

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

import json
import gzip
import psycopg2

# version of the program:
__version__= "0.1.1" #VERSION#

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level = logging.DEBUG)

def script_shortname():
    """return the name of this script without a path component."""
    return os.path.basename(sys.argv[0])

def print_usage():
    """print a short summary of the scripts function."""
    print(('%-20s: Chargement dans BD Postgresql des données Biolovision '+\
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
                      help='Traces de mise au point.')

    parser.add_option('-s', '--site',
                      action='store',
                      dest='site',
                      help='Nom du site, utilisé pour sélectionner le fichier de paramétrage.')

    (options, args) = parser.parse_args()
    # print(sys.argv[1:])
    # print(options)
    # print(args)
    # sys.exit()

    # Read configuration parameters
    config = configparser.ConfigParser()
    config.read(str(Path.home()) + '/.evn_' + options.site + '.ini')

    # Import parameters in local variables
    evn_file_store = config['site']['evn_file_store']
    evn_db_host = config['database']['evn_db_host']
    evn_db_port = config['database']['evn_db_port']
    evn_db_name = config['database']['evn_db_name']
    evn_db_schema = config['database']['evn_db_schema']
    evn_db_group = config['database']['evn_db_group']
    evn_db_user = config['database']['evn_db_user']
    evn_db_pw = config['database']['evn_db_pw']
    evn_sql_scripts = config['database']['evn_sql_scripts']

    logging.info('Opening database {}'.format(evn_db_name))
    # Connect to evn database
    conn = psycopg2.connect('dbname={} user={} password={}'.format(evn_db_name, evn_db_user, evn_db_pw))

    # Open a cursor to perform database operations
    cur = conn.cursor()

    # Read observations from json file
    # Iterate over observation files
    for f in [pth for pth in Path.home().joinpath(evn_file_store + "/json").glob('observations*.json.gz')]:
        logging.info('Reading from {}'.format(str(f)))
        with gzip.open(str(f), 'rb', 9) as g:
            obs_chunk = json.loads(g.read().decode())

        # Insert simple sightings, each row contains id, update timestamp and full json body
        for i in range(0, len(obs_chunk['data']['sightings'])):
            json_obs = obs_chunk['data']['sightings'][i]
            # Find last update timestamp
            if ('update_date' in json_obs['observers'][0]):
                update_date = json_obs['observers'][0]['update_date']['@timestamp']
            else:
                update_date = json_obs['observers'][0]['insert_date']['@timestamp']
            # Insert row
            cur.execute('INSERT INTO {}.observations_json (id_sighting, sightings, update_ts, coord_lat, coord_lon) VALUES (%s, %s, %s, %s, %s)'.format(evn_db_schema),
                        (json_obs['observers'][0]['id_sighting'],
                         json.dumps(json_obs),
                         update_date,
                         json_obs['observers'][0]['coord_lat'],
                         json_obs['observers'][0]['coord_lon']))

        # Insert sightings from forms, each row contains id, update timestamp and full json body
        # TODO: create forms record in another table
        if ('forms' in obs_chunk['data']):
            for f in range(0, len(obs_chunk['data']['forms'])):
                for i in range(0, len(obs_chunk['data']['forms'][f]['sightings'])):
                    json_obs = obs_chunk['data']['forms'][f]['sightings'][i]
                    # Find last update timestamp
                    if ('update_date' in json_obs['observers'][0]):
                        update_date = json_obs['observers'][0]['update_date']['@timestamp']
                    else:
                        update_date = json_obs['observers'][0]['insert_date']['@timestamp']
                    # Insert row
                    cur.execute('INSERT INTO {}.observations_json (id_sighting, sightings, update_ts, coord_lat, coord_lon) VALUES (%s, %s, %s, %s, %s)'.format(evn_db_schema),
                                (json_obs['observers'][0]['id_sighting'],
                                 json.dumps(json_obs),
                                 update_date,
                                 json_obs['observers'][0]['coord_lat'],
                                 json_obs['observers'][0]['coord_lon']))

        # Commit to database
        conn.commit()

    # Refresh view
    cur.execute('REFRESH MATERIALIZED VIEW {}.observations WITH DATA'.format(evn_db_schema))
    conn.commit()

    # Read species from json file
    # Iterate over species files
    for f in [pth for pth in Path.home().joinpath(evn_file_store + "/json").glob('species*.json.gz')]:
        logging.info('Reading from {}'.format(str(f)))
        with gzip.open(str(f), 'rb', 9) as g:
            species_chunk = json.loads(g.read().decode())

        # Insert simple sightings, each row contains id and full json body
        for i in range(0, len(species_chunk['data'])):
            json_specie = species_chunk['data'][i]
            # Insert row
            cur.execute('INSERT INTO {}.species_json (id_specie, specie) VALUES (%s, %s)'.format(evn_db_schema),
                        (json_specie['id'],
                         json.dumps(json_specie)
                         ))

    # Commit to database, once for all species
    conn.commit()

    # Refresh view
    cur.execute('REFRESH MATERIALIZED VIEW {}.species WITH DATA'.format(evn_db_schema))
    conn.commit()

    # Read local_admin_units from json file
    # Iterate over files
    for f in [pth for pth in Path.home().joinpath(evn_file_store + "/json").glob('local_admin_units*.json.gz')]:
        logging.info('Reading from {}'.format(str(f)))
        with gzip.open(str(f), 'rb', 9) as g:
            local_admin_units_chunk = json.loads(g.read().decode())

        # Insert simple local_admin_unit, each row contains id and full json body
        for i in range(0, len(local_admin_units_chunk['data'])):
            json_local_admin_unit = local_admin_units_chunk['data'][i]
            # Insert row
            cur.execute('INSERT INTO {}.local_admin_units_json (id_local_admin_unit, local_admin_unit, coord_lat, coord_lon) VALUES (%s, %s, %s, %s)'.format(evn_db_schema),
                        (json_local_admin_unit['id'],
                         json.dumps(json_local_admin_unit),
                         json_local_admin_unit['coord_lat'],
                         json_local_admin_unit['coord_lon']
                         ))

    # Commit to database, once for all local_admin_units
    conn.commit()

    # Refresh view
    cur.execute('REFRESH MATERIALIZED VIEW {}.local_admin_units WITH DATA'.format(evn_db_schema))
    conn.commit()

    # Read places from json file
    # Iterate over files
    for f in [pth for pth in Path.home().joinpath(evn_file_store + "/json").glob('places*.json.gz')]:
        logging.info('Reading from {}'.format(str(f)))
        with gzip.open(str(f), 'rb', 9) as g:
            places_chunk = json.loads(g.read().decode())

        # Insert simple place, each row contains id and full json body
        for i in range(0, len(places_chunk['data'])):
            json_place = places_chunk['data'][i]
            # Insert row
            cur.execute('INSERT INTO {}.places_json (id_place, place, coord_lat, coord_lon) VALUES (%s, %s, %s, %s)'.format(evn_db_schema),
                        (json_place['id'],
                         json.dumps(json_place),
                         json_place['coord_lat'],
                         json_place['coord_lon']
                         ))

    # Commit to database, once for all places
    conn.commit()

    # Refresh view
    cur.execute('REFRESH MATERIALIZED VIEW {}.places WITH DATA'.format(evn_db_schema))
    conn.commit()

    # Close communication with the database
    logging.info('Closing database {}'.format(evn_db_name))
    cur.close()
    conn.close()

# Main wrapper
if __name__ == "__main__":
    main(sys.argv[1:])
