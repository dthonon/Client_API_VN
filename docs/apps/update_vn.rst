=======================
update_vn Documentation
=======================

User Guide
==========

.. caution::
    This application changes or deletes items directly in the Biolovision
    database. Use with extreme care !


The application ``update_vn`` reads an input CSV file containing operations
to be applied to the Biolovision database. Each line of this file describes
an operation.


Initial setup
-------------

Initialize the sample YAML file in your HOME directory and edit with
your local details. The YAML file is self documented:

.. code:: bash 

    update_vn --init .evn_your_site.yaml
    editor $HOME/.evn_your_site.yaml

CSV file content
----------------

The CSV file must start with the mandatory first line with column headers::

    site;id_universal;path;operation;value


The next lines must contain the following columns:

- site, as defined in YAML site section
- id_universal of the sighting to be modified
- path to the attribute to modify, in `JSONPath syntax <https://goessner.net/articles/JsonPath/>`_,
  unused if operation is delete_observation
- operation:

  - replace: create, if this attibute is not present, or update a sighting 
    attribute
  - delete_attribute: remove the attribute with the given path and keep the 
    other attributes of the observation
  - delete_observation, to remove completely the observation

- value: if operation is replace, new value inserted or updated

Note: each operation is logged in hidden_comment, as a JSON message.
It is not possible to replace hidden_comment, as logging is appended.

For example::

    site;id_universal;path;operation;value
    Isère;2246086;$['data']['sightings'][0]['observers'][0]['atlas_code'];replace;4
    Isère;2246086;$['data']['sightings'][0]['observers'][0]['atlas_code'];delete_attribute;
    Isère;2246086;;delete_observation;

Running the application
-----------------------

The application runs as:

.. code:: bash 

    update_vn options config input

where::

    options  command line options described below
    config   YAML file, located in $HOME directory, described in sample file
    input    CSV file listing sightings to be updated

-h, --help             Prints help and exits
--version              Print version number
--verbose              Increase output verbosity
--quiet                Reduce output verbosity
--init                 Initialize the YAML configuration file



Operations Templates
====================

The following examples can be used as templates::

Modification du code projet
---------------------------

La liste des projets est accessible sur le site faune-xxx, dans "Administration" > "Gestion de projet"
Attention, le numéro de projet est spécifique à chaque site::

    site;id_universal;path;operation;value
    Isère;2775784;$['data']['sightings'][0]['observers'][0]['project'];replace;6

Modification de l'utilisateur
-----------------------------

Il faut modifier à la fois :

- traid : transmitter id
- @id : observer id

Il est possible de ne pas modifier le paramètre traid dans le cas de données intégrées
via un compte d'archives par exemple pour conserver le fait que la donnée a été importée::

    site;id_universal;path;operation;value
    Isère;2775784;$['data']['sightings'][0]['observers'][0]['@id'];replace;38
    Isère;2775784;$['data']['sightings'][0]['observers'][0]['traid'];replace;38

Ajout d'un commentaire
----------------------

Attention, texte entre guillemets simples::

    site;id_universal;path;operation;value
    Isère;2775784;$['data']['sightings'][0]['observers'][0]['comment'];replace;'test'

Changement de comptage
----------------------

Remplacement de "non compté" par un compte exact::

    site;id_universal;path;operation;value
    Isère;2775784;$['data']['sightings'][0]['observers'][0]['estimation_code'];replace;'EXACT_VALUE'
    Isère;2775784;$['data']['sightings'][0]['observers'][0]['count'];replace;1

Changement de la date
---------------------

La date est défine par timestamp calculé par la fonction Excel ``=(C2-DATE(1970;1;1))*86400``::

    site;id_universal;path;operation;value
    Isère;2775784;$['data']['sightings'][0]['date']['@timestamp'];replace;1465948800

Mortalité
---------

Ajout de la mortalité avec une cause::

    site;id_universal;path;operation;value
    Isère;2775784;$['data']['sightings'][0]['observers'][0]['has_death'];replace;2
    Isère;2775784;$['data']['sightings'][0]['observers'][0]['extended_info']['mortality']['death_cause2'];replace;'ROAD_VEHICLE'

Espèce
------

Modification en utilisant le numéro de l'espèce sur la plateforme concernée::

    site;id_universal;path;operation;value
    vn26;1399774;$['data']['sightings'][0]['species']['@id'];replace;'370'

