#!/usr/bin/env python3
"""
Sample application: skeleton for new applications

"""
import argparse
import logging
import shutil
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import sys

import pkg_resources
from export_vn.evnconf import EvnConf
from strictyaml import YAMLValidationError

from . import _, __version__

APP_NAME = "sample_app"

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
    parser.add_argument("file", help=_("Configuration file name"))

    return parser.parse_args(args)


def init(file: str):
    """Copy template YAML file to home directory."""
    logger = logging.getLogger(APP_NAME + "init")
    yaml_src = pkg_resources.resource_filename(__name__, "data/evn_template.yaml")
    yaml_dst = str(Path.home() / file)
    logger.info(_("Creating YAML configuration file %s, from %s"), yaml_dst, yaml_src)
    shutil.copyfile(yaml_src, yaml_dst)
    logger.info(_("Please edit %s before running the script"), yaml_dst)


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    # Create $HOME/tmp directory if it does not exist
    (Path.home() / "tmp").mkdir(exist_ok=True)

    # Define logger format and handlers
    logger = logging.getLogger(APP_NAME + "main")
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
        init(args.file)
        return None

    # Get configuration from file
    if not (Path.home() / args.file).is_file():
        logger.critical(_("File %s does not exist"), str(Path.home() / args.file))
        return None

    return None


def run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


# Main wrapper
if __name__ == "__main__":
    run()
