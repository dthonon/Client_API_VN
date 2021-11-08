Client-API-VN v2.9.3 (2021-11-08)
=================================

Bugfixes
--------

- Observations were not deleted from PG database if deleted in Biolovision site.
  This is fixed and deletion are now synchronized.
  A full download is required to delete previous observations. (`#171 <https://framagit.org/lpo/Client_API_VN/issues/171>`_)
- Parameter max_chunks has been raised, by default to 1000, 
  to allow for much larger transfers.
  Please consider modifying your existing YAML configuration files. (`#178 <https://framagit.org/lpo/Client_API_VN/issues/178>`_)


Client-API-VN v2.9.2 (2021-11-03)
=================================

Bugfixes
--------

- In download_log table, the number of observations updated is now correct. (`#157 <https://framagit.org/lpo/Client_API_VN/issues/157>`_)
- Downloading a taxo_group with limited access will raise HTTP 401 error,
  it the account does not have access right. In that case, 
  it must be excluded in YAML file. (`#165 <https://framagit.org/lpo/Client_API_VN/issues/165>`_)


Improved Documentation
----------------------

- Minimal versions of supported OS has been updated.
  They are tested under Linux Ubuntu >20 or Debian 10. (`#163 <https://framagit.org/lpo/Client_API_VN/issues/163>`_)
- Minimal documentation of transfer_vn is available. (`#164 <https://framagit.org/lpo/Client_API_VN/issues/164>`_)


Client-API-VN v2.9.1 (2021-10-31)
=================================

Bugfixes
--------

- Several transient errors could stop transfer_vn after max_retry errors.
  This is fixed: a succesful transfer resets the error counter. (`#155 <https://framagit.org/lpo/Client_API_VN/issues/155>`_)
- Places are now downloaded and stored correctly. (`#168 <https://framagit.org/lpo/Client_API_VN/issues/168>`_)
- Very long transfer duration are now handled without error. (`#176 <https://framagit.org/lpo/Client_API_VN/issues/176>`_)


Client-API-VN v2.9.0 (2021-10-11)
=================================

Features
--------

- In case of HTTP error, the error message in the text included
  in the response is printed. (`#156 <https://framagit.org/lpo/Client_API_VN/issues/156>`_)
- Supported python versions are 3.7 to 3.9.
  Previous versions are not supported and will not work. (`#172 <https://framagit.org/lpo/Client_API_VN/issues/172>`_)
- observations/delete_list is available in biolovision/apy.
  Note that id_form or id_form_universal to delete must be
  included in data dict. (`#173 <https://framagit.org/lpo/Client_API_VN/issues/173>`_)


Bugfixes
--------

- update_vn now accepts single quote "'" in value parameter.
  It must be quoted with double-quote, i.e. "aujourd'hui". (`#154 <https://framagit.org/lpo/Client_API_VN/issues/154>`_)


Improved Documentation
----------------------

- Link to documentation now refer to readthedocs/stable. (`#160 <https://framagit.org/lpo/Client_API_VN/issues/160>`_)
- Running transfer_vn from cron is now documented in README (`#174 <https://framagit.org/lpo/Client_API_VN/issues/174>`_)


Misc
----

- `#68 <https://framagit.org/lpo/Client_API_VN/issues/68>`_


Client-API-VN v2.8.1 (2021-06-02)
=================================

Features
--------

- In order to get timing data of each request, table import.download_log is extended.
  If you upgrade without recreating JSON tables, you must run the following script::

      ALTER TABLE import.download_log ADD COLUMN length integer;
      ALTER TABLE import.download_log ADD COLUMN duration integer;
      CREATE INDEX ix_import_download_log_duration ON import.download_log USING btree(duration);
      CREATE INDEX ix_import_download_log_length ON import.download_log USING btree(length); 
- confirmed_by is now available in observations table. (`#151 <https://framagit.org/lpo/Client_API_VN/issues/151>`_)


Bugfixes
--------

