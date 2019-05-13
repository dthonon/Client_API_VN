Client-API-VN v2.2.2 (2019-05-13)
=================================

Features
--------

- Added VACUUM FULL ANALYZE after columns table (re)creation (option --col_tables_create)
  to reclaim space left after mass UPDATE. (`#31 < https://framagit.org/lpo/Client_API_VN/issues/31>`_)
- YAML configuration is now checked for validity when loaded. This should improve error finding when typing configuration file. (`#35 < https://framagit.org/lpo/Client_API_VN/issues/35>`_)


Bugfixes
--------

- Version is now correctly displayed in application installed from PyPI. (`#32 < https://framagit.org/lpo/Client_API_VN/issues/32>`_)


Improved Documentation
----------------------

- Now using towncrier (https://github.com/hawkowl/towncrier) to update CHANGELOG.
  Improved and corrected README.rst and CONTRIBUTING.rst (`#34 < https://framagit.org/lpo/Client_API_VN/issues/34>`_)


Client-API-VN 2.2.1 (2019-05-09)
================================

Features
--------

- Starting with this version, the application is packaged and disributed in PyPI. 
  See https://pypi.org/project/Client-API-VN/ for more information.

  transfer_vn is now available as a shell script. (`#29 < https://framagit.org/lpo/Client_API_VN/issues/29>`_)
