#!/usr/bin/env python3
"""
Update sightings attributes in Biolovision database.

Application that reads a CSV file and updates the observations in Biolovision database.
CSV file must contain:

- id_universal of the sighting to modify
- path to the attribute to modify, in JSONPath syntax
- value: new value inserted or updated

Modification are tracked in hidden_comment.

"""
import argparse
import csv
import logging
import shutil
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import pkg_resources
from strictyaml import YAMLValidationError

from biolovision.api import ObservationsAPI
from export_vn.evnconf import EvnConf

from . import _, __version__

APP_NAME = "update_vn"

logger = logging.getLogger(APP_NAME)


def arguments(args):
    """Define and parse command arguments.

    Args:
        args ([str]): command line parameters as list of strings

    Returns:
        :obj:`argparse.Namespace`: command line parameters namespace
    """
    # Get options
    parser = argparse.ArgumentParser(
        description="Sample Biolovision API client application."
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
        "--init", help=_("Initialize the YAML configuration file"), action="store_true"
    )
    parser.add_argument("config", help=_("Configuration file name"))
    parser.add_argument("input", help=_("Update list file name, in CSV format"))

    return parser.parse_args(args)


def init(config: str):
    """Copy template YAML file to home directory."""
    logger = logging.getLogger(APP_NAME + ".init")
    yaml_src = pkg_resources.resource_filename(__name__, "data/evn_template.yaml")
    yaml_dst = str(Path.home() / config)
    logger.info(_("Creating YAML configuration file %s, from %s"), yaml_dst, yaml_src)
    shutil.copyfile(yaml_src, yaml_dst)
    logger.info(_("Please edit %s before running the script"), yaml_dst)


def update(cfg_ctrl, input: str):
    """Update Biolovision database."""
    logger = logging.getLogger(APP_NAME + ".update")
    cfg_crtl_list = cfg_ctrl.ctrl_list
    cfg_site_list = cfg_ctrl.site_list

    obs_api = dict()
    for site, cfg in cfg_site_list.items():
        if cfg.enabled:
            logger.info(_("Preparing update for site %s"), site)
            obs_api[site] = ObservationsAPI(cfg)

    with open(input, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=";")
        nb_row = 0
        for row in reader:
            nb_row += 1
            logger.debug(row)
            if nb_row == 1:
                assert row[0] == "site"
                assert row[1] == "id_universal"
                assert row[2] == "path"
                assert row[3] == "operation"
                assert row[4] == "value"
            else:
                logger.info(
                    _("Site %s: updating sighting %s, operation %s"),
                    row[0],
                    row[1],
                    row[3],
                )
                sighting = obs_api[row[0]].api_get(row[1], short_version="1")
                logger.debug(sighting)
                repl = row[2].replace("$", "sighting")
                old_attr = eval(repl)
                logger.debug(_("Replacing %s by %s"), old_attr, row[4])


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
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
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
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
    else:
        logger.setLevel(logging.INFO)

    logger.info(_("%s, version %s"), sys.argv[0], __version__)
    logger.info(_("Arguments: %s"), sys.argv[1:])

    # If required, first create YAML file
    if args.init:
        logger.info(_("Creating YAML configuration file"))
        init(args.config)
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
    except YAMLValidationError as error:
        logger.critical(_("Incorrect content in YAML configuration %s"), args.config)
        sys.exit(0)

    # Update Biolovision site from update file
    if not Path(args.input).is_file():
        logger.critical(_("Input file %s does not exist"), str(Path(args.input)))
        return None
    update(cfg_ctrl, args.input)

    return None


def run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


# Main wrapper
if __name__ == "__main__":
    run()
