A new ``filter:`` section is added to YAML configuration file.
``taxo_exclude:`` list needs to be moved to this new section.

To limit full download to a time interval, you can add:

- ``start_date``, optional date of first observation. If omitted, start with earliest data.
- ``end_date``, optional date of last observation. If omitted, start with latest data.

Date format is YYYY-MM-DD.

For example:

  .. code-block:: yaml

    # Observations filter, to limit download scope
    filter:
        # List of taxo_groups to exclude from download
        # Uncommment taxo_groups to disable download
        taxo_exclude:
            #- TAXO_GROUP_BIRD
            #- TAXO_GROUP_BAT
            #- TAXO_GROUP_MAMMAL
            - TAXO_GROUP_SEA_MAMMAL
            #- TAXO_GROUP_REPTILIAN
            #- TAXO_GROUP_AMPHIBIAN
            #- TAXO_GROUP_ODONATA
            #- TAXO_GROUP_BUTTERFLY
            #- TAXO_GROUP_MOTH
            #- TAXO_GROUP_ORTHOPTERA
            #- TAXO_GROUP_HYMENOPTERA
            #- TAXO_GROUP_ORCHIDACEAE
            #- TAXO_GROUP_TRASH
            #- TAXO_GROUP_EPHEMEROPTERA
            #- TAXO_GROUP_PLECOPTERA
            #- TAXO_GROUP_MANTODEA
            #- TAXO_GROUP_AUCHENORRHYNCHA
            #- TAXO_GROUP_HETEROPTERA
            #- TAXO_GROUP_COLEOPTERA
            #- TAXO_GROUP_NEVROPTERA
            #- TAXO_GROUP_TRICHOPTERA
            #- TAXO_GROUP_MECOPTERA
            #- TAXO_GROUP_DIPTERA
            #- TAXO_GROUP_PHASMATODEA
            #- TAXO_GROUP_ARACHNIDA
            #- TAXO_GROUP_SCORPIONES
            #- TAXO_GROUP_FISH
            #- TAXO_GROUP_MALACOSTRACA
            #- TAXO_GROUP_GASTROPODA
            #- TAXO_GROUP_BIVALVIA
            #- TAXO_GROUP_BRANCHIOPODA
            - TAXO_GROUP_ALIEN_PLANTS
        # Use short (recommended) or long JSON data
        # json_format: short
        # Optional start and end dates
        # start_date: 2019-09-01
        # end_date: 2019-08-01
