"""Methods to store Biolovision data to Postgresql database.


Methods

- store_data      - Store generic data structure to file

Properties

-

"""
import logging
from datetime import date

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pyproj import Transformer
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    BigInteger,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    create_engine,
    exc,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.engine.url import URL
from sqlalchemy.sql import and_

from . import _, __version__

# from uuid import uuid4


logger = logging.getLogger("transfer_vn.store_postgresql")


class StorePostgresqlException(Exception):
    """An exception occurred while handling download or store. """


class ObservationItem:
    """Properties of an observation, for writing to DB."""

    def __init__(self, site, metadata, conn, transformer, elem, form=None):
        """Item elements.

        Parameters
        ----------
        site : str
            VisioNature site, for column storage.
        metadata :
            sqlalchemy metadata for observation table.
        conn :
            sqlalchemy connection to database
        transformer :
            pyproj transformer used to create local coordinates
        elem : dict
            Single observation to process and store.
        form : str
            id_form_universal if in form, or None
        """
        self._site = site
        self._metadata = metadata
        self._conn = conn
        self._transformer = transformer
        self._elem = elem
        self._form = form
        return None

    @property
    def site(self):
        """Return site."""
        return self._site

    @property
    def metadata(self):
        """Return metadata."""
        return self._metadata

    @property
    def conn(self):
        """Return conn."""
        return self._conn

    @property
    def transformer(self):
        """Return transformer."""
        return self._transformer

    @property
    def elem(self):
        """Return elem."""
        return self._elem

    @property
    def form(self):
        """Return form."""
        return self._form


def store_1_observation(item):
    """Process and store a single observation.

    - find insert or update date
    - simplify data to remove redundant items: dates... (TBD)
    - add x, y transform to local coordinates
    - store json in Postgresql

    Parameters
    ----------
    item : ObservationItem
        Observation item containing all parameters.
    """
    # Insert simple sightings,
    # each row contains id, update timestamp and full json body
    elem = item.elem
    logger.debug(
        _("Storing observation %s to database"), elem["observers"][0]["id_sighting"]
    )
    # Find last update timestamp
    if "update_date" in elem["observers"][0]:
        # update_date = elem['observers'][0]['update_date']['@timestamp']
        update_date = elem["observers"][0]["update_date"]
    else:
        # update_date = elem['observers'][0]['insert_date']['@timestamp']
        update_date = elem["observers"][0]["insert_date"]

    # Add Lambert x, y transform to local coordinates
    (
        elem["observers"][0]["coord_x_local"],
        elem["observers"][0]["coord_y_local"],
    ) = item.transformer(
        elem["observers"][0]["coord_lon"], elem["observers"][0]["coord_lat"]
    )

    # Store in Postgresql
    metadata = item.metadata
    site = item.site
    insert_stmt = insert(metadata).values(
        id=elem["observers"][0]["id_sighting"],
        site=site,
        update_ts=update_date,
        id_form_universal=item.form,
        item=elem,
    )
    do_update_stmt = insert_stmt.on_conflict_do_update(
        constraint=metadata.primary_key,
        set_=dict(update_ts=update_date, item=elem, id_form_universal=item.form),
        where=(metadata.c.update_ts < update_date),
    )

    item.conn.execute(do_update_stmt)
    return None


