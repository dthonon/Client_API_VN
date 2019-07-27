Number of concurrent database insert/update and queue size are parameters 
in YAML file, ``[tuning]`` section:

.. code-block:: yaml

    # Postgresql DB tuning parameters
    db_worker_threads: 4
    db_worker_queue: 100000
