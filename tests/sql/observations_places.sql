-- Query sighting geography
SELECT observations.site, id_sighting, id_place, place, id_commune, local_admin_units.name AS commune, territorial_units.name AS département, territorial_units.id, territorial_units.short_name
FROM src_vn.observations
INNER JOIN src_vn.places ON places.id = observations.id_place
INNER JOIN src_vn.local_admin_units ON local_admin_units.id = places.id_commune
INNER JOIN src_vn.territorial_units ON territorial_units.id = local_admin_units.id_canton
ORDER BY site ASC, id_sighting ASC 
LIMIT 100