- When dropping database (--db_drop), transfer_vn just logs a warning if the role is still used and cannot be dropped. (`#148 <https://framagit.org/lpo/Client_API_VN/issues/148>`_)
- When no territorial_unit_ids parameter is defined in YAML configuration file,
  all territorial_units are downloaded. (`#150 <https://framagit.org/lpo/Client_API_VN/issues/150>`_)


Improved Documentation
----------------------

- JSON schemas are updated. (`#149 <https://framagit.org/lpo/Client_API_VN/issues/149>`_)


Client-API-VN v2.8.0 (2021-04-10)
=================================

Features
--------

- It is now possible to filter download by territorial_unit.
  An optional parameter is available in YAML configuration file, `filter` section::

      # List of territorial_unit_ids to download
      territorial_unit_ids:
          - 01
          - 03

  (`#134 <https://framagit.org/lpo/Client_API_VN/issues/134>`_)
- In observations table, project_code is indexed. (`#142 <https://framagit.org/lpo/Client_API_VN/issues/142>`_)
- UUID, from JSON dowloaded, is now stored in observations table.
  `import.uuid_xref` is removed. (`#146 <https://framagit.org/lpo/Client_API_VN/issues/146>`_)


Bugfixes
--------

- update_vn gracefuly ignores empty line in CSV file. (`#130 <https://framagit.org/lpo/Client_API_VN/issues/130>`_)
- evn_conf raises an exception if configuration file does not exist. (`#132 <https://framagit.org/lpo/Client_API_VN/issues/132>`_)
- Number of downloaded sightings is now displayed for each territorial_unit. (`#137 <https://framagit.org/lpo/Client_API_VN/issues/137>`_)
- Both schemas are now created with `db_group` owner. (`#140 <https://framagit.org/lpo/Client_API_VN/issues/140>`_)
- Updating sightings within forms is now possible.
  Changing data of a sighting inside a forms should use the simple path::

    Isère;3079911;$['data']['sightings'][0]['observers'][0]['project'];replace;26

  and not include `['forms'][0]`. (`#141 <https://framagit.org/lpo/Client_API_VN/issues/141>`_)


Improved Documentation
----------------------

- Documentation improvement for API and installation. (`#129 <https://framagit.org/lpo/Client_API_VN/issues/129>`_)


Deprecations and Removals
-------------------------

- Support for list download is deprecated and will be removed in a future version.
  Download should only be performed using search method. (`#135 <https://framagit.org/lpo/Client_API_VN/issues/135>`_)


Client-API-VN v2.7.1 (2021-02-07)
=================================

Bugfixes
--------

- In column based tables, all text is now stored as TEXT instead of VACHAR(n) (`#138 <https://framagit.org/lpo/Client_API_VN/issues/138>`_)


Client-API-VN v2.7.0 (2020-07-06)
=================================

Features
--------

- Storing to database can be disabled.

  Dowload_vn can now store to any or both Postgresql and File backend stores.

  The database section is optional.
  If present, a new key is required::

      database:
          # Enable storing to database
          enabled: true (`#63 <https://framagit.org/lpo/Client_API_VN/issues/63>`_)
- Validation controler is available in biolovision.api.
   (`#74 <https://framagit.org/lpo/Client_API_VN/issues/74>`_)
- In case of service unavailable error (HTTP 503), wait for longer delay
  before retry. Delay can be changed by YAML parameter unavailable_delay. (`#94 <https://framagit.org/lpo/Client_API_VN/issues/94>`_)
- Added field information from JSON download.

  In field_group table :
  - text_v, from 'text' attribute
  - group_v, from 'group' attributé

  in field_details table :
  - text_v, from 'text' attribute (`#107 <https://framagit.org/lpo/Client_API_VN/issues/107>`_)
- New commands added to update_vn.
  - delete_attribute, to keep the observation and remove the attribute with the given path
  - delete_observation, to remove completely the observation (`#113 <https://framagit.org/lpo/Client_API_VN/issues/113>`_)
- Python version 3.8 is now supported. (`#116 <https://framagit.org/lpo/Client_API_VN/issues/116>`_)
- Added families controler in api and download_vn. (`#120 <https://framagit.org/lpo/Client_API_VN/issues/120>`_)
- A new application, validate, checks downloaded JSON files against its schema.
  JSON schemas are used to document the dowloaded files. (`#123 <https://framagit.org/lpo/Client_API_VN/issues/123>`_)
