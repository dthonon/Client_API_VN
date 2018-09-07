**Rédaction en cours**

# Installation de l'outil d'export sur un serveur

## Installation de l'environnement
Voir https://framagit.org/lpo/Client_API_VN/wikis/Installation%20guide%20debian%209
## Configuration de l'application
L'initialisation de l'application nécessite a minima un argument qui est un identifiant de votre site visionature (ex fauneardeche ou vn07 pour faune-ardeche.org).

``` sh
cd Client_API_VN/Export
./evn.sh --site vn07 --edit
```

L'application créée alors à la racine de votre dossier utilisateur un fichier de configuration qui dans le cas de cet exemple sera `~/.evn_vn07.ini` et l'ouvre dans un éditeur de texte (par défaut `nano`

## Création de l'utilisateur de la bdd

``` sql
create role dbuser login superuser encrypted password 'dbpwd';
```

## Initialisation de l'application

``` sh
cd Client_API_VN/Export
./evn.sh --site=vn07 --init
```
