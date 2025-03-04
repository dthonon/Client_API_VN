# Guide de mise à niveau en version 3

## Principales évolutions

La version 3 comporte des évolutions importantes par rapport à la version 2. Les principales évolutions sont les suivantes :

- Changement du format du fichier de configuration. Le nouveau format utilise la syntaxe TOML, qui est plus lisible. Un utilitaire permet la conversion du fichier YAML actuel vers ce nouveau format.
- Evolution de la gestion multi-site. En version 2, il était possible de télécharger plusieurs sites vers une même base de données. Mais il n'était pas possible de lancer des transferts distinct depuis le même compte. En version 3, un fichier de configuration permet de télécharger un seul site, mais il est maintenant possible d'utiliser le même compte pour effectuer plusieurs téléchargement simultanément.
- Modification de la syntaxe des commandes
- Utilisation de `poetry` pour la gestion des dépendances

Ces évolutions, ainsi que les démarches à réaliser pour la mise à niveau, sont détaillées dans les sections suivantes :

### Fichier de configuration

Le fichier de configuration utilise maintenant le format [TOML](https://toml.io/en/). Il est structuré en sections, par exemple `[controler]` et en sous-sections, par exemple `[controler.entities.schedule]`.

A part le format, les principales différences avec la version V2 sont :

- Le fichier est différent selon les applications transfer_vn et update_vn. Il ne contient que ce qui est nécessaire pour chaque application. Un fichier modèle est fourni en exécutant `transfer_vn init CONFIG` ou `update_vn init CONFIG`, où CONFIG est le nom du fichier de configuration TOML qui est créé dans le répertoire racine.
- Un seul site peut être défini par fichier de configuration. Voir [Gestion de plusieurs sites](#gestion-de-plusieurs-sites) pour la possibilité d'utiliser plusieurs instances de `transfer_vn` avec un seul compte utilisateur.
- Le filtre par groupe taxonomique est une liste des identifiants de groupes taxonomiques suivi d'un booléen.

Il est possible de convertir un fichier de configuration V2 en fichier de configuration V3, en utilisant l'utilitaire `config_file`.

```shell
Usage: config_file [OPTIONS] COMMAND [ARGS]...

  Update biolovision database.

  IN_CONFIG: YAML input configuration filename

  OUT_CONFIG: TOML output configuration filename

Options:
  --verbose / --quiet  Increase or decrease output verbosity.
  --version            Show the version and exit.
  --help               Show this message and exit.

Commands:
  convert  Convert configuration file from YAML to TOML.
  prints   Print TOML configuration, with defaults.
```

### Gestion de plusieurs sites

qsdfqsdf

### Syntaxe des commandes

qsdfqsf