- update_vn adds "updated" date in the hidden_comment (`#127 <https://framagit.org/lpo/Client_API_VN/issues/127>`_)


Bugfixes
--------

- Scheduled jobs are now terminated by Ctrl-C. 
  There is still an OSError raised during shutdown. (`#96 <https://framagit.org/lpo/Client_API_VN/issues/96>`_)
- Option --status does not start pending tasks. (`#112 <https://framagit.org/lpo/Client_API_VN/issues/112>`_)
- update_vn accepts files with leading or trailing blanks in the values. (`#118 <https://framagit.org/lpo/Client_API_VN/issues/118>`_)
- Long json_format was not enforced by transfer_vn. 
  When json_format: long is defined in YAML file and file storage is enablesd,
  files are now correctly containing long JSON data.
  Note: long json_format is not compatible with PostgreSQL storage. (`#122 <https://framagit.org/lpo/Client_API_VN/issues/122>`_)


Misc
----

- `#75 <https://framagit.org/lpo/Client_API_VN/issues/75>`_, `#104 <https://framagit.org/lpo/Client_API_VN/issues/104>`_, `#111 <https://framagit.org/lpo/Client_API_VN/issues/111>`_, `#114 <https://framagit.org/lpo/Client_API_VN/issues/114>`_, `#115 <https://framagit.org/lpo/Client_API_VN/issues/115>`_


Client-API-VN v2.6.4 (2020-04-01)
=================================

Features
--------

- In biolovision.api, api_create and api_delete are implemented. (`#98 <https://framagit.org/lpo/Client_API_VN/issues/98>`_)


Bugfixes
--------

- In biolovision.api, api_search works again (corrected regression). (`#102 <https://framagit.org/lpo/Client_API_VN/issues/102>`_)
- end_date and start_date are now correctly used, ie:
  interval starts with start_date and ends with end_date.
  Exception is raised if not in correct order.
  NOTE : if used in YAML, please check the correct order. (`#105 <https://framagit.org/lpo/Client_API_VN/issues/105>`_)
- When using --update, the list of new observations could get too long and return HTTP error 414.
  Update list are now chunked, and chunk size is controled by YAML parameter max_list_length. (`#109 <https://framagit.org/lpo/Client_API_VN/issues/109>`_)


Client-API-VN v2.6.3 (2020-03-14)
=================================

Bugfixes
--------

- api_search, used in full download, was returning an empty dict.
  It is now working correctly. (`#108 <https://framagit.org/lpo/Client_API_VN/issues/108>`_)


Client-API-VN v2.6.0 (2019-10-17)
=================================

Features
--------

- A sample application is available in src/template. Copy sample_app.py
  and __init__.py to a new directory to start creating a new application. (`#100 <https://framagit.org/lpo/Client_API_VN/issues/100>`_)
- update_vn application is available for field test.
  See README for details on how to use it. (`#101 <https://framagit.org/lpo/Client_API_VN/issues/101>`_)


Client-API-VN v2.5.2 (2019-10-06)
=================================

Features
--------

- Application is now available as docker container.
  See README for installation instructions. (`#95 <https://framagit.org/lpo/Client_API_VN/issues/95>`_)


Client-API-VN v2.5.0 (2019-10-01)
=================================

Features
--------

