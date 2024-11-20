Thin Python binding to Biolovision API, returning dict instead of JSON.
Currently, only a subset of API controlers are implemented, and only a subset
of functions and parameters for implemented controlers.
See details in each class.

Each Biolovision controler is mapped to a python class.
Class name is derived from controler name by removing `_` and using CamelCase.
Methods names are similar to the corresponding API call, prefixed by `api`.
For example, method `api_list` in class `LocalAdminUnits` will
call `local_admin_units`.

Most notable difference is that API chunks are grouped under `data`, i.e.
calling `species_list('1')` will return all birds in one array under `data` key.
This means that requests returning lots of chunks (all bird sightings !)
must be avoided, as memory could be insufficient.

`max_chunks __init__` parameter controls the maximum number of chunks
allowed and raises an exception if it exceeds.

Biolovision API to Classes mapping:

| Controler                        | Class                 |
|----------------------------------|-----------------------|
| `taxo_groups`                    | `TaxoGroupsAPI`       |
| `families`                       | `FamiliesAPI`         |
| `species`                        | `SpeciesAPI`          |
| `territorial_units`              | `TerritorialUnitsAPI` |
| `local_admin_units`              | `LocalAdminUnitsAPI`  |
| `places`                         | `PlacesAPI`           |
| `observers`                      | `ObserversAPI`        |
| `entities`                       | `EntitiesAPI`         |
| `protocol`                       | NA                    |
| `export_organizations`           | NA                    |
| `observations`                   | `ObservationsAPI`     |
| `fields`                         | `FieldsAPI`           |
| `media`                          | NA                    |
| `import_files`                   | NA                    |
| `import_files_observations`      | NA                    |
| `validations`                    | `ValidationsAPI`      |
| `mortality`                      | NA                    |
| `gypaetus_barbatus_birds`        | NA                    |
| `gypaetus_barbatus_informations` | NA                    |
| `observations_by_polygon`        | NA                    |
| `polygons`                       | NA                    |
| `grids`                          | NA                    |
| `grids_communes`                 | NA                    |
| `atlas_documents`                | NA                    |

::: biolovision.api
