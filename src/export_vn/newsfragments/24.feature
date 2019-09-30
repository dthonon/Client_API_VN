Major change on incremental (and full) download. 
All controlers can now be downloaded on a regular basis.
See README for more information on download process.

YAML configuration file must be updated to define download
schedule for all controlers. A typical example is given below:

  .. code-block:: yaml

    # Biolovision API controlers parameters
    # Enables or disables download from each Biolovision API
    # Also defines scheduling (cron-like) parameters, in UTC
    controler:
        entities:
            # Enable download from this controler
            enabled: true
            schedule:
                # Every Friday at 23:00 UTC
                day_of_week: 4
                hour: 23
        fields:
            # Enable download from this controler
            enabled: true
            schedule:
                # Every Friday at 23:00 UTC
                day_of_week: 4
                hour: 23
        local_admin_units:
            # Enable download from this controler
            enabled: true
            schedule:
                # Every Monday at 05:00 UTC
                day_of_week: 0
                hour: 5
        observations:
            # Enable download from this controler
            enabled: true
            # Define scheduling parameters
            schedule:
                # Every hour
                year: '*'
                month: '*'
                day: '*'
                week: '*'
                day_of_week: '*'
                hour: '*'
                minute: 0
        observers:
            # Enable download from this controler
            enabled: true
            schedule:
                # Every day at 06:00 UTC
                hour: 6
        places:
            # Enable download from this controler
            enabled: true
            schedule:
                # Every Thursday at 23:00 UTC
                day_of_week: 3
                hour: 23
        species:
            # Enable download from this controler
            enabled: true
            schedule:
                # Every Wednesday at 22:00 UTC
                day_of_week: 2
                hour: 22
        taxo_groups:
            # Enable download from this controler
            enabled: true
            schedule:
                # Every Wednesday at 22:00 UTC
                day_of_week: 2
                hour: 22
        territorial_units:
            # Enable download from this controler
            enabled: true
            schedule:
                # Every Thursday at 23:00 UTC
                day_of_week: 3
                hour: 23
