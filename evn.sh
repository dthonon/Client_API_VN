#!/usr/bin/env bash
#
# Main shell to call the different Export python scripts.
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
# set -o nounset  # unset values give error
set -o pipefail # prevents errors in a pipeline from being masked

# Required when running from crontab
cd "$(dirname "$0")";
PATH="/usr/local/bin:/usr/bin:/bin"

# Analyze script options
OPTS=`getopt -o v --long all,download,edit,help,init,logfile:,site:,store,test,update,verbose -- "$@"`
if [ "$?" != 0 ] ; then echo "Option non reconnue" >&2 ; exit 1 ; fi
# echo "$OPTS"
eval set -- "$OPTS"
VERBOSE=false
CMD="help"
SITE=""
TEST=""
while true; do
    case "$1" in
        --all ) CMD="all"; shift ;;
        --download ) CMD="download"; shift ;;
        --edit ) CMD="edit"; shift ;;
        --help ) CMD="help"; shift ;;
        --init ) CMD="init"; shift ;;
        --logfile ) EVN_LOG="$2"; shift 2 ;;
        --site ) SITE="$2"; shift 2 ;;
        --store ) CMD="store"; shift ;;
        --test ) TEST="--test"; shift ;;
        --update ) CMD="update"; shift ;;
        -v | --verbose ) VERBOSE=true; shift ;;
        -- ) shift ; if [ -n "$1" ] ; then echo "Option inconnue $1 !" ; exit 1 ; fi ; break ;;
        * ) echo "Erreur de fonctionnement !" ; exit 1 ;;
    esac
done

if [ -z "$SITE" ]
then
    ERROR "Le site de téléchargement doit être spécifié par l'option --site=SITE"
    exit 1
fi

# Logging script
log_path="$HOME/b-log" # the path to the script
if [ ! -f "${log_path}"/b-log.sh ]
then
    pushd "$HOME"
    git clone https://github.com/idelsink/b-log.git
    popd
fi
source "${log_path}"/b-log.sh   # include the log script

# Logging options
B_LOG -o true
if "$VERBOSE"
then
    LOG_LEVEL_ALL
    SQL_QUIET=""
    CLIENT_MIN_MESSAGE="debug1"
    PYTHON_VERBOSE="--verbose"
else
    LOG_LEVEL_INFO
    SQL_QUIET="--quiet"
    CLIENT_MIN_MESSAGE="warning"
    PYTHON_VERBOSE=""
fi

if [[ ! -d "$HOME/tmp" ]]
then
    INFO "Création du répertoire $HOME/tmp"
    mkdir "$HOME/tmp"
fi

# Logging file, created if not given by --logfile parameter
if [ -z "$EVN_LOG" ]
then
    EVN_LOG="$HOME/tmp/evn_all_$(date '+%Y-%m-%d_%H:%M:%S').log"
    touch "$EVN_LOG"
fi
# B_LOG -f "$EVN_LOG" --file-prefix-enable --file-suffix-enable

INFO "Exécution du script avec la commande $CMD, sur le site $SITE"

# Load configuration file, if present, else ask for configuration
evn_conf="$HOME/.evn_$SITE.ini"
unset config      # clear parameter array
typeset -A config # init array

if [[ -f "$evn_conf" ]]  # Check if exists and load existing config
then
    INFO "Analyse des paramètres de configuration $evn_conf"
    # Parse configuration file
    while read line
    do
        # echo ">>>$(echo "$line" | cut -d '=' -f 1 | xargs)<<<"
        if echo "$line" | grep -F = &>/dev/null
        then
            varname=$(echo "$line" | cut -d '=' -f 1 | xargs)
            config[$varname]=$(echo "$line" | cut -d '=' -f 2- | xargs)
            # if $VERBOSE ; then DEBUG "$config[$varname] = ${config[$varname]}" ; fi
        fi
    done < "$evn_conf"
else
    INFO "Configuration initiale"
    cp --update ./evn_template.ini "$evn_conf"
    cmd="edit"
fi

# Create required repositories, if not existing
if [[ ! -d "$HOME/${config[evn_file_store]}" ]]
then
    INFO "Création du répertoire $HOME/${config[evn_file_store]}"
    mkdir "$HOME/${config[evn_file_store]}"
