#!/usr/bin/env python3
"""
Validate schema and downloaded JSON files.
Generate property reports from schema.

"""
import argparse
import gzip
import json
import logging
import pprint
import random
import re
import shutil
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any

import pkg_resources
from jsonschema import ValidationError, validate
from jsonschema.validators import validator_for
from strictyaml import YAMLValidationError

from export_vn.evnconf import EvnConf

from . import _, __version__

logger = logging.getLogger(__name__)


def arguments(args):
    """Define and parse command arguments.

    Args:
        args ([str]): command line parameters as list of strings

    Returns:
        :obj:`argparse.Namespace`: command line parameters namespace
    """
    # Get options
    parser = argparse.ArgumentParser(
        description="JSON schemas validation and reporting."
    )
    parser.add_argument(
        "--version",
        help=_("Print version number"),
        action="version",
        version="%(prog)s {version}".format(version=__version__),
    )
    out_group = parser.add_mutually_exclusive_group()
    out_group.add_argument(
        "--verbose", help=_("Increase output verbosity"), action="store_true"
    )
    out_group.add_argument(
        "--quiet", help=_("Reduce output verbosity"), action="store_true"
    )
    parser.add_argument(
        "--validate",
        help=_("Validate the schemas against downloaded JSON files"),
        action="store_true",
    )
    parser.add_argument(
        "--samples",
        help=_(
            (
                "If float in range [0.0, 1.0], the parameter represents a "
                "proportion of files, else integer absolute counts."
            )
        ),
        default="0.1",
    )
    parser.add_argument("config", help=_("Configuration file name"))

    return parser.parse_args(args)


def _get_int_or_float(v):
    """Convert str to int or float."""
    number_as_float = float(v)
    number_as_int = int(number_as_float)
    return number_as_int if number_as_float == number_as_int else number_as_float


def validate(cfg_site_list: Any, samples: float) -> None:
    """Validate schemas against downloaded files."""
    pp = pprint.PrettyPrinter(indent=2)
    # Iterate over schema list
    js_list = [
        f
        for f in pkg_resources.resource_listdir(__name__, "")
        if re.match(r".*\.json", f)
    ]
    for js_f in js_list:
        schema = js_f.split(".")[0]
        file = pkg_resources.resource_filename(__name__, js_f)
        logger.info(_(f"Validating schema {schema}, in file {file}"))
        with open(file) as f:
            schema_js = json.load(f)
        cls = validator_for(schema_js)
        cls.check_schema(schema_js)
        instance = cls(schema_js)
        # Gathering files to validate
        f_list = list()
        for site, cfg in cfg_site_list.items():
            p = Path.home() / cfg.file_store
            for tst_f in p.glob(f"{schema}*.gz"):
                f_list.append(tst_f)
        if isinstance(samples, float):
            samples = round(samples * len(f_list))
        samples = min(samples, len(f_list))
        logger.debug(_(f"Sampling {samples} out of {len(f_list)} files"))
        f_list = random.sample(f_list, samples)
        for fj in f_list:
            logger.debug(_(f"Validating {schema} schema with {fj}"))
            with gzip.open(fj) as f:
                js = json.load(f)
            instance.validate(js)


    return None


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
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
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    # Get command line arguments
    args = arguments(args)

    # Define verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.WARNING)
    else:
        logger.setLevel(logging.INFO)

    logger.info(_("%s, version %s"), sys.argv[0], __version__)
    logger.info(_("Arguments: %s"), sys.argv[1:])

    # Get configuration from file
    if not (Path.home() / args.config).is_file():
        logger.critical(_("File %s does not exist"), str(Path.home() / args.config))
        return None
    logger.info(_("Getting configuration data from %s"), args.config)
    try:
        cfg_ctrl = EvnConf(args.config)
    except YAMLValidationError:
        logger.critical(_("Incorrect content in YAML configuration %s"), args.config)
        sys.exit(0)
    cfg_site_list = cfg_ctrl.site_list

    # If required, first create YAML file
    if args.validate:
        logger.info(_("Validating schemas"))
        samples = _get_int_or_float(args.samples)
        if isinstance(samples, float) and (samples < 0 or samples > 1):
            logger.error(
                _(
                    f"--samples float parameter: {samples} "
                    f"must be between 0.0 and 1.0. Coerced to 0.1"
                )
            )
            samples = 0.1
        if isinstance(samples, int) and (samples < 0):
            logger.error(
                _(
                    f"--samples int parameter: {samples} "
                    f"must be positive. Coerced to 0.1"
                )
            )
            samples = 0.1
        validate(cfg_site_list, samples)
        return None

    # Get configuration from file
    if not (Path.home() / args.config).is_file():
        logger.critical(
            _("Configuration file %s does not exist"), str(Path.home() / args.config)
        )
        return None
    logger.info(_("Getting configuration data from %s"), args.config)
    try:
        cfg_ctrl = EvnConf(args.config)
    except YAMLValidationError:
        logger.critical(_("Incorrect content in YAML configuration %s"), args.config)
        sys.exit(0)
    cfg_site_list = cfg_ctrl.site_list

    return None


def run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


# Main wrapper
if __name__ == "__main__":
    run()
