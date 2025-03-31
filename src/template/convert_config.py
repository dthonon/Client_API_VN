"""
Sample application: skeleton for new applications

"""

import logging
import sys
from pathlib import Path

import click
import yaml
from dynaconf import Dynaconf, inspect_settings
from tomlkit import array, boolean, comment, document, dump, nl, table

from . import __version__

logger = logging.getLogger(__name__)


@click.version_option(package_name="Client_API_VN")
@click.group()
@click.option("--verbose/--quiet", default=False, help=_("Increase or decrease output verbosity."))
def main(
    verbose: bool,
) -> None:
    """Update biolovision database.

    IN_CONFIG: YAML input configuration filename

    OUT_CONFIG: TOML output configuration filename
    """

    # Define logger format and handlers
    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    # Create formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    ch.setFormatter(formatter)
    # Add the handlers to the logger
    logger.addHandler(ch)

    # Define verbosity
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.info(_("update_vn version %s"), __version__)

    return None


def _controler(in_settings: dict, controler: str) -> table:
    "Return the controler table"
    api = table(is_super_table=True)
    api.add(comment("Enable/disable download from this controler."))
    api.append("enabled", boolean(in_settings["controler"][controler]["enabled"]))
    schedule = table()
    schedule.add(comment("Schedule in year/month/day/week/day_of_week/hour/minute."))
    if "year" in in_settings["controler"][controler]["schedule"]:
        schedule.append("year", in_settings["controler"][controler]["schedule"]["year"])
    if "month" in in_settings["controler"][controler]["schedule"]:
        schedule.append("month", in_settings["controler"][controler]["schedule"]["month"])
    if "day" in in_settings["controler"][controler]["schedule"]:
        schedule.append("day", in_settings["controler"][controler]["schedule"]["day"])
    if "week" in in_settings["controler"][controler]["schedule"]:
        schedule.append("week", in_settings["controler"][controler]["schedule"]["week"])
    if "day_of_week" in in_settings["controler"][controler]["schedule"]:
        schedule.append("day_of_week", in_settings["controler"][controler]["schedule"]["day_of_week"])
    if "hour" in in_settings["controler"][controler]["schedule"]:
        schedule.append("hour", in_settings["controler"][controler]["schedule"]["hour"])
    if "minute" in in_settings["controler"][controler]["schedule"]:
        schedule.append("minute", in_settings["controler"][controler]["schedule"]["minute"])
    api.append("schedule", schedule)
    return api


