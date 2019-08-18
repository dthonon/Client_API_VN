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

  NOTE: if your YAML configuration file contrains a `[tuning]` section,
  please modify `db_worker_threads: 2`. (`#71 <https://framagit.org/lpo/Client_API_VN/issues/71>`_)
- For sites with a large number of observations per day, the minimum was too large,
  leading to chunks exceeding 10 000 observations. Large chunk size reduce parallel
  processing between client and server.
  The minimum is now 5 days by default.

  NOTE: if your YAML configuration file contrains a `[tuning]` section,
  please modify `pid_limit_min: 5`. If your chunk size are still larger
  than 10 000 observations, you can reduce it further. (`#72 <https://framagit.org/lpo/Client_API_VN/issues/72>`_)


Bugfixes
--------

- Forms should now be correctly updated if changed on the site. (`#66 <https://framagit.org/lpo/Client_API_VN/issues/66>`_)
- id_form_universal added to observations, to refer to enclosing form. (`#73 <https://framagit.org/lpo/Client_API_VN/issues/73>`_)


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

  - projection to local coordinates is much faster, reducing processing time by at least a factor of 6

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
  obtained by joining observations and uui_xref on (site=site and id=id_sighing)

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

- Starting with this version, the application is packaged and disributed in PyPI. 
  Seehttps://pypi.org/project/Client-API-VN/ for more information.

  transfer_vn is now available as a shell script. (`#29 <https://framagit.org/lpo/Client_API_VN/issues/29>`_)
