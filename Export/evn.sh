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

# global parameters
set -e          # kill script if a command fails
set -o nounset  # unset values give error
set -o pipefail # prevents errors in a pipeline from being masked

# Logging file
evn_log=~/tmp/evn_all_$(date '+%Y-%m-%d').log

log_path=$HOME/b-log # the path to the script
if [ ! -f "${log_path}"/b-log.sh ]
then
    pushd $HOME
    git clone https://github.com/idelsink/b-log.git
    popd
fi
source "${log_path}"/b-log.sh                         # include the log script

B_LOG -o true
B_LOG -f $evn_log --file-prefix-enable --file-suffix-enable
LOG_LEVEL_ALL

OPTS=`getopt -o vicdsah --long verbose,init,config,download,store,all,help -- "$@"`

if [ $? != 0 ] ; then echo "Option non reconnue" >&2 ; exit 1 ; fi

# echo "$OPTS"
eval set -- "$OPTS"

VERBOSE=false
HELP=false

while true; do
  case "$1" in
    -v | --verbose ) VERBOSE=true; shift ;;
    -i | --init ) CMD="init"; shift ;;
    -c | --config ) CMD="config"; shift ;;
    -d | --download ) CMD="download"; shift ;;
    -s | --store ) CMD="store"; shift ;;
    -a | --all ) CMD="all"; shift ;;
    -h | --help ) HELP=true; shift ;;
    -- ) shift; break ;;
    * ) ERROR "Erreur de fonctionnement!" ; exit 1 ;;
  esac
done

INFO VERBOSE=$VERBOSE
INFO HELP=$HELP
INFO CMD=$CMD

# When running from crontab. To be improved
#cd ~/ExportVN

# Switch on possible actions
case "$CMD" in
  init)
    # Create directories as needed
    INFO "Initialisation de l'environnement"
    INFO "1. Base de données"
    expander3.py --file Sql/InitDB.sql > $HOME/tmp/InitDB.sql
    psql --dbname=postgres --file=$HOME/tmp/InitDB.sql
    expander3.py --file Sql/CreateObsTable.sql > $HOME/tmp/CreateObsTable.sql
    psql --dbname=postgres --file=$HOME/tmp/CreateObsTable.sql
    ;;

    config)
      # Edit configuration file
      INFO "Edition du fichier de configuration"
      editor $HOME/.evn.ini
      ;;

  download)
    # Create directories as needed
    INFO "Téléchargement depuis l'API du site VisioNature"
    python3 Python/DownloadFromVN.py 2>> $evn_log
    ;;

  store)
    # Store json files to Postgresql database
    WARN "Non implémenté"
    ;;

  all)
    # Download and then Store
    WARN "Non implémenté"
    ;;

  *)
    # Unknown option
    ERROR "ERREUR: option inconnue"
    ;;

esac
