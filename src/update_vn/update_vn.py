#!/usr/bin/env python3
"""
Update sightings attributes in Biolovision database.

Application that reads a CSV file and updates the observations in Biolovision database.
CSV file must contain:

- site, as defined in toml site section
- id_universal of the sighting to modify
- path to the attribute to modify, in JSONPath syntax
- operation: update or replace
- value: new value inserted or updated

Modification are tracked in hidden_comment.

"""

import contextlib
import csv
import datetime
import importlib.resources
import logging
import shutil
import sys
from ast import literal_eval
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import click
from dynaconf import Dynaconf, ValidationError, Validator

from biolovision.api import ObservationsAPI

from . import __version__

APP_NAME = "update_vn"

logger = logging.getLogger(APP_NAME)


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
    logger = logging.getLogger(APP_NAME)
    # create file handler which logs even debug messages
    fh = TimedRotatingFileHandler(
        str(Path.home()) + "/tmp/" + APP_NAME + ".log",
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
    logger = logging.getLogger(APP_NAME + ".init")
    toml_dst = Path.home() / config
    if toml_dst.is_file():
        logger.warning(_("toml configuration file %s exists and is not overwritten"), toml_dst)
    else:
        logger.info(_("Creating toml configuration file"))
        ref = importlib.resources.files("update_vn") / "data/evn_template.toml"
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
    logger = logging.getLogger(APP_NAME + ".update")
    # Get configuration from file
    if not (Path.home() / config).is_file():
        logger.critical(_("Configuration file %s does not exist"), str(Path.home() / config))
        raise FileNotFoundError
    logger.info(_("Getting configuration data from %s"), config)
    ref = str(importlib.resources.files("update_vn") / "data/evn_default.toml")
    settings = Dynaconf(
        preload=[ref],
        settings_files=[config],
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

    # Update Biolovision site from update file
    if not Path(input_file).is_file():
        logger.critical(_("Input file %s does not exist"), str(Path(input_file)))
        raise FileNotFoundError

    obs_api = {}
    logger.debug(_("Preparing update for site %s"), site)
    obs_api[site] = ObservationsAPI(
        user_email=cfg.user_email,
        user_pw=cfg.user_pw,
        base_url=cfg.site,
        client_key=cfg.client_key,
        client_secret=cfg.client_secret,
        max_retry=settings.tuning.max_retry,
        max_requests=settings.tuning.max_requests,
        max_chunks=settings.tuning.max_chunks,
        unavailable_delay=settings.tuning.unavailable_delay,
        retry_delay=settings.tuning.retry_delay,
    )

    with open(input_file, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=";")
        nb_row = 0
        for nb_row, row in enumerate(reader):
            logger.debug(row)
            if nb_row == 1:
                # First row must be header
                if row[0].strip() != "site":
                    logger.critical(_("Column header 1 must be 'site'"))
                    raise ValueError
                if row[1].strip() != "id_universal":
                    logger.critical(_("Column header 2 must be 'id_universal'"))
                    raise ValueError
                if row[2].strip() != "path":
                    logger.critical(_("Column header 3 must be 'path'"))
                    raise ValueError
                if row[3].strip() != "operation":
                    logger.critical(_("Column header 4 must be 'operation'"))
                    raise ValueError
                if row[4].strip() != "value":
                    logger.critical(_("Column header 5 must be 'value'"))
                    raise ValueError
            else:
                # Next rows are update commands
                if len(row) < 5:
                    logger.warning("Empty line ignored")
                else:
                    logger.info(
                        _("Site %s: updating sighting %s, operation %s"),
                        row[0].strip(),
                        row[1].strip(),
                        row[3].strip(),
                    )
                    if row[0].strip() != site:
                        logger.error(_("Unknown site in row %d, ignored %s"), nb_row, row[0])
                    elif row[3].strip() not in [
                        "delete_observation",
                        "delete_attribute",
                        "replace",
                    ]:
                        logger.error(_("Unknown operation in row %d, ignored %s"), nb_row, row)
                    elif row[3].strip() == "delete_observation":
                        obs_api[row[0].strip()].api_delete(row[1].strip())
                    else:
                        # Get current observation
                        sighting = obs_api[row[0].strip()].api_get(row[1].strip(), short_version="1")
                        if "forms" in sighting["data"]:
                            # Received a form, changing to single sighting
                            sighting["data"] = sighting["data"]["forms"][0]
                        logger.debug(
                            _("Before: %s"),
                            sighting["data"],
                        )
                        # JSON path relative to "sighting"
                        repl = row[2].strip().replace("$", "sighting")
                        # Get current value, if exists
                        try:
                            old_attr = literal_eval(repl)
                        except KeyError:
                            old_attr = None
                        # Get current hidden_comment, if exists
                        try:
                            msg = (
                                sighting["data"]["sightings"][0]["observers"][0]["hidden_comment"]
                                .replace("\n", "")
                                .replace("\r", "")
                            )
                        except KeyError:  # pragma: no cover
                            msg = ""
                        # Prepare logging message to be appended to hidden_comment
                        msg = (
                            msg
                            + " / "
                            + settings.message.format(
                                date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                op=row[3].strip(),
                                path=row[2].strip(),
                                old=old_attr,
                                new=row[4].strip(),
                            )
                        )
                        if row[3].strip() == "replace":
                            exec("{} = {}".format(repl, "row[4].strip()"))
                        else:  # delete_attribute
                            with contextlib.suppress(KeyError):
                                exec(f"del {repl}")

                        exec(
                            """sighting['data']['sightings'][0]['observers'][0]['hidden_comment'] = '{}'""".format(
                                msg.replace('"', '\\"').replace("'", "\\'")
                            )
                        )
                        logger.debug(_("After: %s"), sighting["data"])
                        # Update to remote site
                        obs_api[row[0].strip()].api_update(row[1].strip(), sighting)

    return None


def run() -> None:
    """Entry point for console_scripts"""
    main(sys.argv[1:])
    return None


# Main wrapper
if __name__ == "__main__":
    run()
