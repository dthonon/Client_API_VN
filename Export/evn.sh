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

# Logging script
log_path=$HOME/b-log # the path to the script
if [ ! -f "${log_path}"/b-log.sh ]
then
    pushd $HOME
    git clone https://github.com/idelsink/b-log.git
    popd
fi
source "${log_path}"/b-log.sh   # include the log script

# Logging options
B_LOG -o true
B_LOG -f $evn_log --file-prefix-enable --file-suffix-enable
LOG_LEVEL_ALL

# Analyze script options
OPTS=`getopt -o vicedsah --long verbose,init,create,edit,download,store,all,help -- "$@"`
if [ $? != 0 ] ; then echo "Option non reconnue" >&2 ; exit 1 ; fi
# echo "$OPTS"
eval set -- "$OPTS"
VERBOSE=false
CMD="help"
while true; do
  case "$1" in
    -v | --verbose ) VERBOSE=true; shift ;;
    -i | --init ) CMD="init"; shift ;;
    -c | --create ) CMD="create"; shift ;;
    -e | --edit ) CMD="edit"; shift ;;
    -d | --download ) CMD="download"; shift ;;
    -s | --store ) CMD="store"; shift ;;
    -a | --all ) CMD="all"; shift ;;
    -h | --help ) CMD="help"; shift ;;
    -- ) shift; break ;;
    * ) ERROR "Erreur de fonctionnement !" ; exit 1 ;;
  esac
done

INFO VERBOSE=$VERBOSE
INFO CMD=$CMD

# Load configuration file, if present, else ask for configuration
evn_conf=~/.evn.ini
unset config      # clear parameter array
typeset -A config # init array

# echo "commande = $cmd"
if [[ -f $evn_conf ]]  # Check if exists and load existing config
then
    INFO "Analyse des paramètres"
    # Parse configuration file
    while read line
    do
        # echo ">>>$(echo "$line" | cut -d '=' -f 1 | xargs)<<<"
        if echo $line | grep -F = &>/dev/null
        then
            varname=$(echo "$line" | cut -d '=' -f 1 | xargs)
            config[$varname]=$(echo "$line" | cut -d '=' -f 2- | xargs)
        fi
    done < $evn_conf
else
    INFO "Configuration initiale"
    cp --update ./evn_template.ini $evn_conf
    cmd=edit
fi

# When running from crontab. To be improved
#cd ~/ExportVN

# Switch on possible actions
case "$CMD" in
  help)
    # Create directories as needed
    INFO "Aide en ligne à rédiger"
    INFO "Mail admin : ${config[evn_admin_mail]}"
    ;;

  init)
    # Create database, tables, views...
    INFO "Initialisation de l'environnement : début"
    INFO "1. Base de données"
    expander3.py --file Sql/InitDB.sql > $HOME/tmp/InitDB.sql
    env PGOPTIONS="-c client-min-messages=WARNING" \
        psql --quiet --dbname=postgres --file=$HOME/tmp/InitDB.sql
    INFO "2. Tables"
    expander3.py --file Sql/CreateTables.sql > $HOME/tmp/CreateTables.sql
    env PGOPTIONS="-c client-min-messages=WARNING" \
        psql --quiet --dbname=postgres --file=$HOME/tmp/CreateTables.sql
    INFO "3. Vues"
    expander3.py --file Sql/CreateViews.sql > $HOME/tmp/CreateViews.sql
    env PGOPTIONS="-c client-min-messages=WARNING" \
        psql --quiet --dbname=postgres --file=$HOME/tmp/CreateViews.sql
    INFO "Initialisation de l'environnement : fin"
    ;;

  edit)
    # Edit configuration file
    INFO "Edition du fichier de configuration"
    editor $HOME/.evn.ini
    ;;

  download)
    # Create directories as needed
    INFO "Début téléchargement depuis le site ${config[evn_site]} : début"
    python3 Python/DownloadFromVN.py 2>> $evn_log
    INFO "Téléchargement depuis l'API du site ${config[evn_site]} : fin"
    ;;

  store)
    # Store json files to Postgresql database
    INFO "Chargement des données JSON dans Postgresql ${config[evn_db_name]} : début"
    INFO "1. Insertion dans la base"
    python3 Python/InsertInDB.py 2>> $evn_log
    INFO "2. Mise à jour des vues et indexation des tables et vues"
    expander3.py --file Sql/UpdateIndex.sql > $HOME/tmp/UpdateIndex.sql
    env PGOPTIONS="-c client-min-messages=WARNING" \
        psql --quiet --dbname=postgres --file=$HOME/tmp/UpdateIndex.sql
    INFO "Chargement des données JSON dans Postgresql ${config[evn_db_name]} : fin"
    ;;

  all)
    # Download and then Store
    INFO "Début téléchargement depuis le site : ${config[evn_site]}"
    $0 download
    INFO "Chargement des fichiers json dans la base ${config[evn_db_name]}"
    $0 store
    INFO "Fin transfert depuis le site : ${config[evn_site]}"
    links -dump ${config[evn_site]}index.php?m_id=23 | fgrep "Les part" | sed 's/Les partenaires       /Total des contributions :/' > ~/mail_fin.txt
    fgrep -c "observations:" $evn_log  >> ~/mail_fin.txt
    echo "Bilan du script : ERROR / WARN :" >> ~/mail_fin.txt
    fgrep -c "ERROR" $evn_log >> ~/mail_fin.txt
    fgrep -c "WARN" $evn_log >> ~/mail_fin.txt
    tail -15 $evn_log >> ~/mail_fin.txt
    gzip -f $evn_log
    INFO "Fin de l'export des données"
    mailx -s "Chargement de ${config[evn_site]}" -a $evn_log.gz ${config[evn_admin_mail]} < ~/mail_fin.txt
    rm -f ~/mail_fin.txt
    ;;

  *)
    # Unknown option
    ERROR "ERREUR: option inconnue"
    ;;

esac