class PostgresqlUtils:
    """Provides create and delete Postgresql database method."""

    def __init__(self, config):
        self._config = config

    # ----------------
    # Internal methods
    # ----------------
    def _create_table(self, name, *cols):
        """Check if table exists, and create it if not

        Parameters
        ----------
        name : str
            Table name.
        cols : list
            Data returned from API call.

        """
        # Store to database, if enabled
        if self._config.db_enabled:
            if (
                self._config.db_schema_import + "." + name
            ) not in self._metadata.tables:
                logger.info(_("Table %s not found => Creating it"), name)
                table = Table(name, self._metadata, *cols)
                table.create(self._db)
            else:
                logger.info(_("Table %s already exists => Keeping it"), name)
        return None

    def _create_download_log(self):
        """Create download_log table if it does not exist."""
        self._create_table(
            "download_log",
            Column("id", Integer, primary_key=True),
            Column("site", String, nullable=False, index=True),
            Column("controler", String, nullable=False),
            Column("download_ts", DateTime, server_default=func.now(), nullable=False),
            Column("error_count", Integer, index=True),
            Column("http_status", Integer, index=True),
            Column("comment", String),
            Column("length", Integer, index=True),
            Column("duration", BigInteger, index=True),
        )
        return None

    def _create_increment_log(self):
        """Create increment_log table if it does not exist."""
        self._create_table(
            "increment_log",
            Column("site", String, nullable=False),
            Column("taxo_group", Integer, nullable=False),
            Column("last_ts", DateTime, server_default=func.now(), nullable=False),
            PrimaryKeyConstraint("site", "taxo_group", name="increment_log_pk"),
        )
        return None

    def _create_entities_json(self):
        """Create entities_json table if it does not exist."""
        self._create_table(
            "entities_json",
            Column("id", Integer, nullable=False),
            Column("site", String, nullable=False),
            Column("item", JSONB, nullable=False),
            PrimaryKeyConstraint("id", "site", name="entities_json_pk"),
        )
        return None

    def _create_families_json(self):
        """Create families_json table if it does not exist."""
        self._create_table(
            "families_json",
            Column("id", Integer, nullable=False),
            Column("site", String, nullable=False),
            Column("item", JSONB, nullable=False),
            PrimaryKeyConstraint("id", "site", name="families_json_pk"),
        )
        return None

    def _create_field_groups_json(self):
        """Create field_groups_json table if it does not exist."""
        self._create_table(
            "field_groups_json",
            Column("id", Integer, nullable=False),
            Column("item", JSONB, nullable=False),
            PrimaryKeyConstraint("id", name="field_groups_json_pk"),
        )
        return None

    def _create_field_details_json(self):
        """Create field_details_json table if it does not exist."""
        self._create_table(
            "field_details_json",
            Column("id", String, nullable=False),
            Column("item", JSONB, nullable=False),
            PrimaryKeyConstraint("id", name="field_details_json_pk"),
        )
        return None

    def _create_forms_json(self):
        """Create forms_json table if it does not exist."""
        self._create_table(
            "forms_json",
            Column("id", Integer, nullable=False, index=True),
            Column("site", String, nullable=False),
            Column("item", JSONB, nullable=False),
            PrimaryKeyConstraint("id", "site", name="forms_json_pk"),
        )
        return None

    def _create_local_admin_units_json(self):
        """Create local_admin_units_json table if it does not exist."""
        self._create_table(
            "local_admin_units_json",
            Column("id", Integer, nullable=False),
            Column("site", String, nullable=False),
            Column("item", JSONB, nullable=False),
            PrimaryKeyConstraint("id", "site", name="local_admin_units_json_pk"),
        )
        return None

    # def _create_uuid_xref(self):
    #     """Create uuid_xref table if it does not exist."""
    #     self._create_table(
    #         "uuid_xref",
    #         Column("id", Integer, nullable=False, index=True),
    #         Column("site", String, nullable=False, index=True),
    #         Column("universal_id", String, nullable=False, index=True),
    #         Column("uuid", String, nullable=False, index=True),
    #         Column("alias", ARRAY(String), nullable=True),
    #         Column("update_ts", DateTime, server_default=func.now(), nullable=False),
    #         PrimaryKeyConstraint("id", "site", name="uuid_xref_json_pk"),
    #     )
    #     return None

    def _create_observations_json(self):
        """Create observations_json table if it does not exist."""
        self._create_table(
            "observations_json",
            Column("id", Integer, nullable=False, index=True),
            Column("site", String, nullable=False),
            Column("item", JSONB, nullable=False),
            Column("update_ts", Integer, nullable=False),
            Column("id_form_universal", String),
            PrimaryKeyConstraint("id", "site", name="observations_json_pk"),
        )
        return None

    def _create_observers_json(self):
        """Create observers_json table if it does not exist."""
        self._create_table(
            "observers_json",
            Column("id", Integer, nullable=False, index=True),
            Column("site", String, nullable=False),
            Column("id_universal", Integer, nullable=False, index=True),
            Column("item", JSONB, nullable=False),
            PrimaryKeyConstraint("id", "site", name="observers_json_pk"),
        )
        return None

    def _create_places_json(self):
        """Create places_json table if it does not exist."""
        self._create_table(
            "places_json",
            Column("id", Integer, nullable=False, index=True),
            Column("site", String, nullable=False),
            Column("item", JSONB, nullable=False),
            PrimaryKeyConstraint("id", "site", name="places_json_pk"),
        )
        return None

    def _create_species_json(self):
        """Create species_json table if it does not exist."""
        self._create_table(
            "species_json",
            Column("id", Integer, nullable=False, index=True),
            Column("site", String, nullable=False),
            Column("item", JSONB, nullable=False),
            PrimaryKeyConstraint("id", "site", name="species_json_pk"),
        )
        return None

    def _create_taxo_groups_json(self):
        """Create taxo_groups_json table if it does not exist."""
        self._create_table(
            "taxo_groups_json",
            Column("id", Integer, nullable=False),
            Column("site", String, nullable=False),
            Column("item", JSONB, nullable=False),
            PrimaryKeyConstraint("id", "site", name="taxo_groups_json_pk"),
        )
        return None

    def _create_territorial_units_json(self):
        """Create territorial_units_json table if it does not exist."""
        self._create_table(
            "territorial_units_json",
            Column("id", Integer, nullable=False),
            Column("site", String, nullable=False),
            Column("item", JSONB, nullable=False),
            PrimaryKeyConstraint("id", "site", name="territorial_units_json_pk"),
        )
        return None

    def _create_validations_json(self):
        """Create validations_json table if it does not exist."""
        self._create_table(
            "validations_json",
            Column("id", Integer, nullable=False),
            Column("site", String, nullable=False),
            Column("item", JSONB, nullable=False),
            PrimaryKeyConstraint("id", "site", name="validations_json_pk"),
        )
        return None

    # ---------------
    # External methods
    # ---------------
    def create_database(self):
        """Create database, roles..."""
        # Store to database, if enabled
        if self._config.db_enabled:
            # Connect first using postgres database, that always exists
            logger.info(
                _("Connecting to postgres database, to create %s database"),
                self._config.db_name,
            )
            db_url = {
                "drivername": "postgresql+psycopg2",
                "username": self._config.db_user,
                "password": self._config.db_pw,
                "host": self._config.db_host,
                "port": self._config.db_port,
                "database": "postgres",
            }
            db = create_engine(URL(**db_url), echo=False)
            conn = db.connect()
            conn.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            # Group role:
            text = """
                SELECT FROM pg_catalog.pg_roles WHERE rolname = '{db_group}'
                """.format(
                db_group=self._config.db_group
            )
            result = conn.execute(text)
            row = result.fetchone()
            if row is None:
                text = """
                    CREATE ROLE {db_group} NOLOGIN NOSUPERUSER INHERIT NOCREATEDB
                    NOCREATEROLE NOREPLICATION
                    """.format(
                    db_group=self._config.db_group
                )
            else:
                text = """
                    ALTER ROLE {db_group} NOLOGIN NOSUPERUSER INHERIT NOCREATEDB
                    NOCREATEROLE NOREPLICATION
                    """.format(
                    db_group=self._config.db_group
                )
            conn.execute(text)

            # Import role:
            text = "GRANT {} TO {}".format(self._config.db_group, self._config.db_user)
            conn.execute(text)

            # Create database:
            text = "CREATE DATABASE {} WITH OWNER = {}".format(
                self._config.db_name, self._config.db_group
            )
            conn.execute(text)
            text = "GRANT ALL ON DATABASE {} TO {}".format(
                self._config.db_name, self._config.db_group
            )
            conn.execute(text)
            conn.close()
            db.dispose()

        return None

    def drop_database(self):
        """Force session deconnection and drop database, roles..."""
        # Store to database, if enabled
        if self._config.db_enabled:
            logger.info(
                _("Connecting to postgres database, to delete %s database"),
                self._config.db_name,
            )
            db_url = {
                "drivername": "postgresql+psycopg2",
                "username": self._config.db_user,
                "password": self._config.db_pw,
                "host": self._config.db_host,
                "port": self._config.db_port,
                "database": "postgres",
            }
            db = create_engine(URL(**db_url), echo=False)
            conn = db.connect()
            conn.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            version = conn.dialect.server_version_info
            pid_column = "pid" if (version >= (9, 2)) else "procpid"

            text = """
            SELECT pg_terminate_backend(pg_stat_activity.%(pid_column)s)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '%(database)s'
            AND %(pid_column)s <> pg_backend_pid();
            """ % {
                "pid_column": pid_column,
                "database": self._config.db_name,
            }
            logger.debug(_("Dropping tables: %s"), text)
            conn.execute(text)
            text = "DROP DATABASE IF EXISTS {}".format(self._config.db_name)
            logger.debug(_("Dropping database: %s"), text)
            conn.execute(text)
            try:
                text = "DROP ROLE IF EXISTS {}".format(self._config.db_group)
                logger.debug(_("Dropping role: %s"), text)
                conn.execute(text)
            except exc.SQLAlchemyError as e:
                logger.warning(_("Error %s ignored when dropping role"), repr(e))

            conn.close()
            db.dispose()

        return None

    def create_json_tables(self):
        """Create all internal and jsonb tables."""
        # Store to database, if enabled
        if self._config.db_enabled:
            # Initialize interface to Postgresql DB
            db_url = {
                "drivername": "postgresql+psycopg2",
                "username": self._config.db_user,
                "password": self._config.db_pw,
                "host": self._config.db_host,
                "port": self._config.db_port,
                "database": self._config.db_name,
            }

            # Connect to database
            logger.info(
                _("Connecting to %s database, to finalize creation"),
                self._config.db_name,
            )
            self._db = create_engine(URL(**db_url), echo=False)
            conn = self._db.connect()

            # Add extensions
            text = "CREATE EXTENSION IF NOT EXISTS pgcrypto"
            conn.execute(text)
            text = "CREATE EXTENSION IF NOT EXISTS adminpack"
            conn.execute(text)
            text = 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'
            conn.execute(text)
            text = "CREATE EXTENSION IF NOT EXISTS postgis"
            conn.execute(text)
            text = "CREATE EXTENSION IF NOT EXISTS postgis_topology"
            conn.execute(text)

            # Create import schema
            text = "CREATE SCHEMA IF NOT EXISTS {} AUTHORIZATION {}".format(
                self._config.db_schema_import, self._config.db_group
            )
            conn.execute(text)

            # Enable privileges
            text = """
            ALTER DEFAULT PRIVILEGES
            GRANT INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLES
            TO postgres"""
            conn.execute(text)
            text = """
            ALTER DEFAULT PRIVILEGES
            GRANT INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLES
            TO {}""".format(
                self._config.db_group
            )
            conn.execute(text)

            # Set path to include VN import schema
            dbschema = self._config.db_schema_import
            self._metadata = MetaData(schema=dbschema)
            self._metadata.reflect(self._db)

            # Check if tables exist or else create them
            self._create_download_log()
            self._create_increment_log()

            self._create_entities_json()
            self._create_families_json()
            self._create_field_groups_json()
            self._create_field_details_json()
            self._create_forms_json()
            self._create_local_admin_units_json()
            # self._create_uuid_xref()
            self._create_observations_json()
            self._create_observers_json()
            self._create_places_json()
            self._create_species_json()
            self._create_taxo_groups_json()
            self._create_territorial_units_json()
            self._create_validations_json()

            conn.close()
            self._db.dispose()

        return None

    def count_json_obs(self):
        """Count observations stored in json table, by site and taxonomy.

        Returns
        -------
        dict
            Count of observations by site and taxonomy.
        """
        result = None
        # Store to database, if enabled
        if self._config.db_enabled:
            logger.info(_("Counting observations in database for all sites"))
            db_url = {
                "drivername": "postgresql+psycopg2",
                "username": self._config.db_user,
                "password": self._config.db_pw,
                "host": self._config.db_host,
                "port": self._config.db_port,
                "database": self._config.db_name,
            }

            # Connect and set path to include VN import schema
            logger.info(_("Connecting to database %s"), self._config.db_name)
            self._db = create_engine(URL(**db_url), echo=False)
            conn = self._db.connect()
            dbschema = self._config.db_schema_import
            self._metadata = MetaData(schema=dbschema)
            # self._metadata.reflect(self._db)

            text = """
            SELECT site, ((item->>0)::json->'species') ->> 'taxonomy' AS taxonomy, COUNT(id)
                FROM {}.observations_json
                GROUP BY site, ((item->>0)::json->'species') ->> 'taxonomy';
            """.format(
                dbschema
            )

            result = conn.execute(text).fetchall()

        return result

    def count_col_obs(self):
        """Count observations stored in column table, by site and taxonomy.

        Returns
        -------
        dict
            Count of observations by site and taxonomy.
        """
        result = None
        # Store to database, if enabled
        if self._config.db_enabled:
            logger.info(_("Counting observations in database for all sites"))
            db_url = {
                "drivername": "postgresql+psycopg2",
                "username": self._config.db_user,
                "password": self._config.db_pw,
                "host": self._config.db_host,
                "port": self._config.db_port,
                "database": self._config.db_name,
            }

            # Connect and set path to include VN import schema
            logger.info(_("Connecting to database %s"), self._config.db_name)
            self._db = create_engine(URL(**db_url), echo=False)
            conn = self._db.connect()
            dbschema = self._config.db_schema_vn
            self._metadata = MetaData(schema=dbschema)
            # self._metadata.reflect(self._db)

            text = """
            SELECT o.site, o.taxonomy, t.name, COUNT(o.id_sighting)
                FROM {}.observations AS o
                    LEFT JOIN {}.taxo_groups AS t
                        ON (o.taxonomy::integer = t.id AND o.site LIKE t.site)
                GROUP BY o.site, o.taxonomy, t.name
            """.format(
                dbschema, dbschema
            )

            result = conn.execute(text).fetchall()

        return result


