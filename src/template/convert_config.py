"""
Sample application: skeleton for new applications

"""

import logging
import sys
from pathlib import Path

import click
from tomlkit import boolean, comment, document, dumps, nl, table

from . import __version__

logger = logging.getLogger(__name__)


@click.version_option(package_name="Client_API_VN")
@click.group()
@click.option("--verbose/--quiet", default=False, help=_("Increase or decrease output verbosity"))
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
    # with open(in_config) as in_file:
    #     in_settings = yaml.safe_load(in_file)

    # Write configuration to file
    logger.info(_("Writing configuration data to %s"), out_config)
    cfg = document()
    cfg.add(comment("Configuration file for export_vn."))
    cfg.add(comment("Needs to be customized for each site. See comments below for details"))
    main = table(is_super_table=False)
    main.add(comment("General parameters"))
    main.add(comment("Mail address for the execution report"))
    main.append("admin_mail", "nom.prenom@example.net")
    cfg.append("main", main)

    controler = table(is_super_table=True)
    controler.add(comment("Biolovision API controlers parameters"))
    controler.add(comment("Enables or disables download from each Biolovision API"))
    controler.add(comment("Also defines scheduling (cron-like) parameters, in UTC"))
    controler.add(comment("See https://apscheduler.readthedocs.io/en/stable/modules/triggers/cron.html"))
    api = table(is_super_table=True)
    api.add(comment("Enable/disable download from this controler"))
    api.append("enabled", boolean("true"))
    schedule = table()
    schedule.add(comment("Every Friday at 23:00 UTC"))
    schedule.append("day_of_week", 4)
    schedule.append("hour", 23)
    api.append("schedule", schedule)
    controler.append("entities", api)
    controler.append("families", api)
    controler.append("local_admin_units", api)
    controler.append("observations", api)
    controler.append("observers", api)
    controler.append("places", api)
    controler.append("taxo_groups", api)
    controler.append("territorial_units", api)
    controler.append("validations", api)

    cfg.add("controler", controler)

    cfg.add(nl())
    cfg.add(comment(""))

    print(dumps(cfg))


def run():
    """Entry point for console_scripts"""
    main(sys.argv[1:])


# Main wrapper
if __name__ == "__main__":
    run()
