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
        self._table_defs = {'taxo_groups': {'type': 'simple',
                                            'metadata': None},
                            'local_admin_units': {'type': 'simple',
                                                                'metadata': None},
                            'observations': {'type': 'simple',
                                                                'metadata': None},
                            'species': {'type': 'simple',
                                                                'metadata': None},
                            'places': {'type': 'simple',
                                                                'metadata': None},
                            'territorial_units': {'type': 'simple',
                                                                'metadata': None}}
        self._table_defs['taxo_groups']['metadata'] = self._metadata.tables[dbschema + '.taxo_groups_json']
        self._table_defs['local_admin_units']['metadata'] = self._metadata.tables[dbschema + '.local_admin_units_json']
        self._table_defs['observations']['metadata'] = self._metadata.tables[dbschema + '.observations_json']
        self._table_defs['species']['metadata'] = self._metadata.tables[dbschema + '.species_json']
        self._table_defs['places']['metadata'] = self._metadata.tables[dbschema + '.places_json']
        self._table_defs['territorial_units']['metadata'] = self._metadata.tables[dbschema + '.territorial_units_json']

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
        logging.info('Storing %d items from %s to database', len(items_dict['data']), controler)
        conn = self._db.connect()
        for elem in items_dict['data']:
            # Convert to json
            items_json = json.dumps(elem)
            logging.debug('Storing element %s',
                          items_json)
            stmt = select([self._table_defs[controler]['metadata'].c.id]).\
                    where(self._table_defs[controler]['metadata'].c.id==elem['id'])
            result = conn.execute(stmt)
            row = result.fetchone()
            if row == None:
                logging.debug('Element not found in database, inserting new row')
                stmt = self._table_defs[controler]['metadata'].insert().\
                        values(id=elem['id'],
                               site=self._config.site,
                               item=items_json)
            else:
                logging.debug('Element %s found in database, updating row', row[0])
                stmt = self._table_defs[controler]['metadata'].update().\
                        where(self._table_defs[controler]['metadata'].c.id==elem['id']).\
                        values(id=elem['id'],
                               site=self._config.site,
                               item=items_json)
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
        if self._table_defs[controler]['type'] == 'simple':
            self._store_simple(controler, items_dict)
        else:
            raise StorePostgresqlException('Not implemented')

        return