- Major change on incremental (and full) download.
  All controlers can now be downloaded on a regular basis.
  See README for more information on download process.

  YAML configuration file must be updated to define download
  schedule for all controlers. A typical example is given below:

    .. code-block:: yaml

      # Biolovision API controlers parameters
      # Enables or disables download from each Biolovision API
      # Also defines scheduling (cron-like) parameters, in UTC
      controler:
          entities:
              # Enable download from this controler
              enabled: true
              schedule:
                  # Every Friday at 23:00 UTC
                  day_of_week: 4
                  hour: 23
          fields:
              # Enable download from this controler
              enabled: true
              schedule:
                  # Every Friday at 23:00 UTC
                  day_of_week: 4
                  hour: 23
          local_admin_units:
              # Enable download from this controler
              enabled: true
              schedule:
                  # Every Monday at 05:00 UTC
                  day_of_week: 0
                  hour: 5
          observations:
              # Enable download from this controler
              enabled: true
              # Define scheduling parameters
              schedule:
                  # Every hour
                  year: '*'
                  month: '*'
                  day: '*'
                  week: '*'
                  day_of_week: '*'
                  hour: '*'
                  minute: 0
          observers:
              # Enable download from this controler
              enabled: true
              schedule:
                  # Every day at 06:00 UTC
                  hour: 6
          places:
              # Enable download from this controler
              enabled: true
              schedule:
                  # Every Thursday at 23:00 UTC
                  day_of_week: 3
                  hour: 23
          species:
              # Enable download from this controler
              enabled: true
              schedule:
                  # Every Wednesday at 22:00 UTC
                  day_of_week: 2
                  hour: 22
          taxo_groups:
              # Enable download from this controler
              enabled: true
              schedule:
                  # Every Wednesday at 22:00 UTC
                  day_of_week: 2
                  hour: 22
          territorial_units:
              # Enable download from this controler
              enabled: true
              schedule:
                  # Every Thursday at 23:00 UTC
                  day_of_week: 3
                  hour: 23

  (`#24 <https://framagit.org/lpo/Client_API_VN/issues/24>`_)

- When using --update option, observations create or update are
  grouped in a single API call. This should improve performances.
  download_log table now contains one row for each group of updates. (`#76 <https://framagit.org/lpo/Client_API_VN/issues/76>`_)
- For developers: biolovision_api.py moved to an independant module.
  Replace ``from export_vn.biolovision_api import ...`` by ``from biolovision.api import ...`` (`#88 <https://framagit.org/lpo/Client_API_VN/issues/88>`_)
- In case of parsing error in YAML configuration file,
  the error message is printed without traceback. (`#89 <https://framagit.org/lpo/Client_API_VN/issues/89>`_)
- A new ``filter:`` section is added to YAML configuration file.
  ``taxo_exclude:`` list needs to be moved to this new section.

  To limit full download to a time interval, you can add:

  - ``start_date``, optional date of first observation.
    If omitted, start with earliest data.
  - ``end_date``, optional date of last observation.
    If omitted, start with latest data.

  Date format is YYYY-MM-DD.

  For example:

    .. code-block:: yaml

      # Observations filter, to limit download scope
      filter:
          # List of taxo_groups to exclude from download
          # Uncommment taxo_groups to disable download
          taxo_exclude:
              #- TAXO_GROUP_BIRD
              #- TAXO_GROUP_BAT
              #- TAXO_GROUP_MAMMAL
              - TAXO_GROUP_SEA_MAMMAL
              #- TAXO_GROUP_REPTILIAN
              #- TAXO_GROUP_AMPHIBIAN
              #- TAXO_GROUP_ODONATA
              #- TAXO_GROUP_BUTTERFLY
              #- TAXO_GROUP_MOTH
              #- TAXO_GROUP_ORTHOPTERA
              #- TAXO_GROUP_HYMENOPTERA
              #- TAXO_GROUP_ORCHIDACEAE
              #- TAXO_GROUP_TRASH
              #- TAXO_GROUP_EPHEMEROPTERA
              #- TAXO_GROUP_PLECOPTERA
              #- TAXO_GROUP_MANTODEA
              #- TAXO_GROUP_AUCHENORRHYNCHA
              #- TAXO_GROUP_HETEROPTERA
              #- TAXO_GROUP_COLEOPTERA
              #- TAXO_GROUP_NEVROPTERA
              #- TAXO_GROUP_TRICHOPTERA
              #- TAXO_GROUP_MECOPTERA
              #- TAXO_GROUP_DIPTERA
              #- TAXO_GROUP_PHASMATODEA
              #- TAXO_GROUP_ARACHNIDA
              #- TAXO_GROUP_SCORPIONES
              #- TAXO_GROUP_FISH
              #- TAXO_GROUP_MALACOSTRACA
              #- TAXO_GROUP_GASTROPODA
              #- TAXO_GROUP_BIVALVIA
              #- TAXO_GROUP_BRANCHIOPODA
              - TAXO_GROUP_ALIEN_PLANTS
          # Use short (recommended) or long JSON data
          # json_format: short
          # Optional start and end dates
          # start_date: 2019-09-01
          # end_date: 2019-08-01

  (`#93 <https://framagit.org/lpo/Client_API_VN/issues/93>`_)


