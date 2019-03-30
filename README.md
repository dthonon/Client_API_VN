# Client_API_VN

Python application that transfers data from Biolovision/VisoNature web sites to a local Postgresql database.

## Getting Started

Download a copy of the code:
```bash
$ git clone https://framagit.org/lpo/Client_API_VN.git
```

Copy the sample YAML file to your HOME directory and edit with your local details.
```bash
$ cp export_vn/export_vn/evn_template.yaml $HOME/.evn_your_site.yaml
$ editor $HOME/.evn_your_site.yaml
```

You can then download all data, as enabled in the YAML file. 
Beware that, depending on the volume of observations, this can take hours. 
We recommend starting with a small taxonomic group first.
```bash
python3 export_vn/export_vn/transfer_vn.py --db-create --json_tables_create --col_tables_create --full .evn_your_site.yaml 
```

Once this is done, you can update the database with new observations:
```bash
python3 export_vn/export_vn/transfer_vn.py --update .evn_your_site.yaml 
```

### Prerequisites

Installation requires the followinf python module
- 

### Installing


## Running the tests

Explain how to run the automated tests for this system

## Running the application

The application runs as:
```bash
python3 export_vn/export_vn/transfer_vn.py options file
```
or
```bash
python3 -m export_vn.transfer_vn options file
```
where:
- options: command line options described below
- file: YAML file, located in $HOME directory, described in sample file

### Command-line options
  -h, --help            show this help message and exit
  --version             Imprime la version
  -v, --verbose         Plus verbeux
  -q, --quiet           Moins verbeux
  --db_drop             Détruit la base de données et les rôles
  --db_create           Crée la base de données et les rôle
  --json_tables_create  Crée, si elles n'existent pas, les tables JSON
  --col_tables_create   Crée ou recrée les tables en colonne
  --full                Réalise un téléchargement complèt
  --update              Réalise un téléchargement incrémental
  --count               Statistiques des observations par site et groupe taxonomique


## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Authors

* **Daniel Thonon** - *Initial work* - [DThonon](https://framagit.org/dthonon)
* **Frédéric Cloitre** - *Testing and bug fixing* - [fred.perso ](https://framagit.org/fred.perso)

See also the list of [contributors](https://framagit.org/lpo/Client_API_VN/graphs/master) who participated in this project.

## License

This project is licensed under the GNU GPL V3 License - see the [LICENSE.md](LICENSE) file for details

## Acknowledgments

* **Gaëtan Delaloye**, for providing examples and support during the development.

