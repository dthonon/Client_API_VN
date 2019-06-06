Added parameter to YAML configuration file.
In ``database:`` section, the followng parameter defines the 
geographic projection (EPGS code) used to create 
``coord_x_local`` and ``coord_y_local``.
 
Optional parameters are added in a new ``tuning:`` section, for expert use::

.. code-block:: yaml
    # Tuning parameters, for expert use.
    tuning:
        # Max chunks in a request before aborting.
        max_chunks: 10
        # Max retries of API calls before aborting.
        max_retry: 5
        # Maximum number of API requests, for debugging only.
        # - 0 means unlimited
        # - >0 limit number of API requests
        max_requests: 0
        # LRU cache size for common requests (taxo_groups...)
        lru_maxsize: 32
        # Earliest year in the archive. Queries will not ge before this date.
        min_year: 1901
        # PID parameters, for throughput management.
        pid_kp: 0.0
        pid_ki: 0.003
        pid_kd: 0.0
        pid_setpoint: 10000
        pid_limit_min: 10
        pid_limit_max: 2000
        pid_delta_days: 15

Deprecated ``local:`` section and parameters must be removed. 
An error is raised if not.
>