fi
if [[ ! -d "$HOME/${config[evn_file_store]}/$SITE" ]]
then
    INFO "Création du répertoire $HOME/${config[evn_file_store]}/$SITE"
    mkdir "$HOME/${config[evn_file_store]}/$SITE"
fi
SVG="${SITE}_svg"
if [[ ! -d "$HOME/${config[evn_file_store]}/$SVG" ]]
then
    INFO "Création du répertoire $HOME/${config[evn_file_store]}/$SVG"
    mkdir "$HOME/${config[evn_file_store]}/$SVG"
fi

# Switch on possible actions
case "$CMD" in
    help)
    # Provide heps on command
    INFO "Aide en ligne à rédiger"
    INFO "Mail admin : ${config[evn_admin_mail]}"
    ;;

    init)
    # Delete and create database
    INFO "Création de la base de données : début"
    DEBUG "1. Base de données"
    expander3.py --eval "evn_db_name=\"${config[evn_db_name]}\";evn_db_schema=\"${config[evn_db_schema]}\";evn_db_group=\"${config[evn_db_group]}\";evn_db_user=\"${config[evn_db_user]}\"" --file sql/init-db.sql > $HOME/tmp/init-db.sql
    env PGOPTIONS="-c client-min-messages=$CLIENT_MIN_MESSAGE" \
    psql "$SQL_QUIET" --dbname=postgres --file=$HOME/tmp/init-db.sql
    INFO "Création de la base de données : fin"
    ;;

    edit)
    # Edit configuration file
    INFO "Edition du fichier de configuration"
    editor "$evn_conf"
    INFO "Il faut aussi créer le compte $(whoami) dans postres, avec les droits SUPERUSER, "
    ;;

    download)
    # Download from VN site and store to JSON file
    INFO "Début téléchargement depuis le site ${config[evn_site]} : début"
    DEBUG "Vers le répertoire $HOME/${config[evn_file_store]}/$SITE/"
    ! rm -f "$HOME/${config[evn_file_store]}/$SVG/"*.json.gz
    ! mv -f "$HOME/${config[evn_file_store]}/$SITE/"*.json.gz "$HOME/${config[evn_file_store]}/$SVG/"
    expander3.py --eval "evn_db_name=\"${config[evn_db_name]}\";evn_db_schema=\"${config[evn_db_schema]}\";evn_db_group=\"${config[evn_db_group]}\";evn_db_user=\"${config[evn_db_user]}\"" --file Sql/CreateLog.sql > $HOME/tmp/CreateLog.sql
    env PGOPTIONS="-c client-min-messages=$CLIENT_MIN_MESSAGE" \
    psql "$SQL_QUIET" --dbname="${config[evn_db_name]}" --file=$HOME/tmp/CreateLog.sql
    python3 export_vn/DownloadFromVN.py "$PYTHON_VERBOSE" "$TEST" --site="$SITE"
    INFO "Téléchargement depuis l'API du site ${config[evn_site]} : fin"
    ;;

    store)
    # Store json files to Postgresql database
    INFO "Chargement des données JSON dans Postgresql ${config[evn_db_name]} : début"
    DEBUG "1. Création des tables"
    expander3.py --eval "evn_db_name=\"${config[evn_db_name]}\";evn_db_schema=\"${config[evn_db_schema]}\";evn_db_group=\"${config[evn_db_group]}\";evn_db_user=\"${config[evn_db_user]}\"" --file Sql/CreateTables.sql > $HOME/tmp/CreateTables.sql
    env PGOPTIONS="-c client-min-messages=$CLIENT_MIN_MESSAGE" \
    psql "$SQL_QUIET" --dbname="${config[evn_db_name]}" --file=$HOME/tmp/CreateTables.sql

    # if [ -f "$HOME/${config[evn_sql_scripts]}/$SITE.sql" ]
    # then
    #   DEBUG "5. Execution du script local : $HOME/${config[evn_sql_scripts]}/$SITE.sql"
    #   expander3.py --eval "evn_db_name=\"${config[evn_db_name]}\";evn_db_schema=\"${config[evn_db_schema]}\";evn_db_group=\"${config[evn_db_group]}\";evn_db_user=\"${config[evn_db_user]}\";evn_external1_name=\"${config[evn_external1_name]}\";evn_external1_pw=\"${config[evn_external1_pw]}\"" \
    #     --file "$HOME/${config[evn_sql_scripts]}/$SITE.sql" > "$HOME/tmp/$SITE.sql"
    #   env PGOPTIONS="-c client-min-messages=$CLIENT_MIN_MESSAGE" \
    #     psql "$SQL_QUIET" --dbname="${config[evn_db_name]}" --file="$HOME/tmp/$SITE.sql"
    # fi
    INFO "Chargement des données JSON dans Postgresql ${config[evn_db_name]} : fin"
    ;;

    all)
    # Download and then Store
    DEBUG "Début téléchargement depuis le site : ${config[evn_site]}" | tee "$HOME/tmp/mail_fin.txt"
    DEBUG "Début téléchargement depuis le site : ${config[evn_site]}" &> "$EVN_LOG"
    $0 --download "$PYTHON_VERBOSE" "$TEST" --site="$SITE" --logfile="$EVN_LOG" &>> "$EVN_LOG"

    DEBUG "Chargement des fichiers json dans la base ${config[evn_db_name]}" | tee -a "$HOME/tmp/mail_fin.txt"
    DEBUG "Chargement des fichiers json dans la base ${config[evn_db_name]}" &>> "$EVN_LOG"
    $0 --store "$PYTHON_VERBOSE" "$TEST" --site="$SITE" --logfile="$EVN_LOG" &>> "$EVN_LOG"

    DEBUG "Fin transfert depuis le site : ${config[evn_site]}" | tee -a "$HOME/tmp/mail_fin.txt"
    DEBUG "Fin transfert depuis le site : ${config[evn_site]}" &>> "$EVN_LOG"
    links -dump "${config[evn_site]}index.php?m_id=23" | fgrep "Les part" | sed 's/   Les partenaires/Total des observations du site :/' >> $HOME/tmp/mail_fin.txt
    expander3.py --eval "evn_db_name=\"${config[evn_db_name]}\";evn_db_schema=\"${config[evn_db_schema]}\";evn_db_group=\"${config[evn_db_group]}\";evn_db_user=\"${config[evn_db_user]}\"" --file Sql/CountRows.sql > $HOME/tmp/CountRows.sql
    env PGOPTIONS="-c client-min-messages=$CLIENT_MIN_MESSAGE" \
    psql "$SQL_QUIET" --dbname="${config[evn_db_name]}" --file="$HOME/tmp/CountRows.sql" > "$HOME/tmp/counted_rows.log"
    fgrep "nb_" "$HOME/tmp/counted_rows.log" >> "$HOME/tmp/mail_fin.txt"
    echo "Bilan du script : ERROR / WARN :" >> "$HOME/tmp/mail_fin.txt"
    ! fgrep -c "ERROR" "$EVN_LOG" >> "$HOME/tmp/mail_fin.txt"
    ! fgrep -c "WARN" "$EVN_LOG" >> "$HOME/tmp/mail_fin.txt"
    INFO "Fin de l'export des données" | tee -a "$HOME/tmp/mail_fin.txt"
    INFO "Fin de l'export des données"  >> "$EVN_LOG"
    gzip "$EVN_LOG"
    mailx --subject="Chargement de ${config[evn_site]}" --attach="$EVN_LOG.gz" ${config[evn_admin_mail]} < "$HOME/tmp/mail_fin.txt"
    #rm -f "$HOME/tmp/mail_fin.txt"
    ;;

    update)
    # Test mode, with limited volume of data managed
    INFO "Mise à jour incrémentale des données"

    INFO "Téléchargement et stockage en base - MODE TEST : début"
    export_vn/export_vn.py $PYTHON_VERBOSE $TEST $SITE
    INFO "Téléchargement et stockage en base - MODE TEST : fin"
    ;;

    *)
    # Unknown option
    ERROR "ERREUR: option inconnue"
    ;;

esac