Misc
----

- `#36 <https://framagit.org/lpo/Client_API_VN/issues/36>`_, `#84 <https://framagit.org/lpo/Client_API_VN/issues/84>`_


Client-API-VN v2.4.4 (2019-08-22)
=================================

Features
--------

- The following colums are added to forms::

      observer_uid        INT
      date_start          DATE
      date_stop           DATE

(`#86 <https://framagit.org/lpo/Client_API_VN/issues/86>`_)


Client-API-VN v2.4.3 (2019-08-22)
=================================

Features
--------

- Added protocol_name column in forms table. (`#85 <https://framagit.org/lpo/Client_API_VN/issues/85>`_)


Bugfixes
--------

- VACUUM is only performed on json and column-based tables created by transfer_vn.
  This avoids a lengthy VACUUM on the full database. (`#70 <https://framagit.org/lpo/Client_API_VN/issues/70>`_)
- Corrected loggin message "Updating observation {}" (`#79 <https://framagit.org/lpo/Client_API_VN/issues/79>`_)
- UUID are now correctly created for all observations. (`#80 <https://framagit.org/lpo/Client_API_VN/issues/80>`_)
- In observations, date and date_year are correctly extracted from JSON. (`#82 <https://framagit.org/lpo/Client_API_VN/issues/82>`_)
- Protocol data is stored in JSONB column, in forms table.
  See `example query <https://framagit.org/lpo/partage-de-codes/snippets/3741>`_
  for how to use it to get STOC data.

  Note: For survey datas, as G. Delaloye pointed out, protocols rights accesses
  must be configured in portals:
  +-----------------+--------------------------------------------------------+
  |    compte       |                         droit                          |
  +=================+========================================================+
  | utilisateur_api | Droits de gestion des données complémentaires Gypaètes |
  +-----------------+--------------------------------------------------------+
  | utilisateur_api | Droit de voir toutes les observations cachées          |
  +-----------------+--------------------------------------------------------+
  | utilisateur_api | Droits de faire des recherches, malgré le quota        |
  +-----------------+--------------------------------------------------------+
  | utilisateur_api | Droits de gestion des observations                     |
  +-----------------+--------------------------------------------------------+
  | utilisateur_api | Droits d'administration                                |
  +-----------------+--------------------------------------------------------+
  | utilisateur_api | Accès admin Wetlands                                   |
  +-----------------+--------------------------------------------------------+
  | utilisateur_api | Accès aux comptes utilisateurs tiers via l'API         |
  +-----------------+--------------------------------------------------------+
  | utilisateur_api | Accès admin comptage protocolé                         |
  +-----------------+--------------------------------------------------------+
  | utilisateur_api | Accès admin STOC Montagne                              |
  +-----------------+--------------------------------------------------------+
  | utilisateur_api | Accès admin STOC Sites                                 |
  +-----------------+--------------------------------------------------------+
  | utilisateur_api | Accès admin SHOC                                       |
  +-----------------+--------------------------------------------------------+
  | utilisateur_api | Accès admin STOC EPS                                   |
  +-----------------+--------------------------------------------------------+

Client-API-VN v2.4.2 (2019-08-20)
=================================

Features
--------

- When using ``--full`` option, observations and forms are processed after all other controlers. (`#77 <https://framagit.org/lpo/Client_API_VN/issues/77>`_)


Bugfixes
--------

- Some options are exclusives::

      [--verbose | --quiet]
      [--full | --update] (`#78 <https://framagit.org/lpo/Client_API_VN/issues/78>`_)


Client-API-VN v2.4.1 (2019-08-19)
=================================

Features
--------

