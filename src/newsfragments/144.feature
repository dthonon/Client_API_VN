In order to get timing data of each request, table import.download_log is extended.
If upgrade without recreating JSON tables, you must run the following script::
    ALTER TABLE import.download_log ADD COLUMN length integer;
    ALTER TABLE import.download_log ADD COLUMN duration integer;
    CREATE INDEX ix_import_download_log_duration ON import.download_log USING btree(duration);
    CREATE INDEX ix_import_download_log_length ON import.download_log USING btree(length);

