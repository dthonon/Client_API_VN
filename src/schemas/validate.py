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
        "--report",
        help=_("Report of the properties in the schemas"),
        action="store_true",
    )
    parser.add_argument(
        "--restore",
        help=_("Rename processed files back to their original name"),
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


def validate_schema(cfg_site_list: Any, samples: float) -> None:
    """Validate schemas against downloaded files.
    Files are renamed *.done after successful processing."""
    # Iterate over schema list
    js_list = [
        f
        for f in pkg_resources.resource_listdir(__name__, "")
        if re.match(r".*\.json", f)
    ]
    for js_f in js_list:
        schema = js_f.split(".")[0]
        file = pkg_resources.resource_filename(__name__, js_f)
        logger.info(_("Validating schema %s, in file %s"), schema, file)
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


def restore(cfg_site_list: Any) -> None:
    """Restore file names."""
    # Iterate over schema list
    js_list = [
        f
        for f in pkg_resources.resource_listdir(__name__, "")
        if re.match(r".*\.json", f)
    ]
    for js_f in js_list:
        schema = js_f.split(".")[0]
        logger.info(_("Restoring files for schema %s"), schema)
        # Gathering files to rename
        f_list = list()
        for site, cfg in cfg_site_list.items():
            p = Path.home() / cfg.file_store
            for tst_f in p.glob(f"{schema}*.gz.done"):
                f_list.append(tst_f)
        for fj in f_list:
            fjr = str(fj)[:-5]
            logger.debug(_("Renaming %s to %s"), fj, fjr)
            shutil.move(fj, fjr)

    return None


def report(cfg_site_list: Any) -> None:
    """Print of list of properties in the schemas."""
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
        logger.info(_("Validating schema %s, in file %s"), schema, file)
        with open(file) as f:
            schema_js = json.load(f)
        for defs in schema_js["definitions"]:
            if "properties" in schema_js["definitions"][defs]:
                for key, props in schema_js["definitions"][defs]["properties"].items():
                    if "title" in props:
                        pp.pprint(props)


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

    # Schema validation
    if args.validate:
        logger.info(_("Validating schemas"))
        samples = _get_int_or_float(args.samples)
        if isinstance(samples, float) and (samples < 0 or samples > 1):
            logger.error(
                _(
                    "--samples float parameter: %s "
                    "must be between 0.0 and 1.0. Coerced to 0.1"
                ),
                samples,
            )
            samples = 0.1
        if isinstance(samples, int) and (samples < 0):
            logger.error(
                _("--samples int parameter: %s " "must be positive. Coerced to 0.1"),
                samples,
            )
            samples = 0.1
        validate_schema(cfg_site_list, samples)
        return None

    # Restoring file names
    if args.restore:
        logger.info(_("Restoring file names"))
        restore(cfg_site_list)

    # Schema reporting
    if args.report:
        logger.info(_("Reporting on schemas"))
        report(cfg_site_list)

    return None


def run():
    """Entry point for console_scripts"""
    main(sys.argv[1:])


# Main wrapper
if __name__ == "__main__":
    run()
