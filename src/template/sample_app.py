#!/usr/bin/env python3
"""
Sample application: skeleton for new applications

"""

import importlib.resources
import logging
import shutil
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import click
from dynaconf import Dynaconf, ValidationError, Validator

from . import __version__

logger = logging.getLogger(__name__)


@click.version_option(package_name="Client_API_VN")
@click.group()
@click.option("--verbose/--quiet", default=False, help=_("Increase or decrease output verbosity"))
def main(
    verbose: bool,
) -> None:
    """Update biolovision database.

    CONFIG: configuration filename

    INPUT_FILE: CSV file listing modifications to be applied
    """
    # Create $HOME/tmp directory if it does not exist
    (Path.home() / "tmp").mkdir(exist_ok=True)

    # Define logger format and handlers
    # create file handler which logs even debug messages
    fh = TimedRotatingFileHandler(
        str(Path.home()) + "/tmp/" + __name__ + ".log",
        when="midnight",
        interval=1,
        backupCount=100,
    )
    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    # Create formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # Add the handlers to the logger
    logger.addHandler(fh)
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
    "config",
)
def init(config: str):
    """Copy template TOML file to home directory."""
    toml_dst = Path.home() / config
    if toml_dst.is_file():
        logger.warning(_("toml configuration file %s exists and is not overwritten"), toml_dst)
    else:
        logger.info(_("Creating toml configuration file"))
        ref = importlib.resources.files(__name__.split(".")[0]) / "data/evn_template.toml"
        with importlib.resources.as_file(ref) as toml_src:
            logger.info(_("Creating toml configuration file %s, from %s"), toml_dst, toml_src)
            shutil.copyfile(toml_src, toml_dst)
            logger.info(_("Please edit %s before running the script"), toml_dst)


@main.command()
@click.argument(
    "config",
)
@click.argument(
    "input_file",
)
def update(config: str, input_file: str) -> None:
    """Update Biolovision database."""
    logger = logging.getLogger(__name__ + ".update")
    # Get configuration from file
    if not (Path.home() / config).is_file():
        logger.critical(_("Configuration file %s does not exist"), str(Path.home() / config))
        raise FileNotFoundError
    logger.info(_("Getting configuration data from %s"), config)
    ref = str(importlib.resources.files(__name__.split(".")[0]) / "data/evn_default.toml")
    settings = Dynaconf(
        settings_files=[ref, config],
    )

    # Validation de tous les paramètres
    cfg_site_list = settings.sites
    if len(cfg_site_list) > 1:
        raise ValueError(_("Only one site can be defined in configuration file"))
    for site, cfg in cfg_site_list.items():  # noqa: B007
        break
    site_up = site.upper()
    settings.validators.register(
        Validator("MESSAGE", len_min=5),
        Validator(f"SITES.{site_up}.SITE", len_min=10, startswith="https://"),
        Validator("SITES.{site_up}.USER_EMAIL", len_min=5, cont="@"),
        Validator("SITES.{site_up}.USER_PW", len_min=5),
        Validator("SITES.{site_up}.CLIENT_KEY", len_min=20),
        Validator("SITES.{site_up}.CLIENT_SECRET", len_min=5),
        Validator("TUNING.MAX_LIST_LENGTH", gte=1),
        Validator("TUNING.MAX_CHUNKS", gte=1),
        Validator("TUNING.MAX_RETRY", gte=1),
        Validator("TUNING.MAX_REQUESTS", gte=0),
        Validator("TUNING.RETRY_DELAY", gte=1),
        Validator("TUNING.UNAVAILABLE_DELAY", gte=1),
    )
    try:
        settings.validators.validate_all()
    except ValidationError as e:
        accumulative_errors = e.details
        logger.exception(accumulative_errors)
        raise


def run():
    """Entry point for console_scripts"""
    main(sys.argv[1:])


# Main wrapper
if __name__ == "__main__":
    run()
