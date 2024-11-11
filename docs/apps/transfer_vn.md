# transfer_vn Documentation

## User Guide

### Initial setup

Initialize the sample YAML file in your HOME directory and edit with
your local details. The YAML file is self documented::

    transfer_vn --init .evn_your_site.yaml
    editor $HOME/.evn_your_site.yaml

Create the database and tables::

    transfer_vn --db_create --json_tables_create --col_tables_create .evn_your_site.yaml

### Running the application

After editing YAML configuration file, you should proceed in 3 stages:

1. Transfer of all historical data `transfer_vn --full`.
   Note: the probability of a blocking error during this large transfer is not negligible.
   In this case, it is possible to resume the complete download by limiting the taxonomic groups
   and/or the start and end dates.
2. Schedule update tasks, based on recurrences defined in the YAML configuration file:
   `transfer_vn --schedule`
3. Regular incremental update, for example in an hourly crontab:
   `transfer_vn --update`

Transfers overwrite data already downloaded. It is therefore not a problem to
restart `transfer_vn --full` on part of the database.

Beware that, depending on the volume of observations,
this can take several hours. We recommend starting with a small taxonomic
group first::

    transfer_vn --full .evn_your_site.yaml

After this full download, data can be updated. For observations, only new,
modified or deleted observations are downloaded. For other controlers, a full
download is always performed. Each controler runs on its own schedule,
defined in the YAML configuration file. This step needs to be performed
after each `--full` execution or YAML file modification. To create or update,
after modifying the configuration file, the schedule::

    transfer_vn --schedule .evn_your_site.yaml

Once this is done, you can update the database with new observations::

    transfer_vn --update .evn_your_site.yaml

This can be done by cron, every hour for example. At each run, all scheduled
tasks are performed. Note: you must wait until the first scheduled task has
expired for a transfer to be carried out. With the default schedule, you must
therefore wait for the next round hour `--schedule`. It must run at least
once a week. The virtual environment must be activated in the cron job, for
example::

    0 * * * * echo 'source client_api_vn/env_VN/bin/activate;cd client_api_vn/;transfer_vn --update .evn_your_site.yaml --verbose'| /bin/bash > /dev/null

## Reference

The application runs as::

    transfer_vn options config

where::

    options  command line options described below
    config   YAML file, located in $HOME directory, described in sample file

    -h, --help Prints help and exits
    --version Print version number
    --verbose Increase output verbosity
    --quiet Reduce output verbosity
    --init Initialize the YAML configuration file
    --db_drop Delete if exists database and roles
    --db_create Create database and roles
    --json_tables_create Create or recreate JSON tables in import schema
    --col_tables_create Create or recreate colums based tables
    --migrate Migrates the JSON import schema to latest version
    --full Perform a full download
    --update Perform an incremental download
    --schedule Create or update the incremental update schedule
    --status Print downloading status (schedule, errors...)
    --count Count observations by site and taxo_group
    --profile Gather and print profiling times