- First pass of database tuning:

  - Added indexes on main id columns
  - Added id indexes on JSON tables (`#65 <https://framagit.org/lpo/Client_API_VN/issues/65>`_)
- The number of concurrent database insertion threads was 4, which
  is too much for the work required. At most 1 or 2 are used.
  The default is now 2 workers.

  NOTE: if your YAML configuration file contains a ``[tuning]`` section,
  please modify ``db_worker_threads: 2``. (`#71 <https://framagit.org/lpo/Client_API_VN/issues/71>`_)
- For sites with a large number of observations per day, the minimum was too
  large, leading to chunks exceeding 10 000 observations. Large chunk size
  reduce parallel processing between client and server.
  The minimum is now 5 days by default.

  NOTE: if your YAML configuration file contains a ``[tuning]`` section,
  please modify ``pid_limit_min: 5``. If your chunk size are still larger
  than 10 000 observations, you can reduce it further. (`#72 <https://framagit.org/lpo/Client_API_VN/issues/72>`_)


Bugfixes
--------

- Forms should now be correctly updated if changed on the site. (`#66 <https://framagit.org/lpo/Client_API_VN/issues/66>`_)
- ``id_form_universal`` added to observations table, to refer to enclosing form. (`#73 <https://framagit.org/lpo/Client_API_VN/issues/73>`_)


Client-API-VN v2.4.0 (2019-08-07)
=================================

Features
--------

- Storage and processing of JSON data has been improved, reducing processing time. (`#56 <https://framagit.org/lpo/Client_API_VN/issues/56>`_)
- Field groups details use the text index provided by the API.
  For example, field_details.id '5_1' is value '1' of group '5', meaning 'COLL_TRANS'. (`#62 <https://framagit.org/lpo/Client_API_VN/issues/62>`_)
- In observers_json, id_universal is stored in a separate column. (`#64 <https://framagit.org/lpo/Client_API_VN/issues/64>`_)


Client-API-VN v2.3.3 (2019-08-04)
=================================

Features
--------

- Several performance enhancements:

  - projection to local coordinates is much faster, reducing processing
    time by at least a factor of 6

  - forms are only processed once, at the first observation of the form. (`#56 <https://framagit.org/lpo/Client_API_VN/issues/56>`_)


Bugfixes
--------

- SQL file should be correct, when installed from PyPI.
  To be tested from PyPI and from framagit clone. (`#57 <https://framagit.org/lpo/Client_API_VN/issues/57>`_)
- In table observations, update_date is correctly filled. (`#59 <https://framagit.org/lpo/Client_API_VN/issues/59>`_)
- Increments are correctly tracked. When using --update, only new or changed observations are downloaded. (`#60 <https://framagit.org/lpo/Client_API_VN/issues/60>`_)
- Fields are now dowloaded in 2 tables :

  - field_groups, which lists all groups of fields

  - field_details, which lists all values for each group

  Column observations.behaviours is now a Postgresql ARRAY,
  listing behaviours link_id code. (`#61 <https://framagit.org/lpo/Client_API_VN/issues/61>`_)


Improved Documentation
----------------------

- README.rst updated to document --init option.
  CONTRIBUTING.rst improved.
  Updated french translations. (`#58 <https://framagit.org/lpo/Client_API_VN/issues/58>`_)


Client-API-VN v2.3.2 (2019-07-27)
=================================

Features
--------

- Added --init option, that creates a draft YAML configuration file.
  This file then needs to be edited before use. (`#37 <https://framagit.org/lpo/Client_API_VN/issues/37>`_)
- The comment in download_log table is improved, displaying more information about observations download progress. (`#53 <https://framagit.org/lpo/Client_API_VN/issues/53>`_)
- Number of concurrent database insert/update and queue size are parameters
  in YAML file, ``[tuning]`` section:

  .. code-block:: yaml

      # Postgresql DB tuning parameters
      db_worker_threads: 4
      db_worker_queue: 100000

(`#54 <https://framagit.org/lpo/Client_API_VN/issues/54>`_)

Bugfixes
--------

