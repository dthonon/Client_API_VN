For sites with a large number of observations per day, the minimum was too large,
leading to chunks exceeding 10 000 observations. Large chunk size reduce parallel
processing between client and server.
The minimum is now 5 days by default.

NOTE: if your YAML configuration file contrains a `[tuning]` section,
please modify `pid_limit_min: 5`. If your chunk size are still larger
than 10 000 observations, you can reduce it further.