class Postgresql:
    """Provides common access Postgresql database."""

    def __init__(self, config):
        self._config = config

        if self._config.db_enabled:
            # Initialize interface to Postgresql DB
            db_url = {
                "drivername": "postgresql+psycopg2",
                "username": self._config.db_user,
                "password": self._config.db_pw,
                "host": self._config.db_host,
                "port": self._config.db_port,
                "database": self._config.db_name,
            }

            dbschema = self._config.db_schema_import
            self._metadata = MetaData(schema=dbschema)
            logger.info(_("Connecting to database %s"), self._config.db_name)

            # Connect and set path to include VN import schema
            self._db = create_engine(URL(**db_url), echo=False)
            self._conn = self._db.connect()

            # Get dbtable definition
            self._metadata.reflect(bind=self._db, schema=dbschema)

            # Map Biolovision tables in a single dict for easy reference
            self._table_defs = {
                "entities": {"type": "simple", "metadata": None},
                "families": {"type": "simple", "metadata": None},
                "field_groups": {"type": "fields", "metadata": None},
                "field_details": {"type": "fields", "metadata": None},
                "forms": {"type": "others", "metadata": None},
                "local_admin_units": {"type": "geometry", "metadata": None},
                # "uuid_xref": {"type": "others", "metadata": None},
                "observations": {"type": "observation", "metadata": None},
                "observers": {"type": "observers", "metadata": None},
                "places": {"type": "geometry", "metadata": None},
                "species": {"type": "simple", "metadata": None},
                "taxo_groups": {"type": "simple", "metadata": None},
                "territorial_units": {"type": "simple", "metadata": None},
                "validations": {"type": "simple", "metadata": None},
            }
            self._table_defs["entities"]["metadata"] = self._metadata.tables[
                dbschema + ".entities_json"
            ]
            self._table_defs["families"]["metadata"] = self._metadata.tables[
                dbschema + ".families_json"
            ]
            self._table_defs["field_groups"]["metadata"] = self._metadata.tables[
                dbschema + ".field_groups_json"
            ]
            self._table_defs["field_details"]["metadata"] = self._metadata.tables[
                dbschema + ".field_details_json"
            ]
            self._table_defs["forms"]["metadata"] = self._metadata.tables[
                dbschema + ".forms_json"
            ]
            self._table_defs["local_admin_units"]["metadata"] = self._metadata.tables[
                dbschema + ".local_admin_units_json"
            ]
            # self._table_defs["uuid_xref"]["metadata"] = self._metadata.tables[
            #     dbschema + ".uuid_xref"
            # ]
            self._table_defs["observations"]["metadata"] = self._metadata.tables[
                dbschema + ".observations_json"
            ]
            self._table_defs["observers"]["metadata"] = self._metadata.tables[
                dbschema + ".observers_json"
            ]
            self._table_defs["places"]["metadata"] = self._metadata.tables[
                dbschema + ".places_json"
            ]
            self._table_defs["species"]["metadata"] = self._metadata.tables[
                dbschema + ".species_json"
            ]
            self._table_defs["taxo_groups"]["metadata"] = self._metadata.tables[
                dbschema + ".taxo_groups_json"
            ]
            self._table_defs["territorial_units"]["metadata"] = self._metadata.tables[
                dbschema + ".territorial_units_json"
            ]
            self._table_defs["validations"]["metadata"] = self._metadata.tables[
                dbschema + ".validations_json"
            ]

            # Create transformation
            self._transformer = Transformer.from_proj(
                4326, int(self._config.db_out_proj), always_xy=True
            )

        return None

    def __enter__(self):
        logger.debug(_("Entry into StorePostgresql"))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Finalize connections."""
        if self._config.db_enabled:
            logger.info(_("Closing connection to database %s"), self._config.db_name)
            self._conn.close()

    @property
    def version(self):
        """Return version."""
        return __version__


class ReadPostgresql(Postgresql):
    """Provides read from Postgresql database method."""

    # ----------------
    # External methods
    # ----------------
    def read(self, controler):
        """Read items from database.

        Parameters
        ----------
        controler : str
            Name of API controler.

        Returns
        -------
        dict
            Dict of items read from table.
        """

        logger.info(
            _("Reading from %s of site %s"),
            controler,
            self._config.site,
        )
        metadata = self._table_defs[controler]["metadata"]
        stmt = select([metadata.c.item]).where(metadata.c.site == self._config.site)
        return self._conn.execute(stmt).fetchall()


class StorePostgresql(Postgresql):
    """Provides store to Postgresql database method."""

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

        Returns
        -------
        int
            Count of items stored (not exact for observations, due to forms).
        """

        # Loop on data array to store each element to database
        logger.info(
            _("Storing %d items from %s of site %s"),
            len(items_dict["data"]),
            controler,
            self._config.site,
        )
        metadata = self._table_defs[controler]["metadata"]
        for elem in items_dict["data"]:
            # Convert to json
            logger.debug(_("Storing element %s"), elem)
            insert_stmt = insert(metadata).values(
                id=elem["id"], site=self._config.site, item=elem
            )
            do_update_stmt = insert_stmt.on_conflict_do_update(
                constraint=metadata.primary_key, set_=dict(item=elem)
            )
            self._conn.execute(do_update_stmt)

        return len(items_dict["data"])

    def _store_geometry(self, controler, items_dict):
        """Add local coordinates and pass to _store_simple.

        Add X, Y local coordinates to each item and then
        send to _store_simple for database storage

        Parameters
        ----------
        controler : str
            Name of API controler.
        items_dict : dict
            Data returned from API call.

        Returns
        -------
        int
            Count of items stored (not exact for observations, due to forms).
        """

        # Loop on data array to reproject
        for elem in items_dict["data"]:
            elem["coord_x_local"], elem["coord_y_local"] = self._transformer.transform(
                elem["coord_lon"], elem["coord_lat"]
            )
        return self._store_simple(controler, items_dict)

    def _store_fields(self, controler, items_dict):
        """Write items_dict to database, for field_groups and field_details.

        Converts each element to JSON and store to database in a tables
        named from controler.

        Parameters
        ----------
        controler : str
            Name of API controler.
        items_dict : dict
            Data returned from API call.

        Returns
        -------
        int
            Count of items stored (not exact for observations, due to forms).
        """

        # Loop on data array to store each element to database
        logger.info(_("Storing %d items from %s"), len(items_dict["data"]), controler)
        metadata = self._table_defs[controler]["metadata"]
        for elem in items_dict["data"]:
            logger.debug(_("Storing element %s"), elem)
            insert_stmt = insert(metadata).values(id=elem["id"], item=elem)
            do_update_stmt = insert_stmt.on_conflict_do_update(
                constraint=metadata.primary_key, set_=dict(item=elem)
            )
            self._conn.execute(do_update_stmt)

        return len(items_dict["data"])

    def _store_form(self, items_dict, transformer):
        """Write forms to database.

        Check if forms is in database and either insert or update.

        Parameters
        ----------
        items_dict : dict
            Forms data to store.
        transformer : Transformer.from_proj
            Projection transformer for adding local coordinates

        Returns
        -------
        int
            Count of items stored.
        """

        controler = "forms"
        logger.debug(
            _("Storing %d items from %s of site %s"),
            len(items_dict),
            controler,
            self._config.site,
        )

        # Add local coordinates
        if ("lon" in items_dict) and ("lat" in items_dict):
            items_dict["coord_x_local"], items_dict["coord_y_local"] = transformer(
                items_dict["lon"], items_dict["lat"]
            )

        # Convert to json
        logger.debug(_("Storing element %s"), items_dict)
        metadata = self._table_defs[controler]["metadata"]
        insert_stmt = insert(metadata).values(
            id=items_dict["@id"], site=self._config.site, item=items_dict
        )
        do_update_stmt = insert_stmt.on_conflict_do_update(
            constraint=metadata.primary_key, set_=dict(item=items_dict)
        )
        self._conn.execute(do_update_stmt)

        return len(items_dict)

    # def _store_uuid(self, obs_id, universal_id=""):
    #     """Creates UUID and store along id and site.

    #     If (id, site) does not exist:
    #     - creates an UID
    #     - store it, along with id, site, universal_id to table.

    #     Parameters
    #     ----------
    #     obs_id : str
    #         Observations id.
    #     universal_id : str
    #         Observations universal id.

    #     Returns
    #     -------
    #     int
    #         Count of items stored.
    #     """

    #     controler = "uuid_xref"
    #     metadata = self._table_defs[controler]["metadata"]
    #     insert_stmt = insert(metadata).values(
    #         id=obs_id,
    #         site=self._config.site,
    #         universal_id=universal_id,
    #         uuid=uuid4(),
    #         update_ts=datetime.now(),
    #     )
    #     do_nothing_stmt = insert_stmt.on_conflict_do_nothing(
    #         constraint=metadata.primary_key
    #     )
    #     self._conn.execute(do_nothing_stmt)

    #     return 1

    def _store_observation(self, controler, items_dict):
        """Iterate through observations or forms and store.

        Checks if sightings or forms and iterate on each sighting
        - find insert or update date
        - simplity data to remove redundant items: dates... (TBD)
        - add x, y transform to local coordinates
        - store json in Postgresql

        Parameters
        ----------
        controler : str
            Name of API controler.
        items_dict : dict
            Data returned from API call.

        Returns
        -------
        int
            Count of items stored (not exact for observations, due to forms).
        """
        # Insert simple sightings, each row contains id, update timestamp and
        # full json body
        nb_obs = 0
        logger.debug(
            _("Storing %d single observations"), len(items_dict["data"]["sightings"])
        )
        for i in range(0, len(items_dict["data"]["sightings"])):
            elem = items_dict["data"]["sightings"][i]
            # # Create UUID
            # self._store_uuid(
            #     elem["observers"][0]["id_sighting"],
            #     elem["observers"][0]["id_universal"],
            # )
            # Write observation to database
            store_1_observation(
                ObservationItem(
                    self._config.site,
                    self._table_defs[controler]["metadata"],
                    self._conn,
                    self._transformer.transform,
                    elem,
                )
            )
            nb_obs += 1

        if "forms" in items_dict["data"]:
            for f in range(0, len(items_dict["data"]["forms"])):
                if "@id" in items_dict["data"]["forms"][f]:
                    # It's a real form
                    forms_data = {}
                    if "id_form_universal" in items_dict["data"]["forms"][f]:
                        id_form_universal = items_dict["data"]["forms"][f][
                            "id_form_universal"
                        ]
                    else:
                        id_form_universal = None
                    for (k, v) in items_dict["data"]["forms"][f].items():
                        if k == "sightings":
                            dates = []
                            nb_s = len(v)
                            logger.debug("Storing %d observations in form %d", nb_s, f)
                            for i in range(0, nb_s):
                                # Find max and min dates
                                dates.append(
                                    date.fromtimestamp(int(v[i]["date"]["@timestamp"]))
                                )
                                # # Create UUID
                                # self._store_uuid(
                                #     v[i]["observers"][0]["id_sighting"],
                                #     v[i]["observers"][0]["id_universal"],
                                # )
                                store_1_observation(
                                    ObservationItem(
                                        self._config.site,
                                        self._table_defs[controler]["metadata"],
                                        self._conn,
                                        self._transformer.transform,
                                        v[i],
                                        id_form_universal,
                                    )
                                )
                                nb_obs += 1
                            # Add presumed start and stop date from observations
                            forms_data["date_start"] = min(dates).isoformat()
                            forms_data["date_stop"] = max(dates).isoformat()
                            # Add presumed observer from first observation
                            forms_data["@uid"] = v[0]["observers"][0]["@uid"]
                        else:
                            # Put everything except sightings in forms data
                            forms_data[k] = v
                    self._store_form(forms_data, self._transformer.transform)
                else:
                    # It's not a form, store it as a sighting
                    store_1_observation(
                        ObservationItem(
                            self._config.site,
                            self._table_defs[controler]["metadata"],
                            self._conn,
                            self._transformer.transform,
                            items_dict["data"]["forms"][f],
                            None,
                        )
                    )

        logger.debug(_("Stored %d observations or forms to database"), nb_obs)
        return nb_obs

    def _store_observers(self, controler, items_dict):
        """Write observers items_dict to database.

        Converts each element to JSON and store to database in a tables
        named from controler.

        Parameters
        ----------
        controler : str
            Name of API controler.
        items_dict : dict
            Data returned from API call.

        Returns
        -------
        int
            Count of items stored (not exact for observations, due to forms).
        """

        # Loop on data array to store each element to database
        logger.info(
            _("Storing %d observers from site %s"),
            len(items_dict["data"]),
            self._config.site,
        )
        metadata = self._table_defs[controler]["metadata"]
        for elem in items_dict["data"]:
            # Convert to json
            logger.debug(_("Storing element %s"), elem)
            insert_stmt = insert(metadata).values(
                id=elem["id"],
                id_universal=elem["id_universal"],
                site=self._config.site,
                item=elem,
            )
            do_update_stmt = insert_stmt.on_conflict_do_update(
                constraint=metadata.primary_key,
                set_=dict(id_universal=elem["id_universal"], item=elem),
            )
            self._conn.execute(do_update_stmt)

        return len(items_dict["data"])

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

        Returns
        -------
        int
            Count of items stored (not exact for observations, due to forms).
        """
        nb_item = 0
        # Store to database, if enabled
        if self._config.db_enabled:
            if self._table_defs[controler]["type"] == "observation":
                nb_item = self._store_observation(controler, items_dict)
            elif self._table_defs[controler]["type"] == "simple":
                nb_item = self._store_simple(controler, items_dict)
            elif self._table_defs[controler]["type"] == "geometry":
                nb_item = self._store_geometry(controler, items_dict)
            elif self._table_defs[controler]["type"] == "observers":
                nb_item = self._store_observers(controler, items_dict)
            elif self._table_defs[controler]["type"] == "fields":
                nb_item = self._store_fields(controler, items_dict)

            else:
                raise StorePostgresqlException(_("Not implemented"))

        return nb_item

    def delete_obs(self, obs_list):
        """Delete observations stored in database.

        Parameters
        ----------
        obs_list : list
            Data returned from API call.

        Returns
        -------
        int
            Count of items deleted.
        """
        nb_delete = 0
        # Store to database, if enabled
        if self._config.db_enabled:
            logger.info(_("Deleting %d observations from database"), len(obs_list))
            nb_delete = 0
            for obs in obs_list:
                nd = self._conn.execute(
                    self._table_defs["observations"]["metadata"]
                    .delete()
                    .where(
                        and_(
                            self._table_defs["observations"]["metadata"].c.id == obs,
                            self._table_defs["observations"]["metadata"].c.site
                            == self._config.site,
                        )
                    )
                )
                nb_delete += nd.rowcount

        return nb_delete

    def log(
        self,
        site,
        controler,
        error_count=0,
        http_status=0,
        comment="",
        length=0,
        duration=0,
    ):
        """Write download log entries to database.

        Parameters
        ----------
        site : str
            VN site name.
        controler : str
            Name of API controler.
        error_count : integer
            Number of errors during download.
        http_status : integer
            HTTP status of latest download.
        comment : str
            Optional comment, in free text.
        length : integer
            Optional length of data transfer
        duration : integer
            Optional duration of data transfer, in ms
        """
        # Store to database, if enabled
        if self._config.db_enabled:
            metadata = self._metadata.tables[
                self._config.db_schema_import + "." + "download_log"
            ]
            stmt = metadata.insert().values(
                site=site,
                controler=controler,
                error_count=error_count,
                http_status=http_status,
                comment=comment,
                length=length,
                duration=duration,
            )
            self._conn.execute(stmt)

        return None

    def increment_log(self, site, taxo_group, last_ts):
        """Write last increment timestamp to database.

        Parameters
        ----------
        site : str
            VN site name.
        taxo_group : str
            Taxo_group updated.
        last_ts : timestamp
            Timestamp of last update of this taxo_group.
        """
        # Store to database, if enabled
        if self._config.db_enabled:
            metadata = self._metadata.tables[
                self._config.db_schema_import + "." + "increment_log"
            ]

            insert_stmt = insert(metadata).values(
                taxo_group=taxo_group, site=site, last_ts=last_ts
            )
            do_update_stmt = insert_stmt.on_conflict_do_update(
                constraint=metadata.primary_key, set_=dict(last_ts=last_ts)
            )
            self._conn.execute(do_update_stmt)

        return None

    def increment_get(self, site, taxo_group):
        """Get last increment timestamp from database.

        Parameters
        ----------
        site : str
            VN site name.
        taxo_group : str
            Taxo_group updated.

        Returns
        -------
        timestamp
            Timestamp of last update of this taxo_group.
        """
        row = None
        # Store to database, if enabled
        if self._config.db_enabled:
            metadata = self._metadata.tables[
                self._config.db_schema_import + "." + "increment_log"
            ]
            stmt = select([metadata.c.last_ts]).where(
                and_(metadata.c.taxo_group == taxo_group, metadata.c.site == site)
            )
            result = self._conn.execute(stmt)
            row = result.fetchone()

        if row is None:
            return None
        else:
            return row[0]