- Tentative correction of duplicate key exception. As this is not reproductible, bug fix is not certain.
  Insert or update of records in Postgresql DB is now atomic (insert + on conflict). (`#55 <https://framagit.org/lpo/Client_API_VN/issues/55>`_)


Client-API-VN v2.3.1 (2019-07-23)
=================================

Features
--------

- HMAC encoding key is defined by YAML parameter db_secret_key (`#50 <https://framagit.org/lpo/Client_API_VN/issues/50>`_)
- A new field is added to src_vn.observers to anonymize observers:
   pseudo_observer_uid. It should be used for data exchance to respect
   user privacy. It is encoded by HMAC, using db_secret_key token. (`#51 <https://framagit.org/lpo/Client_API_VN/issues/51>`_)


Misc
----

- `#52 <https://framagit.org/lpo/Client_API_VN/issues/52>`_


Client-API-VN v2.3.0 (2019-06-30)
=================================

Features
--------

- Local coordinate system can now be modified.
  The new YAML configuration parameter `db_out_proj` selects the
  EPGS system for coordinate transformation. It defaults to 2154 (Lambert 93).
  Local coordinates are available in columns coord_x_local and coord_y_local.

  (`#22 <https://framagit.org/lpo/Client_API_VN/issues/22>`_)

- Forms are now available in the forms_json and forms tables.
  Forms contain the following columns:

  +-------------------+-----------------+
  | column            | type            |
  +===================+=================+
  | site              | VARCHAR(50)     |
  +-------------------+-----------------+
  | id                | INTEGER         |
  +-------------------+-----------------+
  | id_form_universal | VARCHAR(500)    |
  +-------------------+-----------------+
  | time_start        | VARCHAR(500)    |
  +-------------------+-----------------+
  | time_stop         | VARCHAR(500)    |
  +-------------------+-----------------+
  | full_form         | VARCHAR(500)    |
  +-------------------+-----------------+
  | version           | VARCHAR(500)    |
  +-------------------+-----------------+
  | coord_lat         | FLOAT           |
  +-------------------+-----------------+
  | coord_lon         | FLOAT           |
  +-------------------+-----------------+
  | coord_x_local     | FLOAT           |
  +-------------------+-----------------+
  | coord_y_local     | FLOAT           |
  +-------------------+-----------------+
  | comments          | VARCHAR(100000) |
  +-------------------+-----------------+
  | protocol          | VARCHAR(100000) |
  +-------------------+-----------------+

  (`#28 <https://framagit.org/lpo/Client_API_VN/issues/28>`_)

- Added parameters to YAML configuration file.
  See also Issue #43 and #44 for new or changed parameters.

  In ``database:`` section, the followng parameter defines the
  geographic projection (EPGS code) used to create
  ``coord_x_local`` and ``coord_y_local``.

  Optional parameters are added in a new ``tuning:`` section, for expert use:

  .. code-block:: yaml

     # Tuning parameters, for expert use.
     tuning:
        # Max chunks in a request before aborting.
        max_chunks: 10
        # Max retries of API calls before aborting.
        max_retry: 5
        # Maximum number of API requests, for debugging only.
        # - 0 means unlimited
        # - >0 limit number of API requests
        max_requests: 0
        # LRU cache size for common requests (taxo_groups...)
        lru_maxsize: 32
        # Earliest year in the archive. Queries will not ge before this date.
        min_year: 1901
        # PID parameters, for throughput management.
        pid_kp: 0.0
        pid_ki: 0.003
        pid_kd: 0.0
        pid_setpoint: 10000
        pid_limit_min: 10
        pid_limit_max: 2000
        pid_delta_days: 15

  Deprecated ``local:`` section and parameters must be removed.
  An error is raised if not.

  (`#33 <https://framagit.org/lpo/Client_API_VN/issues/33>`_)

- UUID are not (re)created during columns tables creation.
  For observations, they are in a separate uui_xref table. They can be
  obtained by joining observations and uui_xref on
  (site=site and id=id_sighing).

  They are dropped for other tables.

  Table uuid_xref contains:

  +--------------+----------+
  | column       | type     |
  +==============+==========+
  | site         | String   |
  +--------------+----------+
  | universal_id | String   |
  +--------------+----------+
  | uuid         | String   |
  +--------------+----------+
  | alias        | JSONB    |
  +--------------+----------+
  | update_ts    | DateTime |
  +--------------+----------+

  (`#38 <https://framagit.org/lpo/Client_API_VN/issues/38>`_)

