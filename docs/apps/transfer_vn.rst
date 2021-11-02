======================
transfer_vn User Guide
======================

After editing YAML configuration file, it is necessary to proceed in 3 stages:

1. Transfer of all historical data ``transfer_vn --full``. 
   Note: the probability of a blocking error during this large transfer is not negligible.
   In this case, it is possible to resume the complete download by limiting the taxonomic groups
   and/or the start and end dates.
2. Schedule update tasks, based on recurrences defined in the YAML configuration file:
   ``transfer_vn --schedule``
3. Regular incremental update, for example in an hourly crontab: 
   ``transfer_vn --update``

Transfers overwrite data already downloaded. It is therefore not a problem to
restart ``transfer_vn --full`` on part of the database.