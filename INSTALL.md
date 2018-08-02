**Rédaction en cours**

# Installation de l'outil d'export sur un serveur

## Installation de l'environnement
Sur un serveur Debian Stretch (9)
``` sh
# Ajout du dépot PostgreSQL et de la clé 
sudo echo "deb http://apt.postgresql.org/pub/repos/apt stretch-pgdg main" >> /etc/apt/sources.list.d/postgresql.list
wget --quiet -O - http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc | sudo apt-key add -

# Mise à jour des dépots
sudo apt update

# Installation de Postgresql / PostGIS
sudo apt install postgresql-10 postgresql-10-postgis-2.4 postgresql-10-postgis-scripts postgis

# Installation de Python3 et des modules requis
sudo apt install  python3.5 python3-requests python3-requests-oauthlib python3-pip
sudo pip3 install pyexpander
```

## Clonage du dépot d'origine

``` sh
cd ~/
git clone https://framagit.org/lpo/Client_API_VN.git
```

## Configuration de l'application
L'initialisation de l'application nécessite a minima un argument qui est un identifiant de votre site visionature (ex fauneardeche ou vn07 pour faune-ardeche.org).

``` sh
cd Client_API_VN/Export
./evn.sh --site vn07 --edit
```

L'application créée alors à la racine de votre dossier utilisateur un fichier de configuration qui dans le cas de cet exemple sera `~/.evn_vn07.ini` et l'ouvre dans un éditeur de texte (par défaut `nano`, quelques infos sur cet éditeur [ici](https://korben.info/utiliser-nano.html))

## Création de l'utilisateur de la bdd

``` sql
create role dbuser login superuser encrypted password 'dbpwd';
```

## Initialisation de l'application

``` sh
cd Client_API_VN/Export
./evn.sh --site=vn07 --init
```


