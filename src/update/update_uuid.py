#!/usr/bin/env python3
"""
Update sightings attributes in Biolovision database.

Application that reads a TSV file and updates the observations in Biolovision database.
TSV file must contain:

    source: le site source de la donnée
    id_local: l'id local dans le site source
    uuid: le nouvel UUID à attribuer aux données en remplacement de l'UUID FF actuel.
    id_universal: l'id_universal visionature de la donnée

Modification are tracked in hidden_comment.

"""
import argparse
import csv
import datetime
import json
import logging
import shutil
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import numpy as np
import pkg_resources
from strictyaml import YAMLValidationError

from biolovision.api import ObservationsAPI, HTTPError
from export_vn.evnconf import EvnConf

from . import _, __version__

APP_NAME = "update_uuid"

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
    parser.add_argument(
        "input", help=_("To be updated sightings file name, in TSV format")
    )
    parser.add_argument("output", help=_("Updated sightings file name, in TSV format"))
    parser.add_argument(
        "--chunk",
        type=int,
        help=_("Number of input file to read in each chunk"),
        default="100",
    )
    parser.add_argument(
        "--max_done",
        type=int,
        help=_("Total, across all script runs, of sightings to process"),
        default="1000",
    )
    return parser.parse_args(args)


def init(config: str):
    """Copy template YAML file to home directory."""
    logger = logging.getLogger(APP_NAME + ".init")
    yaml_src = pkg_resources.resource_filename("export_vn", "data/evn_template.yaml")
    yaml_dst = str(Path.home() / config)
    logger.info(_("Creating YAML configuration file %s, from %s"), yaml_dst, yaml_src)
    shutil.copyfile(yaml_src, yaml_dst)
    logger.info(_("Please edit %s before running the script"), yaml_dst)


def _count_generator(reader):
    b = reader(1024 * 1024)
    while b:
        yield b
        b = reader(1024 * 1024)


def update(cfg_ctrl, input: str, output: str, max_done: int, chunk: int):
    """Update Biolovision database."""
    logger = logging.getLogger(APP_NAME + ".update")
    cfg_site_list = cfg_ctrl.site_list

    obs_api = dict()
    update_site = None
    for site, cfg in cfg_site_list.items():
        # There should be only 1 site in params file
        update_site = site
        obs_api[site] = ObservationsAPI(cfg)

    logger.info(
        _("Preparing update for site %s, max_done = %d, chunk = %d"),
        update_site,
        max_done,
        chunk,
    )

    done = 0
    with open(output, "rb") as fp:
        c_generator = _count_generator(fp.raw.read)
        # count each \n
        done = sum(buffer.count(b"\n") for buffer in c_generator) + 1

    with open(output, "a") as fout:
        nb_error = 0
        while done < max_done:
            # Read a chunk of the input files
            logger.info(_("Loading UUID from %d to %d"), done, done + chunk - 1)
            to_update = np.loadtxt(
                input,
                delimiter="\t",
                usecols=(2, 3),
                skiprows=done,  # Skipping header + already done
                max_rows=chunk,
                dtype={"names": ("id_universal", "uuid"), "formats": ("U36", "U13")},
            )

            for row in to_update:
                id_universal = row[1].strip()
                new_uuid = row[0].strip()
                logger.info(
                    _("Update # %s, sighting %s, uuid %s"),
                    done,
                    id_universal,
                    new_uuid,
                )

                # Get current observation
                try:
                    sighting = obs_api[update_site].api_search(
                        {"id_sighting_universal": id_universal},
                        short_version="1",
                    )
                except HTTPError:
                    sighting = []
                    # Avoid looping on permanent error
                    nb_error += 1
                    if nb_error > 100:
                        raise HTTPError
                if sighting == []:
                    # No sighting found, probably deleted
                    fout.write(f"{id_universal}\tUnfound\n")
                else:
                    # Found a sighting implies transient error
                    nb_error = 0
                    # Sighting found : update UUID
                    if "forms" in sighting["data"]:
                        # Received a form, changing to single sighting
                        sighting["data"] = sighting["data"]["forms"][0]
                    logger.debug(
                        _("Before: %s"),
                        sighting["data"],
                    )

                    # Get current UUID, if exists
                    repl = "sighting['data']['sightings'][0]['observers'][0]['uuid']"
                    try:
                        old_attr = eval(repl)
                    except KeyError:
                        old_attr = None
                    exec("{} = {}".format(repl, "new_uuid"))

                    # Get sighting id
                    s_id = eval(
                        "sighting['data']['sightings'][0]['observers'][0]['id_sighting']"
                    )

                    logger.debug(_("After: %s"), sighting["data"])
                    # Update to remote site
                    obs_api[update_site].api_update(s_id, sighting)
                    # Append previous UUID to output
                    fout.write(f"{id_universal}\t{old_attr}\n")
                done += 1


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
    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    # Create formatter and add it to the handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # Add the handlers to the logger
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
        raise FileNotFoundError
    logger.info(_("Getting configuration data from %s"), args.config)
    try:
        cfg_ctrl = EvnConf(args.config)
    except YAMLValidationError:
        logger.critical(_("Incorrect content in YAML configuration %s"), args.config)
        raise

    # Update Biolovision site from update file
    if not Path(args.input).is_file():
        logger.critical(_("Input file %s does not exist"), str(Path(args.input)))
        raise FileNotFoundError
    if Path(args.output).is_file():
        logger.info(_("Output file %s is extended"), str(Path(args.output)))
    else:
        logger.info(_("Output file %s is created"), str(Path(args.output)))
        Path(args.output).touch()
    update(cfg_ctrl, args.input, args.output, args.max_done, args.chunk)

    return None


def run():
    """Entry point for console_scripts"""
    main(sys.argv[1:])


# Main wrapper
if __name__ == "__main__":
    run()
