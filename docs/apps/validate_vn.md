# validate_vn Documentation
## User Guide

This application validates downloaded JSON files against JSON schemas.
JSON files must fist be downloaded by `transfer_vn`.
If the JSON schema does not match with a downloaded file, an error message
is printed, describing the difference. The JSON schema should be modified
to comply with the newly downloaded files.

### Running the application

The application runs as:

```bash
validate_vn options config
```
where:

    options  command line options described below
    config   YAML file, located in $HOME directory, described in sample file

    -h, --help Prints help and exits
    --version Print version number
    --verbose Increase output verbosity
    --quiet Reduce output verbosity
    --init Initialize the YAML configuration file
    --validate Validation des schémas avec les fichier JSON téléchargés
    --report Rapport des propriétes des schémas
    --restore Rename a rendu leur nom d'origine aux fichiers
    --samples SAMPLES If float in range [0.0, 1.0], the parameter represents a proportion of files, else integer absolute counts.