@main.command()
@click.argument(
    "in_config",
)
@click.argument(
    "out_config",
)
def convert(in_config: str, out_config: str) -> None:
    """Convert configuration file from YAML to TOML."""
    logger = logging.getLogger(__name__ + ".update")
    # Check file existence
    if not (Path.home() / in_config).is_file():
        logger.critical(_("Input configuration file %s does not exist"), str(Path.home() / in_config))
        raise FileNotFoundError
    if (Path.home() / out_config).is_file():
        logger.critical(_("Output configuration file %s already exists"), str(Path.home() / out_config))
        raise FileNotFoundError

    # Get configuration from file
    logger.info(_("Getting configuration data from %s"), in_config)
    with open(Path.home() / in_config) as in_file:
        in_settings = yaml.safe_load(in_file)
    # pprint.pp(in_settings)

    # Prepare configuration document
    logger.info(_("Creating configuration document"))
    cfg = document()
    cfg.add(comment("Configuration file for export_vn."))
    cfg.add(comment("Needs to be customized for each site. See comments below for details."))

    cfg.add(nl())
    cfg.add(comment("------------------- Controler section -------------------"))

    controlers = table(is_super_table=True)
    controlers.add(comment("Biolovision API controlers parameters."))
    controlers.add(comment("Enables or disables download from each Biolovision API."))
    controlers.add(comment("Also defines scheduling (cron-like) parameters, in UTC."))
    controlers.add(comment("See https://apscheduler.readthedocs.io/en/stable/modules/triggers/cron.html."))

    controlers.append("entities", _controler(in_settings=in_settings, controler="entities"))
    controlers.append("families", _controler(in_settings=in_settings, controler="families"))
    controlers.append("fields", _controler(in_settings=in_settings, controler="families"))
    controlers.append("local_admin_units", _controler(in_settings=in_settings, controler="local_admin_units"))
    controlers.append("observations", _controler(in_settings=in_settings, controler="observations"))
    controlers.append("observers", _controler(in_settings=in_settings, controler="observers"))
    controlers.append("places", _controler(in_settings=in_settings, controler="places"))
    controlers.append("species", _controler(in_settings=in_settings, controler="places"))
    controlers.append("taxo_groups", _controler(in_settings=in_settings, controler="taxo_groups"))
    controlers.append("territorial_units", _controler(in_settings=in_settings, controler="territorial_units"))
    controlers.append("validations", _controler(in_settings=in_settings, controler="validations"))
    cfg.add("controler", controlers)

    cfg.add(nl())
    cfg.add(comment("------------------- Filter section -------------------"))

    filters = table(is_super_table=True)
    filters.add(comment("Observations filter, to limit download scope."))
    filters.add(nl())

    territorial_unit_ids = array()
    filters.add(comment("List of territorial_unit_ids to download."))
    filters.add(comment("Note : use the territory short_name, not the territory id."))
    filters.add(comment('Example: territorial_units_ids = ["7", "38"]'))
    filters.add(comment("Leave empty to download all territorial_units."))
    filters.append("territorial_unit_ids", territorial_unit_ids)

    filters.add(nl())
    filters.add(comment("Optional start and end dates."))
    filters.add(comment("start_date = 2019-08-01"))
    filters.add(comment("end_date = 2019-09-01"))
    filters.append("type_date", "entry")

    filters.add(nl())
    filters.add(comment("Use short (recommended) or long JSON data."))
    filters.append("json_format", "short")

    taxo_include = table()
    taxo_include.add(comment("List of taxo_groups, flagged for download."))
    taxo_include.add(comment(" - true: enable download"))
    taxo_include.add(comment(" - false: disable download"))
    taxo_include.add(
        comment("Taxo_groups with limited access must be excluded, if no access right is granted to the account.")
    )
    taxo_include.append(
        "TAXO_GROUP_BIRD", boolean("false" if "TAXO_GROUP_BIRD" in in_settings["filter"]["taxo_exclude"] else "true")
    )
    taxo_include.append(
        "TAXO_GROUP_BAT", boolean("false" if "TAXO_GROUP_BAT" in in_settings["filter"]["taxo_exclude"] else "true")
    )
    taxo_include.append(
        "TAXO_GROUP_MAMMAL",
        boolean("false" if "TAXO_GROUP_MAMMAL" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_SEA_MAMMAL",
        boolean("false" if "TAXO_GROUP_SEA_MAMMAL" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_REPTILIAN",
        boolean("false" if "TAXO_GROUP_REPTILIAN" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_AMPHIBIAN",
        boolean("false" if "TAXO_GROUP_AMPHIBIAN" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_ODONATA",
        boolean("false" if "TAXO_GROUP_ODONATA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_BUTTERFLY",
        boolean("false" if "TAXO_GROUP_BUTTERFLY" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_MOTH", boolean("false" if "TAXO_GROUP_MOTH" in in_settings["filter"]["taxo_exclude"] else "true")
    )
    taxo_include.append(
        "TAXO_GROUP_ORTHOPTERA",
        boolean("false" if "TAXO_GROUP_ORTHOPTERA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_HYMENOPTERA",
        boolean("false" if "TAXO_GROUP_HYMENOPTERA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_ORCHIDACEAE",
        boolean("false" if "TAXO_GROUP_ORCHIDACEAE" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_TRASH", boolean("false" if "TAXO_GROUP_TRASH" in in_settings["filter"]["taxo_exclude"] else "true")
    )
    taxo_include.append(
        "TAXO_GROUP_EPHEMEROPTERA",
        boolean("false" if "TAXO_GROUP_EPHEMEROPTERA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_PLECOPTERA",
        boolean("false" if "TAXO_GROUP_PLECOPTERA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_MANTODEA",
        boolean("false" if "TAXO_GROUP_MANTODEA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_AUCHENORRHYNCHA",
        boolean("false" if "TAXO_GROUP_AUCHENORRHYNCHA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_HETEROPTERA",
        boolean("false" if "TAXO_GROUP_HETEROPTERA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_COLEOPTERA",
        boolean("false" if "TAXO_GROUP_COLEOPTERA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_NEVROPTERA",
        boolean("false" if "TAXO_GROUP_NEVROPTERA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_TRICHOPTERA",
        boolean("false" if "TAXO_GROUP_TRICHOPTERA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_MECOPTERA",
        boolean("false" if "TAXO_GROUP_MECOPTERA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_DIPTERA",
        boolean("false" if "TAXO_GROUP_DIPTERA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_PHASMATODEA",
        boolean("false" if "TAXO_GROUP_PHASMATODEA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_ARACHNIDA",
        boolean("false" if "TAXO_GROUP_ARACHNIDA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_SCORPIONES",
        boolean("false" if "TAXO_GROUP_SCORPIONES" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_FISH", boolean("false" if "TAXO_GROUP_FISH" in in_settings["filter"]["taxo_exclude"] else "true")
    )
    taxo_include.append(
        "TAXO_GROUP_MALACOSTRACA",
        boolean("false" if "TAXO_GROUP_MALACOSTRACA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_GASTROPODA",
        boolean("false" if "TAXO_GROUP_GASTROPODA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_BIVALVIA",
        boolean("false" if "TAXO_GROUP_BIVALVIA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append(
        "TAXO_GROUP_BRANCHIOPODA",
        boolean("false" if "TAXO_GROUP_BRANCHIOPODA" in in_settings["filter"]["taxo_exclude"] else "true"),
    )
    taxo_include.append("TAXO_GROUP_SPERMATOPHYTA", boolean("false"))
    taxo_include.append("TAXO_GROUP_BRYOPHYTA", boolean("false"))
    taxo_include.append("TAXO_GROUP_LICHEN", boolean("false"))
    taxo_include.append("TAXO_GROUP_FUNGI", boolean("false"))
    taxo_include.append("TAXO_GROUP_ALGAE", boolean("false"))
    taxo_include.append("TAXO_GROUP_PTERIDOPHYTA", boolean("false"))
    taxo_include.append("TAXO_GROUP_STERNORRHYNCHA", boolean("false"))
    taxo_include.append("TAXO_GROUP_MYRIAPODA", boolean("false"))
    taxo_include.append("TAXO_GROUP_ANNELIDA", boolean("false"))
    taxo_include.append("TAXO_GROUP_DERMAPTERA", boolean("false"))
    taxo_include.append("TAXO_GROUP_MEDUSOZOA", boolean("false"))
    taxo_include.append("TAXO_GROUP_PORIFERA", boolean("false"))
    taxo_include.append("TAXO_GROUP_BACTERIA", boolean("false"))
    taxo_include.append("TAXO_GROUP_MYXOGASTRIA", boolean("false"))
    taxo_include.append("TAXO_GROUP_BLATTARIA", boolean("false"))
    taxo_include.append("TAXO_GROUP_ARTHROPODA", boolean("false"))
    taxo_include.append("TAXO_GROUP_IGNOTUS", boolean("false"))
    taxo_include.append("TAXO_GROUP_FORMICOIDEA", boolean("false"))
    filters.append("taxo_download", taxo_include)

    cfg.append("filter", filters)

    cfg.add(nl())
    cfg.add(comment("------------------- Site section -------------------"))
    site = table(is_super_table=True)
    if len(in_settings["site"]) > 1:
        logger.warning(_("Multiple sites are not supported. Only the first site will be used."))
    else:
        k = next(iter(in_settings["site"].keys()))
        s = in_settings["site"][k]
        site.add(comment(f"Sites parameters for {k}."))
        site.add(nl())
        site.add(comment("Enable download from this site."))
        site.append("enabled", boolean("true" if s["enabled"] else "false"))
        site.add(comment("Site name, used as key in database tables."))
        site.append("name", k)
        site.add(comment("Site URL."))
        site.append("URL", s["site"])
        site.add(comment("Username."))
        site.append("user_email", s["user_email"])
        site.add(comment("User password."))
        site.append("user_pw", s["user_pw"])
        site.add(comment("Client key, obtained from Biolovision."))
        site.append("client_key", s["client_key"])
        site.add(comment("Client secret, obtained from Biolovision."))
        site.append("client_secret", s["client_secret"])
    cfg.append("site", site)

    cfg.add(nl())
    cfg.add(comment("------------------- File section -------------------"))
    files = table(is_super_table=False)
    files.add(comment("File storage backend parameters."))
    files.add(nl())
    files.add(comment("Enable storing to file."))
    files.append("enabled", boolean("true" if in_settings["file"]["enabled"] else "false"))
    files.add(comment("Top level path name for downloaded file storage, relative to $HOME."))
    files.append("file_store", in_settings["file"]["file_store"])
    cfg.append("file", files)

    cfg.add(nl())
    cfg.add(comment("------------------- Database section -------------------"))
    databases = table(is_super_table=False)
    databases.add(comment("Postgresql backend related parameters."))
    databases.add(nl())
    databases.add(comment("Enable storing to file."))
    databases.append("enabled", boolean("true" if in_settings["database"]["enabled"] else "false"))
    databases.add(comment("Database host."))
    databases.append("db_host", in_settings["database"]["db_host"])
    databases.add(comment("Database IP port."))
    databases.append("db_port", in_settings["database"]["db_port"])
    databases.add(comment("Database name."))
    databases.append("db_name", in_settings["database"]["db_name"])
    databases.add(comment("Database schema inside db_name database, for imported JSON data."))
    databases.append("db_schema_import", in_settings["database"]["db_schema_import"])
    databases.add(comment("Database schema inside db_name database, for columns extracted from JSON."))
    databases.append("db_schema_vn", in_settings["database"]["db_schema_vn"])
    databases.add(comment("Postgresql user group accessing imported data."))
    databases.append("db_group", in_settings["database"]["db_group"])
    databases.add(comment("Postgresql user used to import data."))
    databases.append("db_user", in_settings["database"]["db_user"])
    databases.add(comment("Postgresql user password."))
    databases.append("db_pw", in_settings["database"]["db_pw"])
    databases.add(comment("Coordinates systems for local projection, see EPSG."))
    databases.append("db_out_proj", in_settings["database"]["db_out_proj"])
    cfg.append("database", databases)

    cfg.add(nl())
    cfg.add(comment("------------------- Tuning section -------------------"))
    tunings = table(is_super_table=False)
    tunings.add(comment("Optional tuning parameters, for expert use."))
    tunings.add(nl())
    tunings.add(comment("Max items in an API list request."))
    tunings.add(comment("Longer lists are split by API in max_list_length chunks."))
    tunings.append("max_list_length", in_settings["tuning"]["max_list_length"])
    tunings.add(comment("Max chunks in a request before aborting."))
    tunings.append("max_chunks", in_settings["tuning"]["max_chunks"])
    tunings.add(comment("Max retries of API calls before aborting."))
    tunings.append("max_retry", in_settings["tuning"]["max_retry"])
    tunings.add(comment("Maximum number of API requests, for debugging only."))
    tunings.add(comment("- 0 means unlimited"))
    tunings.add(comment("- >0 limit number of API requests"))
    tunings.append("max_requests", in_settings["tuning"]["max_requests"])
    tunings.add(comment("Delay between retries after an error."))
    tunings.append("retry_delay", in_settings["tuning"]["retry_delay"])
    tunings.add(comment("Delay between retries after an error HTTP 503 (service unavailable)."))
    tunings.append("unavailable_delay", in_settings["tuning"]["unavailable_delay"])
    tunings.add(comment("LRU cache size for common requests (taxo_groups...)."))
    tunings.append("lru_maxsize", in_settings["tuning"]["lru_maxsize"])
    tunings.add(comment("PID parameters, for throughput management."))
    tunings.append("pid_kp", in_settings["tuning"]["pid_kp"])
    tunings.append("pid_ki", in_settings["tuning"]["pid_ki"])
    tunings.append("pid_kd", in_settings["tuning"]["pid_kd"])
    tunings.append("pid_setpoint", in_settings["tuning"]["pid_setpoint"])
    tunings.append("pid_limit_min", in_settings["tuning"]["pid_limit_min"])
    tunings.append("pid_limit_max", in_settings["tuning"]["pid_limit_max"])
    tunings.append("pid_delta_days", in_settings["tuning"]["pid_delta_days"])
    tunings.add(comment("Scheduler tuning parameters."))
    tunings.append("sched_sqllite_file", "jobstore.sqlite")
    tunings.append("sched_executors", in_settings["tuning"]["sched_executors"])
    cfg.append("tuning", tunings)

    with open(Path.home() / out_config, "w") as fp:
        dump(cfg, fp)


@main.command()
@click.argument(
    "in_config",
)
def prints(in_config: str) -> None:
    """Print TOML configuration, with defaults."""
    logger = logging.getLogger(__name__ + ".update")
    # Check file existence
    if not (Path.home() / in_config).is_file():
        logger.critical(_("Input configuration file %s does not exist"), str(Path.home() / in_config))
        raise FileNotFoundError

    settings = Dynaconf(
        settings_files=[in_config],
    )

    inspect_settings(settings, print_report=True)


def run():
    """Entry point for console_scripts"""
    main(sys.argv[1:])


# Main wrapper
if __name__ == "__main__":
    run()
