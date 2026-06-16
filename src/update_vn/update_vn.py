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
import json
import logging
import pprint
import shutil
import sys
from ast import literal_eval
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import click
import pandas as pd
from dynaconf import Dynaconf, ValidationError, Validator

from biolovision.api import ObservationsAPI

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

    # # Define logger format and handlers
    # logger = logging.getLogger(APP_NAME)
    # create file handler which logs even debug messages
    fh = TimedRotatingFileHandler(
        str(Path.home()) + "/tmp/" + __name__.split(".")[0] + ".log",
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
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, handlers=[fh, ch])

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
    # Get configuration from file
    if not (Path.home() / config).is_file():
        logger.critical(_("Configuration file %s does not exist"), str(Path.home() / config))
        raise FileNotFoundError
    logger.info(_("Getting configuration data from %s"), config)
    settings = Dynaconf(
        settings_files=[config],
    )

    # Validation de tous les paramètres
    cfg_site_list = settings.sites
    if not cfg_site_list:
        raise ValueError(_("No site defined in configuration file"))
    if len(cfg_site_list) > 1:
        raise ValueError(_("Only one site can be defined in configuration file"))
    # Get the single site key
    site = None
    cfg = None
    for site, cfg in cfg_site_list.items():  # noqa: B007
        break
    site_up = site.upper()  # pyright: ignore[reportOptionalMemberAccess]
    settings.validators.register(
        Validator(
            "MESSAGE",
            len_min=5,
            default="Modification en masse, le {date}, opération {op}, attribut {path}, depuis {old} vers {new}",
        ),
        Validator(f"SITES.{site_up}.URL", len_min=10, startswith="https://"),
        Validator("SITES.{site_up}.USER_EMAIL", len_min=5, cont="@"),
        Validator("SITES.{site_up}.USER_PW", len_min=5),
        Validator("SITES.{site_up}.CLIENT_KEY", len_min=20),
        Validator("SITES.{site_up}.CLIENT_SECRET", len_min=5),
        Validator("TUNING.MAX_LIST_LENGTH", gte=1, default=100),
        Validator("TUNING.MAX_CHUNKS", gte=1, default=1000),
        Validator("TUNING.MAX_RETRY", gte=1, default=5),
        Validator("TUNING.MAX_REQUESTS", gte=0, default=0),
        Validator("TUNING.RETRY_DELAY", gte=1, default=5),
        Validator("TUNING.UNAVAILABLE_DELAY", gte=1, default=600),
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

    print(cfg)
    obs_api = {}
    logger.debug(_("Preparing update for site %s"), site)
    obs_api[site] = ObservationsAPI(
        user_email=cfg.user_email,  # pyright: ignore[reportOptionalMemberAccess]
        user_pw=cfg.user_pw,  # pyright: ignore[reportOptionalMemberAccess]
        base_url=cfg.URL,  # pyright: ignore[reportOptionalMemberAccess]
        client_key=cfg.client_key,  # pyright: ignore[reportOptionalMemberAccess]
        client_secret=cfg.client_secret,  # pyright: ignore[reportOptionalMemberAccess]
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
            if nb_row == 0:
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
                        except ValueError:
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


@main.command()
@click.argument(
    "config",
)
@click.argument(
    "forms_file",
)
@click.argument(
    "data_file",
)
def upload_forms(config: str, forms_file: str, data_file: str) -> None:
    """Upload forms to Biolovision database."""
    # Get configuration from file
    if not (Path.home() / config).is_file():
        logger.critical(_("Configuration file %s does not exist"), str(Path.home() / config))
        raise FileNotFoundError
    logger.info(_("Getting configuration data from %s"), config)
    settings = Dynaconf(
        settings_files=[config],
    )

    # Validation de tous les paramètres
    cfg_site_list = settings.sites
    if len(cfg_site_list) > 1:
        raise ValueError(_("Only one site can be defined in configuration file"))
    site = None
    cfg = None
    for site, cfg in cfg_site_list.items():  # noqa: B007
        break
    site_up = site.upper()  # pyright: ignore[reportOptionalMemberAccess]
    settings.validators.register(
        Validator(
            "MESSAGE",
            len_min=5,
            default="Modification en masse, le {date}, opération {op}, attribut {path}, depuis {old} vers {new}",
        ),
        Validator(f"SITES.{site_up}.URL", len_min=10, startswith="https://"),
        Validator("SITES.{site_up}.USER_EMAIL", len_min=5, cont="@"),
        Validator("SITES.{site_up}.USER_PW", len_min=5),
        Validator("SITES.{site_up}.CLIENT_KEY", len_min=20),
        Validator("SITES.{site_up}.CLIENT_SECRET", len_min=5),
        Validator("TUNING.MAX_LIST_LENGTH", gte=1, default=100),
        Validator("TUNING.MAX_CHUNKS", gte=1, default=1000),
        Validator("TUNING.MAX_RETRY", gte=1, default=5),
        Validator("TUNING.MAX_REQUESTS", gte=0, default=0),
        Validator("TUNING.RETRY_DELAY", gte=1, default=5),
        Validator("TUNING.UNAVAILABLE_DELAY", gte=1, default=600),
    )
    try:
        settings.validators.validate_all()
    except ValidationError as e:
        accumulative_errors = e.details
        logger.exception(accumulative_errors)
        raise

    # Check forms and data file
    if not Path(forms_file).is_file():
        logger.critical(_("Forms file %s does not exist"), str(Path(forms_file)))
        raise FileNotFoundError
    if not Path(data_file).is_file():
        logger.critical(_("Data file %s does not exist"), str(Path(data_file)))
        raise FileNotFoundError

    # Read forms and data file
    with open(forms_file, newline="") as csvfile:
        forms_reader = csv.reader(csvfile, delimiter=",")
        forms = pd.DataFrame([row for row in forms_reader if len(row) >= 2])
    forms.columns = forms.iloc[0]
    forms = forms[1:]
    forms.set_index("id", inplace=True)
    with open(data_file, newline="") as csvfile:
        data_reader = csv.reader(csvfile, delimiter=",")
        data = pd.DataFrame([row for row in data_reader if len(row) >= 2])
    data.columns = data.iloc[0]
    data = data[1:]
    data.set_index("id", inplace=True)

    jform = None
    for _form_id, form in forms.iterrows():
        form_id = form["id_form_universal"]
        jform = json.loads(f"{form['item']}")
        jform = {"data": {"forms": [jform]}}
        # print(pprint.pformat(jform))
        # jform["data"]["forms"][0].pop("@id", None)
        # jform["data"]["forms"][0].pop("@uid", None)
        # jform["data"]["forms"][0].pop("id_form_universal", None)
        # jform["data"]["forms"][0].pop("coord_x_local", None)
        # jform["data"]["forms"][0].pop("coord_y_local", None)
        # jform["data"]["forms"][0].pop("place_type", None)
        # jform["data"]["forms"][0].pop("id_form", None)
        # jform["data"]["forms"][0].pop("date_start", None)
        # jform["data"]["forms"][0].pop("date_stop", None)
        # jform["data"]["forms"][0].pop("version", None)
        # jform["data"]["forms"][0].pop("protocol", None)
        jform["data"]["forms"][0]["sightings"] = []
        for _data_id, dat in data.iterrows():
            if dat["id_form_universal"] == form_id:
                jdat = json.loads(str(dat["item"]))
                # for observer in range(len(jdat["observers"])):
                #     jdat["date"].pop("@offset", None)
                #     jdat["observers"][observer].pop("@uid", None)
                #     jdat["observers"][observer].pop("id_form_universal", None)
                #     jdat["observers"][observer].pop("coord_x_local", None)
                #     jdat["observers"][observer].pop("coord_y_local", None)
                #     jdat["observers"][observer].pop("id_form", None)
                #     jdat["observers"][observer].pop("id_sighting", None)
                #     jdat["observers"][observer].pop("id_universal", None)
                #     jdat["observers"][observer].pop("insert_date", None)
                #     jdat["observers"][observer].pop("update_date", None)
                #     jdat["observers"][observer].pop("uuid", None)
                #     jdat["observers"][observer].pop("source", None)
                #     jdat["observers"][observer].pop("version", None)
                #     jdat["observers"][observer]["timing"].pop("@offset", None)
                #     jdat["observers"][observer].pop("traid", None)
                # jdat["place"].pop("id_universal", None)
                # jdat["place"].pop("loc_precision", None)
                # jdat["place"].pop("lat", None)
                # jdat["place"].pop("lon", None)
                # jdat["place"].pop("name", None)
                # jdat["place"].pop("place_type", None)
                # jdat["species"].pop("category", None)
                # jdat["species"].pop("rarity", None)
                # jdat["species"].pop("taxonomy", None)
                jform["data"]["forms"][0]["sightings"].append(jdat)
        break
    print(pprint.pformat(jform))

    obs_api = ObservationsAPI(
        user_email=cfg.user_email,  # pyright: ignore[reportOptionalMemberAccess]
        user_pw=cfg.user_pw,  # pyright: ignore[reportOptionalMemberAccess]
        base_url=cfg.URL,  # pyright: ignore[reportOptionalMemberAccess]
        client_key=cfg.client_key,  # pyright: ignore[reportOptionalMemberAccess]
        client_secret=cfg.client_secret,  # pyright: ignore[reportOptionalMemberAccess]
        max_retry=settings.tuning.max_retry,
        max_requests=settings.tuning.max_requests,
        max_chunks=settings.tuning.max_chunks,
        unavailable_delay=settings.tuning.unavailable_delay,
        retry_delay=settings.tuning.retry_delay,
    )
    formc = obs_api.api_create(jform)  # pyright: ignore[reportOptionalMemberAccess]
    print(formc)
    return None


def run() -> None:
    """Entry point for console_scripts"""
    main(sys.argv[1:])
    return None


# Main wrapper
if __name__ == "__main__":
    run()
