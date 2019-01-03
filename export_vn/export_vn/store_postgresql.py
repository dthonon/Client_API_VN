"""Methods to store Biolovision data to Postgresql database.


Methods

- store_data      - Store generic data structure to file

Properties

-

"""
import sys
import logging
import json
from sqlalchemy import create_engine, update, select
from sqlalchemy import Table, Column, Integer, String, Float, DateTime
from sqlalchemy import MetaData, ForeignKey

# version of the program:
__version__ = "0.1.1" #VERSION#

class StorePostgresqlException(Exception):
    """An exception occurred while handling download or store. """

class StorePostgresql:
    """Provides store to Postgresql database method."""

    def __init__(self, config):
        self._config = config
        # Get tables definition from Postgresql DB
        db_string = 'postgres+psycopg2://' + \
                    self._config.db_user + \
                    ':' +\
                    self._config.db_pw + \
                    '@' + \
                    self._config.db_host + \
                    ':' + \
                    self._config.db_port + \
                    '/' + \
                    self._config.db_name
        dbschema = self._config.db_schema
        self._metadata = MetaData(schema=dbschema)
        logging.info('Connecting to database %s', self._config.db_name)

        # Connect
        self._db = create_engine(db_string, echo=False)
        conn = self._db.connect()
        conn.execute('SET search_path TO {},public'.format(dbschema))

        # Get dbtable definition
        self._metadata.reflect(bind=self._db)
        for t in self._metadata.tables:
            logging.debug('Found table: %s', t)
        self._taxo_groups_json_def = self._metadata.tables[dbschema + '.taxo_groups_json']
        self._local_admin_units_json_def = self._metadata.tables[dbschema + '.local_admin_units_json']
        self._observations_json_def = self._metadata.tables[dbschema + '.observations_json']
        self._species_json_def = self._metadata.tables[dbschema + '.species_json']
        self._places_json_def = self._metadata.tables[dbschema + '.places_json']

        # Finished with DB
        conn.close()

    # ----------------
    # Internal methods
    # ----------------
    def _store_simple(self, controler, items_dict):
        """Write items_dict to database.

        Converts each element to JSON and store to database in a tables
        named from controler.

        Parameters
        ----------
        controler : str
            Name of API controler.
        items_dict : dict
            Data returned from API call.

        """

        # Loop on data array to store each element to database
        conn = self._db.connect()
        for elem in items_dict['data']:
            # Convert to json
            items_json = json.dumps(elem, sort_keys=True, indent=4, separators=(',', ': '))
            logging.debug('Storing element %s',
                          items_json)
            stmt = select([self._local_admin_units_json_def.c.id_local_admin_unit]).\
                    where(self._local_admin_units_json_def.c.id_local_admin_unit==elem['id'])
            result = conn.execute(stmt)
            row = result.fetchone()
            if row == None:
                logging.debug('Element not found in database, inserting new row')
                stmt = self._local_admin_units_json_def.insert().\
                        values(id_local_admin_unit=elem['id'],
                               site=self._config.site,
                               local_admin_unit=items_json)
            else:
                logging.info('Element %s found in database, updating row', row[0])
                stmt = self._local_admin_units_json_def.update().\
                        where(self._local_admin_units_json_def.c.id_local_admin_unit==elem['id']).\
                        values(id_local_admin_unit=elem['id'],
                               site=self._config.site,
                               local_admin_unit=items_json)
            result = conn.execute(stmt)

        # Finished with DB
        conn.close()

    # ---------------
    # External methods
    # ---------------
    def store(self, controler, seq, items_dict):
        """Write items_dict to database.

        Processing depends on controler, as items_dict structure varies.
        Converts each element to JSON and store to database in a tables
        named from controler.

        Parameters
        ----------
        controler : str
            Name of API controler.
        seq : str
            (Composed) sequence of data stream => Unused for db
        items_dict : dict
            Data returned from API call.

        """
        if controler == 'local_admin_units':
            self._store_simple(controler, items_dict)

        return
