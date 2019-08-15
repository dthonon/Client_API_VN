The number of concurrent database insertion threads was 4, which
is too much for the work required. At most 1 or 2 are used.
The default is now 2 workers.

NOTE: if your YAML configuration file contrains a `[tuning]` section,
please modify `db_worker_threads: 2`.