- Application is now tested with

  * Python version 3.5, 3.6 and 3.7
  * Debian 9, Ubuntu 18.10
  * Postgresql 10, 11

  (`#40 <https://framagit.org/lpo/Client_API_VN/issues/40>`_)

- Implemented fields controler.
  Fields data is dowloaded and stored in fields table:

  +--------------+---------------+
  | column       | type          |
  +==============+===============+
  | site         | VARCHAR(50)   |
  +--------------+---------------+
  | id           | INTEGER       |
  +--------------+---------------+
  | default_v    | VARCHAR(500)  |
  +--------------+---------------+
  | empty_choice | VARCHAR(500)  |
  +--------------+---------------+
  | mandatory    | VARCHAR(500)  |
  +--------------+---------------+
  | name         | VARCHAR(1000) |
  +--------------+---------------+

  (`#43 <https://framagit.org/lpo/Client_API_VN/issues/43>`_)

- The following columns are added:

      * observations.behaviours

  The following columns are now boolean:

      * species.is_used
      * observations.hidden
      * observations.admin_hidden
      * observations.mortality
      * observers.anonymous
      * observers.collectif
      * observers.default_hidden
      * places.is_private
      * places.visible
      * species.is_used

      (`#46 <https://framagit.org/lpo/Client_API_VN/issues/46>`_)


Bugfixes
--------

- Database tables can now be created from any user, provided it is defined
  in .yaml file::

      # Postgresql user used to import data
      db_user: *any_user*
      # Postgresql user password
      db_pw: *password*

  (`#39 <https://framagit.org/lpo/Client_API_VN/issues/39>`_)

- Some columns were not filled correctly. This is corrected as described below:

  +--------------+---------------------------------+
  | column       | comment                         |
  +==============+=================================+
  | timing       | Available in observations table |
  +--------------+---------------------------------+
  | update_date  | Available in observations table |
  +--------------+---------------------------------+
  | project_code | Available in observations table |
  +--------------+---------------------------------+
  | details      | Available in observations table |
  +--------------+---------------------------------+

  The following parameters are not available in observations table and
  need to be fetched from observers table.

  (`#41 <https://framagit.org/lpo/Client_API_VN/issues/41>`_)

- Incorrect parameters name in YAML configuration file.
  Replace:
  - taxo_group by taxo_groups
  - territorial_unit by territorial_units

  (`#44 <https://framagit.org/lpo/Client_API_VN/issues/44>`_)

- update_date is extracted correctly and does raise an exception.

  (`#49 <https://framagit.org/lpo/Client_API_VN/issues/49>`_)


Client-API-VN v2.2.2 (2019-05-13)
=================================

Features
--------

- Added VACUUM FULL ANALYZE after columns table (re)creation (option --col_tables_create)
  to reclaim space left after mass UPDATE. (`#31 <https://framagit.org/lpo/Client_API_VN/issues/31>`_)
- YAML configuration is now checked for validity when loaded. This should improve error finding when typing configuration file. (`#35 <https://framagit.org/lpo/Client_API_VN/issues/35>`_)


Bugfixes
--------

- Version is now correctly displayed in application installed from PyPI. (`#32 <https://framagit.org/lpo/Client_API_VN/issues/32>`_)


Improved Documentation
----------------------

- Now using towncrier (https://github.com/hawkowl/towncrier) to update CHANGELOG.
  Improved and corrected README.rst and CONTRIBUTING.rst (`#34 <https://framagit.org/lpo/Client_API_VN/issues/34>`_)


Client-API-VN 2.2.1 (2019-05-09)
================================

Features
--------

- Starting with this version, the application is packaged and distributed
  in PyPI.
  See https://pypi.org/project/Client-API-VN/ for more information.

  transfer_vn is now available as a shell script. (`#29 <https://framagit.org/lpo/Client_API_VN/issues/29>`_)
