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

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


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
                      help='Traces de mise au point.',
                     )

    parser.add_option('-q', '--quiet',
                      action='store_false',
                      dest='verbose',
                      help='Traces de suivi minimales.',
                     )

    (options, args) = parser.parse_args()

    # Read configuration parameters
    config = configparser.ConfigParser()
    config.read(str(Path.home()) + '/.evn.ini')

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

    logger.info('Opening database {}'.format(evn_db_name))
    # Connect to an existing database
    conn = psycopg2.connect('dbname={} user={} password={}'.format(evn_db_name, evn_db_user, evn_db_pw))

    # Open a cursor to perform database operations
    cur = conn.cursor()

    # Insert 1 row, with id and json body
    cur.execute('INSERT INTO import.observations (id_sighting, sightings) VALUES (%s, %s)',
    (1, "{}"))

    # Close communication with the database
    cur.close()
    conn.close()

# Main wrapper
if __name__ == "__main__":
    main(sys.argv[1:])
