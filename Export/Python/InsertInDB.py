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

from bisect import bisect_left, bisect_right
from operator import itemgetter
from pprint import pprint

class SortedCollection(object):
    '''Sequence sorted by a key function.

    SortedCollection() is much easier to work with than using bisect() directly.
    It supports key functions like those use in sorted(), min(), and max().
    The result of the key function call is saved so that keys can be searched
    efficiently.

    Instead of returning an insertion-point which can be hard to interpret, the
    five find-methods return a specific item in the sequence. They can scan for
    exact matches, the last item less-than-or-equal to a key, or the first item
    greater-than-or-equal to a key.

    Once found, an item's ordinal position can be located with the index() method.
    New items can be added with the insert() and insert_right() methods.
    Old items can be deleted with the remove() method.

    The usual sequence methods are provided to support indexing, slicing,
    length lookup, clearing, copying, forward and reverse iteration, contains
    checking, item counts, item removal, and a nice looking repr.

    Finding and indexing are O(log n) operations while iteration and insertion
    are O(n).  The initial sort is O(n log n).

    The key function is stored in the 'key' attibute for easy introspection or
    so that you can assign a new key function (triggering an automatic re-sort).

    In short, the class was designed to handle all of the common use cases for
    bisect but with a simpler API and support for key functions.

    >>> from pprint import pprint
    >>> from operator import itemgetter

    >>> s = SortedCollection(key=itemgetter(2))
    >>> for record in [
    ...         ('roger', 'young', 30),
    ...         ('angela', 'jones', 28),
    ...         ('bill', 'smith', 22),
    ...         ('david', 'thomas', 32)]:
    ...     s.insert(record)

    >>> pprint(list(s))         # show records sorted by age
    [('bill', 'smith', 22),
     ('angela', 'jones', 28),
     ('roger', 'young', 30),
     ('david', 'thomas', 32)]

    >>> s.find_le(29)           # find oldest person aged 29 or younger
    ('angela', 'jones', 28)
    >>> s.find_lt(28)           # find oldest person under 28
    ('bill', 'smith', 22)
    >>> s.find_gt(28)           # find youngest person over 28
    ('roger', 'young', 30)

    >>> r = s.find_ge(32)       # find youngest person aged 32 or older
    >>> s.index(r)              # get the index of their record
    3
    >>> s[3]                    # fetch the record at that index
    ('david', 'thomas', 32)

    >>> s.key = itemgetter(0)   # now sort by first name
    >>> pprint(list(s))
    [('angela', 'jones', 28),
     ('bill', 'smith', 22),
     ('david', 'thomas', 32),
     ('roger', 'young', 30)]

    '''

    def __init__(self, iterable=(), key=None):
        self._given_key = key
        key = (lambda x: x) if key is None else key
        decorated = sorted((key(item), item) for item in iterable)
        self._keys = [k for k, item in decorated]
        self._items = [item for k, item in decorated]
        self._key = key

    def _getkey(self):
        return self._key

    def _setkey(self, key):
        if key is not self._key:
            self.__init__(self._items, key=key)

    def _delkey(self):
        self._setkey(None)

    key = property(_getkey, _setkey, _delkey, 'key function')

    def clear(self):
        self.__init__([], self._key)

    def copy(self):
        return self.__class__(self, self._key)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, i):
        return self._items[i]

    def __iter__(self):
        return iter(self._items)

    def __reversed__(self):
        return reversed(self._items)

    def __repr__(self):
        return '%s(%r, key=%s)' % (
            self.__class__.__name__,
            self._items,
            getattr(self._given_key, '__name__', repr(self._given_key))
        )

    def __reduce__(self):
        return self.__class__, (self._items, self._given_key)

    def __contains__(self, item):
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return item in self._items[i:j]

    def index(self, item):
        'Find the position of an item.  Raise ValueError if not found.'
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return self._items[i:j].index(item) + i

    def count(self, item):
        'Return number of occurrences of item'
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return self._items[i:j].count(item)

    def insert(self, item):
        'Insert a new item.  If equal keys are found, add to the left'
        k = self._key(item)
        i = bisect_left(self._keys, k)
        self._keys.insert(i, k)
        self._items.insert(i, item)

    def insert_right(self, item):
        'Insert a new item.  If equal keys are found, add to the right'
        k = self._key(item)
        i = bisect_right(self._keys, k)
        self._keys.insert(i, k)
        self._items.insert(i, item)

    def remove(self, item):
        'Remove first occurence of item.  Raise ValueError if not found'
        i = self.index(item)
        del self._keys[i]
        del self._items[i]

    def exists(self, k):
        'Return True if key already exists.'
        i = bisect_left(self._keys, k)
        if i != len(self) and self._keys[i] == k:
            return True
        else:
            return False

    def find(self, k):
        'Return first item with a key == k.  Raise ValueError if not found.'
        i = bisect_left(self._keys, k)
        if i != len(self) and self._keys[i] == k:
            return self._items[i]
        raise ValueError('No item found with key equal to: %r' % (k,))

    def find_le(self, k):
        'Return last item with a key <= k.  Raise ValueError if not found.'
        i = bisect_right(self._keys, k)
        if i:
            return self._items[i-1]
        raise ValueError('No item found with key at or below: %r' % (k,))

    def find_lt(self, k):
        'Return last item with a key < k.  Raise ValueError if not found.'
        i = bisect_left(self._keys, k)
        if i:
            return self._items[i-1]
        raise ValueError('No item found with key below: %r' % (k,))

    def find_ge(self, k):
        'Return first item with a key >= equal to k.  Raise ValueError if not found'
        i = bisect_left(self._keys, k)
        if i != len(self):
            return self._items[i]
        raise ValueError('No item found with key at or above: %r' % (k,))

    def find_gt(self, k):
        'Return first item with a key > k.  Raise ValueError if not found'
        i = bisect_right(self._keys, k)
        if i != len(self):
            return self._items[i]
        raise ValueError('No item found with key above: %r' % (k,))



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

    # if (options.verbose) :
    #     logger.setLevel(logging.DEBUG)

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

    # Insert or update in postgres observations read from json files
    # Should be insert most of the time, but observations can be modified on site during download
    # and be dowloaded twice. To manage this case, we keep a list of inserted observations
    inserted_obs = SortedCollection(key=itemgetter(0))
    logging.info('Inserting observations in database {}'.format(evn_db_name))
    # Iterate over observation files
    for f in [pth for pth in Path.home().joinpath(evn_file_store + '/' + options.site).glob('observations*.json.gz')]:
        # Read observations from json file
        logging.debug('Reading from {}'.format(str(f)))
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
            # Keep track of insertions
            obs_id = json_obs['observers'][0]['id_sighting']
            if (inserted_obs.exists(obs_id)):
                logging.warning('Observation {} was already downloaded, updating it'.format(obs_id))
                cur.execute('UPDATE {}.observations_json SET sightings=(%s), update_ts=(%s), coord_lat=(%s), coord_lon=(%s) WHERE id_sighting = (%s)'.format(evn_db_schema),
                            (json.dumps(json_obs),
                             update_date,
                             json_obs['observers'][0]['coord_lat'],
                             json_obs['observers'][0]['coord_lon'],
                             obs_id))
            else :
                inserted_obs.insert((obs_id, update_date))
                cur.execute('INSERT INTO {}.observations_json (id_sighting, sightings, update_ts, coord_lat, coord_lon) VALUES (%s, %s, %s, %s, %s)'.format(evn_db_schema),
                            (obs_id,
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
                    # Keep track of insertions
                    obs_id = json_obs['observers'][0]['id_sighting']
                    if (inserted_obs.exists(obs_id)):
                        logging.warning('Observation {} was already downloaded, updating it'.format(obs_id))
                        cur.execute('UPDATE {}.observations_json SET sightings=(%s), update_ts=(%s), coord_lat=(%s), coord_lon=(%s) WHERE id_sighting = (%s)'.format(evn_db_schema),
                                    (json.dumps(json_obs),
                                     update_date,
                                     json_obs['observers'][0]['coord_lat'],
                                     json_obs['observers'][0]['coord_lon'],
                                     obs_id))
                    else :
                        inserted_obs.insert((obs_id, update_date))
                        cur.execute('INSERT INTO {}.observations_json (id_sighting, sightings, update_ts, coord_lat, coord_lon) VALUES (%s, %s, %s, %s, %s)'.format(evn_db_schema),
                                    (obs_id,
                                     json.dumps(json_obs),
                                     update_date,
                                     json_obs['observers'][0]['coord_lat'],
                                     json_obs['observers'][0]['coord_lon']))

        # Commit to database
        conn.commit()

    # Read species from json file
    # Iterate over species files
    logging.info('Inserting species in database {}'.format(evn_db_name))
    for f in [pth for pth in Path.home().joinpath(evn_file_store + '/' + options.site).glob('species*.json.gz')]:
        logging.debug('Reading from {}'.format(str(f)))
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

    # Read local_admin_units from json file
    # Iterate over files
    logging.info('Inserting local_admin_units in database {}'.format(evn_db_name))
    for f in [pth for pth in Path.home().joinpath(evn_file_store + '/' + options.site).glob('local_admin_units*.json.gz')]:
        logging.debug('Reading from {}'.format(str(f)))
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

    # Read places from json file
    # Iterate over files
    logging.info('Inserting places in database {}'.format(evn_db_name))
    for f in [pth for pth in Path.home().joinpath(evn_file_store + '/' + options.site).glob('places*.json.gz')]:
        logging.debug('Reading from {}'.format(str(f)))
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

    # Close communication with the database
    logging.info('Closing database {}'.format(evn_db_name))
    cur.close()
    conn.close()

# Main wrapper
if __name__ == "__main__":
    main(sys.argv[1:])
