#!/bin/bash
#
# Main shell to call the different Export PHP scripts.
#
# Parameters:
#     $1: type of action to perform:
#          - config => Configure parameters for scripts (sites, passwords...).
#          - init => Prepare DB init script.
#          - download => Export from VisioNature fo json files, using API.
#          - store => Load json files in Postgresql.
#          - all => download then store
#
#Copyright (C) 2018, Daniel Thonon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

cmd=$1

# When running from crontab. To be improved
#cd ~/ExportVN

# Logging file
evn_log=~/evn_all_$(date '+%Y-%m-%d').log

# Default mail address for results mail, overriden by config file
config[evn_admin_mail]="d.thonon9@gmail.com"

# Switch on possible actions
case "$cmd" in
  config)
    # Edit configuration file
    echo "Non implémenté"
    ;;

  init)
    # Create directories as needed
    echo "Initialisation de l'environnement"
    echo "1. Base de données"
    expander3.py --file Sql/InitDB.sql > $HOME/tmp/InitDB.sql
    psql --dbname=postgres --file=$HOME/tmp/InitDB.sql
    ;;

  download)
    # Create directories as needed
    echo "Non implémenté"
    ;;

  store)
    # Store json files to Postgresql database
    echo "Non implémenté"
    ;;

  all)
    # Download and then Store
    echo "Non implémenté"
    ;;

esac
