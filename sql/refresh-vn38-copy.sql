-- Refresh vn38-copy materialized views
-- Add to crontab: 
-- 0 5 * * * psql --file=/home/xfer38/Client_API_VN/sql/refresh-vn38-copy.sql faune_isere
REFRESH MATERIALIZED VIEW src_vn_copy.mv_local_admin_units;
REFRESH MATERIALIZED VIEW src_vn_copy.mv_observations;
REFRESH MATERIALIZED VIEW src_vn_copy.mv_places;
REFRESH MATERIALIZED VIEW src_vn_copy.mv_species;
REFRESH MATERIALIZED VIEW src_vn_copy.mv_taxo_groups;
