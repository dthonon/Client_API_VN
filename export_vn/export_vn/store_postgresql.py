"""Methods to store Biolovision data to Postgresql database.


Methods

- store_data      - Store generic data structure to file

Properties

-

"""
import sys
import logging
import json
from sqlalchemy import create_engine, select
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

    # ---------------
    # Generic methods
    # ---------------
    def store(self, controler, seq, items_dict):
        """Write data to file.

        Processing depends on controler, as items_dict structure varies.
        Converts to JSON and store to file, named from
        controler and seq.

        Parameters
        ----------
        controler : str
            Name of API controler.
        seq : str
            (Composed) sequence of data stream.
        controler : dict
            Data returned from API call.

        """

        # Get data from Postgresql DB
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
        dbtable = 'taxo_groups_json'
        metadata = MetaData(schema=dbschema)
        logging.info('Connecting to db %s', db_string)

        # Connect
        db = create_engine(db_string, echo=False)
        conn = db.connect()
        conn.execute('SET search_path TO {},public'.format(dbschema))

        # Get dbtable definition
        dbtable_def = Table(dbtable, metadata, autoload=True, autoload_with=db)
        for c in dbtable_def.columns:
            logging.info('Column: %s', c.name)

        # Finished with DB
        conn.close()

        # # Store to file
        # if (len(items_dict['data']) > 0):
        #     # Convert to json
        #     logging.debug('Converting to json %d items',
        #                   len(items_dict['data']))
        #     items_json = json.dumps(items_dict, sort_keys=True, indent=4, separators=(',', ': '))


            # log = Table(dbtable, metadata,
            #               Column('log_date', DateTime),
            #               Column('name', String),
            #               Column('credit', Float),
            #               Column('workunits', Integer),
            #               Column('primes', Integer)
            #               )
            #
            # # Select\n",
            # s = select([log])\n",
            # result = conn.execute(s)
            # rows = result.fetchall()
        return
