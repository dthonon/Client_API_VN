#!/usr/bin/env python3
"""
Validate schema and downloaded JSON files.
Generate property reports from schema.

"""

# import argparse
import gzip
import importlib.resources
import json
import logging
import random
import shutil
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import click
from dynaconf import Dynaconf, ValidationError, Validator
from jsonschema.validators import validator_for

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

    INPUT: CSV file listing modifications to be applied
    """
    # Create $HOME/tmp directory if it does not exist
    (Path.home() / "tmp").mkdir(exist_ok=True)

    # create file handler which logs even debug messages
    fh = TimedRotatingFileHandler(
        str(Path.home()) + "/tmp/" + __name__ + ".log",
        when="midnight",
        interval=1,
        backupCount=100,
    )
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    # Define verbosity
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.info(_("%s, version %s"), sys.argv[0], __version__)

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


def _get_int_or_float(v):
    """Convert str to int or float."""
    number_as_float = float(v)
    number_as_int = int(number_as_float)
    return number_as_int if number_as_float == number_as_int else number_as_float


@main.command()
@click.option(
    "--samples",
    default="0.1",
    help=_(
        "If float in range [0.0, 1.0], the parameter represents a proportion of files, else integer absolute counts."
    ),
)
@click.argument(
    "config",
)
def validate(config: str, samples: float) -> None:
    """Validate schemas against downloaded files.
    Files are renamed *.done after successful processing."""
    # Get configuration from file
    if not (Path.home() / config).is_file():
        logger.critical(_("Configuration file %s does not exist"), str(Path.home() / config))
        raise FileNotFoundError
    logger.info(_("Getting configuration data from %s"), config)
    settings = Dynaconf(
        settings_files=[config],
    )

    # Validation de tous les paramètres
    settings.validators.register(
        Validator("FILE.FILE_STORE", len_min=1),
    )
    try:
        settings.validators.validate_all()
    except ValidationError as e:
        accumulative_errors = e.details
        logger.exception(accumulative_errors)
        raise

    val_path = Path.home() / settings.file.file_store
    logger.info(_("Validating schemas with %s"), val_path)
    samples = _get_int_or_float(samples)
    if isinstance(samples, float) and (samples < 0 or samples > 1):
        logger.error(
            _("--samples float parameter: %s must be between 0.0 and 1.0. Coerced to 0.1"),
            samples,
        )
        samples = 0.1
    if isinstance(samples, int) and (samples < 0):
        logger.error(
            _("--samples int parameter: %s must be positive. Coerced to 0.1"),
            samples,
        )
        samples = 0.1

    for js_f in importlib.resources.files("schemas").iterdir():
        with importlib.resources.as_file(js_f) as file:
            if js_f.suffix == ".json":
                schema = js_f.stem
                logger.info(_("Validating schema %s, in file %s"), schema, file)
                with open(file) as f:
                    schema_js = json.load(f)
                cls = validator_for(schema_js)
                cls.check_schema(schema_js)
                instance = cls(schema_js)
                # Gathering files to validate
                f_list = []
                p = Path.home() / settings.file.file_store
                for tst_f in p.glob(f"*/{schema}*.gz"):
                    f_list.append(tst_f)
                sample_schema = samples
                if isinstance(sample_schema, float):
                    sample_schema = round(sample_schema * len(f_list))
                sample_schema = min(sample_schema, len(f_list))
                logger.debug(_("Sampling %s out of %i files"), sample_schema, len(f_list))
                f_list = random.sample(f_list, sample_schema)
                for fj in f_list:
                    logger.debug(_("Validating %s schema with %s"), schema, fj)
                    with gzip.open(fj) as f:
                        js = json.load(f)
                    instance.validate(js)
                    shutil.move(fj, str(fj) + ".done")

    return None


@main.command()
@click.argument(
    "config",
)
def restore(config: str) -> None:
    """Restore file names."""
    # Get configuration from file
    if not (Path.home() / config).is_file():
        logger.critical(_("Configuration file %s does not exist"), str(Path.home() / config))
        raise FileNotFoundError
    logger.info(_("Getting configuration data from %s"), config)
    settings = Dynaconf(
        settings_files=[config],
    )

    # Validation de tous les paramètres
    settings.validators.register(
        Validator("FILE.FILE_STORE", len_min=1),
    )
    try:
        settings.validators.validate_all()
    except ValidationError as e:
        accumulative_errors = e.details
        logger.exception(accumulative_errors)
        raise

    # Iterate over schema list
    for js_f in importlib.resources.files("schemas").iterdir():
        if js_f.suffix == ".json":
            schema = js_f.stem
            logger.info(_("Restoring files for schema %s"), schema)
            # Gathering files to rename
            f_list = []
            p = Path.home() / settings.file.file_store
            for tst_f in p.glob(f"*/{schema}*.gz.done"):
                f_list.append(tst_f)
            for fj in f_list:
                fjr = str(fj)[:-5]
                logger.debug(_("Renaming %s to %s"), fj, fjr)
                shutil.move(fj, fjr)

    return None


# def report(cfg_site_list: Any) -> None:
#     """Print of list of properties in the schemas."""
#     pp = pprint.PrettyPrinter(indent=2)
#     # Iterate over schema list
#     for js_f in importlib.resources.files("schemas").iterdir():
#         with importlib.resources.as_file(js_f) as file:
#             if js_f.suffix == ".json":
#                 schema = js_f.stem
#                 logger.info(_("Validating schema %s, in file %s"), schema, file)
#                 with open(file) as f:
#                     schema_js = json.load(f)
#                 for defs in schema_js["definitions"]:
#                     if "properties" in schema_js["definitions"][defs]:
#                         for key, props in schema_js["definitions"][defs][
#                             "properties"
#                         ].items():
#                             if "title" in props:
#                                 pp.pprint(props)


def run():
    """Entry point for console_scripts"""
    main(sys.argv[1:])


# Main wrapper
if __name__ == "__main__":
    run()
