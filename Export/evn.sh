#!/usr/bin/env bash
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
# set -o nounset  # unset values give error
set -o pipefail # prevents errors in a pipeline from being masked

# Required when running from crontab
cd "$(dirname "$0")";
PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games"

# Analyze script options
OPTS=`getopt -o v --long all,download,edit,help,init,logfile:,site:,store,test,verbose -- "$@"`
if [ "$?" != 0 ] ; then echo "Option non reconnue" >&2 ; exit 1 ; fi
# echo "$OPTS"
eval set -- "$OPTS"
VERBOSE=false
CMD="help"
SITE=
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
        -v | --verbose ) VERBOSE=true; shift ;;
        --test ) CMD="test"; shift ;;
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

# Logging file, created if not given by --logfile parameter
if [ -z "$EVN_LOG" ]
then
    EVN_LOG="$HOME/tmp/evn_all_$(date '+%Y-%m-%d_%H:%M:%S').log"
    touch "$EVN_LOG"
fi
B_LOG -f "$EVN_LOG" --file-prefix-enable --file-suffix-enable

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

# Switch on possible actions
case "$CMD" in
    help)
    # Provide heps on command
    INFO "Aide en ligne à rédiger"
    INFO "Mail admin : ${config[evn_admin_mail]}"
    ;;

    test)
    # Testing configuration file
    INFO "Test de la configuration"
    DEBUG "Site : $SITE"
    DEBUG "Working directory $(pwd)"
    DEBUG "Mail admin : ${config[evn_admin_mail]}"
    DEBUG "Logging : ${config[evn_logging]}"
    DEBUG "URL site : ${config[evn_site]}"
    DEBUG "Database name : ${config[evn_db_name]}"
    ;;

    init)
    #
    INFO "Création de la base de données : début"
    DEBUG "1. Base de données"
    expander3.py --eval "evn_db_name=\"${config[evn_db_name]}\";evn_db_schema=\"${config[evn_db_schema]}\";evn_db_group=\"${config[evn_db_group]}\";evn_db_user=\"${config[evn_db_user]}\"" --file Sql/InitDB.sql > $HOME/tmp/InitDB.sql
    env PGOPTIONS="-c client-min-messages=$CLIENT_MIN_MESSAGE" \
    psql "$SQL_QUIET" --dbname=postgres --file=$HOME/tmp/InitDB.sql
    INFO "Création de la base de données : fin"
    ;;

    edit)
    # Edit configuration file
    INFO "Edition du fichier de configuration"
    editor "$evn_conf"
    ;;

    download)
    # Create directories as needed
    INFO "Début téléchargement depuis le site ${config[evn_site]} : début"
    rm -f "$HOME/${config[evn_file_store]}/${config[evn_site]}/*.json.gz"
    python3 Python/DownloadFromVN.py $PYTHON_VERBOSE --site=$SITE 2>> "$EVN_LOG"
    INFO "Téléchargement depuis l'API du site ${config[evn_site]} : fin"
    ;;

    store)
    # Store json files to Postgresql database
    INFO "Chargement des données JSON dans Postgresql ${config[evn_db_name]} : début"
    DEBUG "1. Création des tables"
    expander3.py --eval "evn_db_name=\"${config[evn_db_name]}\";evn_db_schema=\"${config[evn_db_schema]}\";evn_db_group=\"${config[evn_db_group]}\";evn_db_user=\"${config[evn_db_user]}\"" --file Sql/CreateTables.sql > $HOME/tmp/CreateTables.sql
    env PGOPTIONS="-c client-min-messages=$CLIENT_MIN_MESSAGE" \
    psql "$SQL_QUIET" --dbname=postgres --file=$HOME/tmp/CreateTables.sql
    DEBUG "2. Insertion dans la base"
    Python/InsertInDB.py "$PYTHON_VERBOSE" --site="$SITE"
    DEBUG "3. Création des vues"
    expander3.py --eval "evn_db_name=\"${config[evn_db_name]}\";evn_db_schema=\"${config[evn_db_schema]}\";evn_db_group=\"${config[evn_db_group]}\";evn_db_user=\"${config[evn_db_user]}\"" --file Sql/CreateViews.sql > $HOME/tmp/CreateViews.sql
    env PGOPTIONS="-c client-min-messages=$CLIENT_MIN_MESSAGE" \
    psql "$SQL_QUIET" --dbname=postgres --file=$HOME/tmp/CreateViews.sql
    DEBUG "4. Mise à jour des vues et indexation des tables et vues"
    expander3.py --eval "evn_db_name=\"${config[evn_db_name]}\";evn_db_schema=\"${config[evn_db_schema]}\";evn_db_group=\"${config[evn_db_group]}\";evn_db_user=\"${config[evn_db_user]}\"" \
      --file Sql/UpdateIndex.sql > "$HOME/tmp/UpdateIndex.sql"
    env PGOPTIONS="-c client-min-messages=$CLIENT_MIN_MESSAGE" \
      psql "$SQL_QUIET" --dbname=postgres --file="$HOME/tmp/UpdateIndex.sql"
    if [ -f "$HOME/${config[evn_sql_scripts]}/$SITE.sql" ]
    then
      DEBUG "5. Execution du script local : $HOME/${config[evn_sql_scripts]}/$SITE.sql"
      expander3.py --eval "evn_db_name=\"${config[evn_db_name]}\";evn_db_schema=\"${config[evn_db_schema]}\";evn_db_group=\"${config[evn_db_group]}\";evn_db_user=\"${config[evn_db_user]}\"" \
        --file "$HOME/${config[evn_sql_scripts]}/$SITE.sql" > "$HOME/tmp/$SITE.sql"
      env PGOPTIONS="-c client-min-messages=$CLIENT_MIN_MESSAGE" \
        psql "$SQL_QUIET" --dbname=postgres --file="$HOME/tmp/$SITE.sql"
    fi
    INFO "Chargement des données JSON dans Postgresql ${config[evn_db_name]} : fin"
    ;;

    all)
    # Download and then Store
    DEBUG "Début téléchargement depuis le site : ${config[evn_site]}"
    $0 --download $PYTHON_VERBOSE --site="$SITE" --logfile="$EVN_LOG"
    DEBUG "Chargement des fichiers json dans la base ${config[evn_db_name]}"
    $0 --store $PYTHON_VERBOSE --site="$SITE" --logfile="$EVN_LOG"
    DEBUG "Fin transfert depuis le site : ${config[evn_site]}"
    links -dump "${config[evn_site]}index.php?m_id=23" | fgrep "Les part" | sed 's/Les partenaires/Total des observations du site :/' > $HOME/tmp/mail_fin.txt
    expander3.py --eval "evn_db_name=\"${config[evn_db_name]}\";evn_db_schema=\"${config[evn_db_schema]}\";evn_db_group=\"${config[evn_db_group]}\";evn_db_user=\"${config[evn_db_user]}\"" --file Sql/CountRows.sql > $HOME/tmp/CountRows.sql
    env PGOPTIONS="-c client-min-messages=$CLIENT_MIN_MESSAGE" \
    psql "$SQL_QUIET" --dbname=postgres --file="$HOME/tmp/CountRows.sql" > "$HOME/tmp/counted_rows.log"
    fgrep "nb_" "$HOME/tmp/counted_rows.log" >> "$HOME/tmp/mail_fin.txt"
    echo "Bilan du script : ERROR / WARN :" >> "$HOME/tmp/mail_fin.txt"
    ! fgrep -c "ERROR" "$EVN_LOG" >> "$HOME/tmp/mail_fin.txt"
    ! fgrep -c "WARN" "$EVN_LOG" >> "$HOME/tmp/mail_fin.txt"
    gzip "$EVN_LOG"
    INFO "Fin de l'export des données"
    mailx --subject="Chargement de ${config[evn_site]}" --attach="$EVN_LOG.gz" ${config[evn_admin_mail]} < "$HOME/tmp/mail_fin.txt"
    #rm -f "$HOME/tmp/mail_fin.txt"
    ;;

    *)
    # Unknown option
    ERROR "ERREUR: option inconnue"
    ;;

esac
