#!/usr/bin/env python3
"""
Program managing VisioNature export to Postgresql database

"""
import argparse
import logging
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import pkg_resources
import psutil
import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader
from pytz import utc

import yappi
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_SUBMITTED
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers import SchedulerNotRunningError
from apscheduler.schedulers.background import BackgroundScheduler
from export_vn.download_vn import (
    Entities,
    Families,
    Fields,
    LocalAdminUnits,
    Observations,
    Observers,
    Places,
    Species,
    TaxoGroup,
    TerritorialUnits,
    Validations,
)
from export_vn.evnconf import EvnConf
from export_vn.store_all import StoreAll
from export_vn.store_file import StoreFile
from export_vn.store_postgresql import PostgresqlUtils, StorePostgresql
from strictyaml import YAMLValidationError
from tabulate import tabulate

from . import _, __version__

CTRL_DEFS = {
    "entities": Entities,
    "families": Families,
    "fields": Fields,
    "local_admin_units": LocalAdminUnits,
    "observations": Observations,
    "observers": Observers,
    "places": Places,
    "species": Species,
    "taxo_groups": TaxoGroup,
    "territorial_units": TerritorialUnits,
    "validations": Validations,
}
logger = logging.getLogger("transfer_vn")


class Jobs:
    def _listener(self, event):
        if event.code == EVENT_JOB_SUBMITTED:
            logger.debug(_("The job %s started"), event.job_id)
            self._job_set.add(event.job_id)
        else:
            if event.job_id in self._job_set:
                self._job_set.remove(event.job_id)
            else:
                logger.error(
                    _("Job %s not found in job_set"), event.job_id
                )  # pragma: no cover
            if event.exception:
                logger.error(_("The job %s crashed"), event.job_id)  # pragma: no cover
            else:
                logger.debug(_("The job %s worked"), event.job_id)
        logger.debug(_("Job set: %s"), self._job_set)

    def __init__(self, url="sqlite:///jobs.sqlite", nb_executors=1):
        """Initialize class.

        Parameters
        ----------
        url: str
            SQLalchemy URL for persistent jobstore.
        nb_executors : int
            Number of concurrent executor processes.

        """
        self._job_set = set()
        logger.info(
            _("Creating scheduler, %s executors, storing in %s"),
            nb_executors,
            str(url)[0 : str(url).find(":")],
        )
        jobstores = {"once": MemoryJobStore(), "default": SQLAlchemyJobStore(url=url)}
        executors = {"default": ProcessPoolExecutor(nb_executors)}
        job_defaults = {
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 3600,
        }
        self._scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=utc,
        )
        self._scheduler.add_listener(
            self._listener, EVENT_JOB_SUBMITTED | EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logger.info(_("Shutting down scheduler in __atexit__, if still running"))
        try:
            self._scheduler.shutdown(wait=False)
        except Exception:
            pass

    def shutdown(self):
        logger.info(_("Shutting down scheduler"))
        try:
            self._scheduler.shutdown()
        except SchedulerNotRunningError:  # pragma: no cover
            pass

    def _handler(self, signum, frame):  # pragma: no cover
        logger.error(_("Signal handler called with signal %s"), signum)
        try:
            self._scheduler.shutdown(wait=False)
        except SchedulerNotRunningError:
            pass
        try:
            parent_id = os.getpid()
            for child in psutil.Process(parent_id).children(recursive=True):
                child.kill()
        except Exception:
            pass
        sys.exit(1)

    def start(self, paused=False):
        logger.debug(_("Starting scheduler, paused=%s"), paused)
        self._scheduler.start(paused)
        signal.signal(signal.SIGINT, self._handler)
        # signal.signal(signal.SIGTERM, self._handler)

    # def pause(self):
    #     logger.debug(_("Pausing scheduler"))
    #     self._scheduler.pause()

    def resume(self):
        logger.debug(_("Resuming scheduler"))
        self._scheduler.resume()

    def remove_all_jobs(self):
        logger.debug(_("Removing all scheduled jobs"))
        self._scheduler.remove_all_jobs()

    def add_job_once(self, job_fn, args=None, kwargs=None):
        logger.debug(
            _("Adding immediate job %s"), args[0].__name__ + "_" + args[2].site
        )
        self._scheduler.add_job(
            job_fn,
            args=args,
            kwargs=kwargs,
            id=args[0].__name__ + "_" + args[2].site,
            jobstore="once",
        )

    def add_job_schedule(
        self,
        job_fn,
        args=None,
        kwargs=None,
        year=None,
        month=None,
        day=None,
        week=None,
        day_of_week=None,
        hour=None,
        minute=None,
        second=None,
    ):
        logger.debug(
            _("Adding scheduled job %s"), args[0].__name__ + "_" + args[2].site
        )
        self._scheduler.add_job(
            job_fn,
            args=args,
            kwargs=kwargs,
            id=args[0].__name__ + "_" + args[2].site,
            jobstore="default",
            trigger="cron",
            year=year,
            month=month,
            day=day,
            week=week,
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            second=second,
            replace_existing=True,
        )

    def count_jobs(self):
        # self._scheduler.print_jobs()
        jobs = self._scheduler.get_jobs()
        logger.debug(_("Number of jobs scheduled, %s"), len(jobs))
        for j in jobs:
            logger.debug(
                _("Job %s, scheduled in: %s"),
                j.id,
                j.next_run_time - datetime.now(timezone.utc),
            )
        logger.debug(_("Number of jobs running, %s"), len(self._job_set))
        return len(self._job_set)

    def print_jobs(self):
        jobs = self._scheduler.get_jobs()
        logger.info(_("Number of jobs scheduled, %s"), len(jobs))
        for j in jobs:
            logger.info(_("Job %s, scheduled: %s"), j.id, j.trigger)


def db_config(cfg):
    """Return database related parameters."""
    return {
        "db_host": cfg.db_host,
        "db_port": cfg.db_port,
        "db_name": cfg.db_name,
        "db_schema_import": cfg.db_schema_import,
        "db_schema_vn": cfg.db_schema_vn,
        "db_group": cfg.db_group,
        "db_user": cfg.db_user,
        "db_pw": cfg.db_pw,
        "db_secret_key": cfg.db_secret_key,
        "proj": cfg.db_out_proj,
    }


def arguments(args):
    """Define and parse command arguments.

    Args:
        args ([str]): command line parameters as list of strings

    Returns:
        :obj:`argparse.Namespace`: command line parameters namespace
    """
    # Get options
    parser = argparse.ArgumentParser(
        description="Script that transfers data from Biolovision"
        + "and stores it to a Postgresql database."
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
    parser.add_argument(
        "--db_drop", help=_("Delete if exists database and roles"), action="store_true"
    )
    parser.add_argument(
        "--db_create", help=_("Create database and roles"), action="store_true"
    )
    parser.add_argument(
        "--json_tables_create",
        help=_("Create or recreate json tables"),
        action="store_true",
    )
    parser.add_argument(
        "--col_tables_create",
        help=_("Create or recreate colums based tables"),
        action="store_true",
    )
    download_group = parser.add_mutually_exclusive_group()
    download_group.add_argument(
        "--full", help=_("Perform a full download"), action="store_true"
    )
    download_group.add_argument(
        "--update", help=_("Perform an incremental download"), action="store_true"
    )
    download_group.add_argument(
        "--schedule",
        help=_("Create or modify incremental download schedule"),
        action="store_true",
    )
    parser.add_argument(
        "--status",
        help=_("Print downloading status (schedule, errors...)"),
        action="store_true",
    )
    parser.add_argument(
        "--count",
        help=_("Count observations by site and taxo_group"),
        action="store_true",
    )
    parser.add_argument(
        "--profile", help=_("Gather and print profiling times"), action="store_true"
    )
    parser.add_argument("file", help=_("Configuration file name"))

    return parser.parse_args(args)


def init(file: str):
    """Copy template YAML file to home directory."""
    logger = logging.getLogger("transfer_vn")
    yaml_src = pkg_resources.resource_filename(__name__, "data/evn_template.yaml")
    yaml_dst = str(Path.home() / file)
    logger.info(_("Creating YAML configuration file %s, from %s"), yaml_dst, yaml_src)
    shutil.copyfile(yaml_src, yaml_dst)
    logger.info(_("Please edit %s before running the script"), yaml_dst)


def col_table_create(cfg, sql_quiet, client_min_message):
    """Create the column based tables, by running psql script."""
    logger = logging.getLogger("transfer_vn")
    logger.debug(_("Creating SQL file from template"))
    env = Environment(
        loader=PackageLoader("export_vn", "sql"),
        keep_trailing_newline=True,
    )
    template = env.get_template("create-vn-tables.sql")
    cmd = template.render(cfg=db_config(cfg))
    tmp_sql = Path.home() / "tmp/create-vn-tables.sql"
    with tmp_sql.open(mode="w") as myfile:
        myfile.write(cmd)
    try:
        subprocess.run(
            ' PGPASSWORD="' + cfg.db_pw + '" '
            'env PGOPTIONS="-c client-min-messages='
            + client_min_message
            + '" psql '
            + sql_quiet
            + " --host="
            + cfg.db_host
            + " --port="
            + cfg.db_port
            + " --dbname="
            + cfg.db_name
            + " --user="
            + cfg.db_user
            + " --file="
            + str(tmp_sql),
            check=True,
            shell=True,
        )
    except subprocess.CalledProcessError as err:  # pragma: no cover
        logger.error(err)

    return None


def full_download_1(ctrl, cfg_crtl_list, cfg):
    """Downloads from a single controler."""
    logger = logging.getLogger("transfer_vn")
    logger.debug(_("Enter full_download_1: %s"), ctrl.__name__)
    with StorePostgresql(cfg) as store_pg, StoreFile(cfg) as store_f:
        store_all = StoreAll(cfg, db_backend=store_pg, file_backend=store_f)
        downloader = ctrl(cfg, store_all)
        if cfg_crtl_list[downloader.name].enabled:
            logger.info(
                _("%s => Starting download using controler %s"),
                cfg.site,
                downloader.name,
            )
            if downloader.name == "observations":
                logger.info(
                    _("%s => Excluded taxo_groups: %s"), cfg.site, cfg.taxo_exclude
                )
                downloader.store(
                    id_taxo_group=None,
                    method="search",
                    by_specie=False,
                    taxo_groups_ex=cfg.taxo_exclude,
                    territorial_unit_ids=cfg.territorial_unit_ids,
                    short_version=(1 if cfg.json_format == "short" else 0),
                )
            elif (downloader.name == "local_admin_units") or (
                downloader.name == "places"
            ):
                logger.info(
                    _("%s => Included territorial_unit_ids: %s"),
                    cfg.site,
                    cfg.territorial_unit_ids,
                )
                downloader.store(
                    territorial_unit_ids=cfg.territorial_unit_ids,
                )
            else:
                downloader.store()
            logger.info(
                _("%s => Ending download using controler %s"), cfg.site, downloader.name
            )


def full_download(cfg_ctrl):
    """Performs a full download of all sites and controlers,
    based on configuration file."""
    logger = logging.getLogger("transfer_vn")
    cfg_crtl_list = cfg_ctrl.ctrl_list
    cfg_site_list = cfg_ctrl.site_list
    cfg = list(cfg_site_list.values())[0]

    logger.info(_("Defining full download jobs"))
    # db_url = {
    #     "drivername": "postgresql+psycopg2",
    #     "username": cfg.db_user,
    #     "password": cfg.db_pw,
    #     "host": cfg.db_host,
    #     "port": cfg.db_port,
    #     "database": "postgres",
    # }
    jobs_o = Jobs(nb_executors=cfg.tuning_sched_executors)
    with jobs_o as jobs:
        # Cleanup any existing job
        jobs.start(paused=True)
        jobs.remove_all_jobs()
        jobs.resume()
        # Download field only once
        jobs.add_job_once(job_fn=full_download_1, args=[Fields, cfg_crtl_list, cfg])
        # Looping on sites for other controlers
        for site, cfg in cfg_site_list.items():
            if cfg.enabled:
                logger.info(_("Scheduling work for site %s"), cfg.site)
                jobs.add_job_once(
                    job_fn=full_download_1, args=[Entities, cfg_crtl_list, cfg]
                )
                jobs.add_job_once(
                    job_fn=full_download_1, args=[Families, cfg_crtl_list, cfg]
                )
                jobs.add_job_once(
                    job_fn=full_download_1, args=[LocalAdminUnits, cfg_crtl_list, cfg]
                )
                jobs.add_job_once(
                    job_fn=full_download_1, args=[Observations, cfg_crtl_list, cfg]
                )
                jobs.add_job_once(
                    job_fn=full_download_1, args=[Observers, cfg_crtl_list, cfg]
                )
                jobs.add_job_once(
                    job_fn=full_download_1, args=[Places, cfg_crtl_list, cfg]
                )
                jobs.add_job_once(
                    job_fn=full_download_1, args=[Species, cfg_crtl_list, cfg]
                )
                jobs.add_job_once(
                    job_fn=full_download_1, args=[TaxoGroup, cfg_crtl_list, cfg]
                )
                jobs.add_job_once(
                    job_fn=full_download_1, args=[TerritorialUnits, cfg_crtl_list, cfg]
                )
                jobs.add_job_once(
                    job_fn=full_download_1, args=[Validations, cfg_crtl_list, cfg]
                )
            else:
                logger.info(_("Skipping site %s"), site)

        # Wait for jobs to finish
        time.sleep(1)
        while jobs.count_jobs() > 0:
            time.sleep(1)
        jobs.shutdown()

    return None


def increment_download_1(ctrl, cfg_crtl_list, cfg):
    """Download incremental updates from one site."""
    logger = logging.getLogger("transfer_vn")
    logger.debug(_("Enter increment_download_1: %s"), ctrl.__name__)
    with StorePostgresql(cfg) as store_pg, StoreFile(cfg) as store_f:
        store_all = StoreAll(cfg, db_backend=store_pg, file_backend=store_f)
        downloader = ctrl(cfg, store_all)
        if cfg_crtl_list[downloader.name].enabled:
            logger.info(
                _("%s => Starting incremental download using controler %s"),
                cfg.site,
                downloader.name,
            )
            if downloader.name == "observations":
                logger.info(
                    _("%s => Excluded taxo_groups: %s"), cfg.site, cfg.taxo_exclude
                )
                downloader.update(taxo_groups_ex=cfg.taxo_exclude)
            elif (downloader.name == "local_admin_units") or (
                downloader.name == "places"
            ):
                logger.info(
                    _("%s => Included territorial_unit_ids: %s"),
                    cfg.site,
                    cfg.territorial_unit_ids,
                )
                downloader.store(
                    territorial_unit_ids=cfg.territorial_unit_ids,
                )
            else:
                downloader.store()
            logger.info(
                _("%s => Ending download using controler %s"), cfg.site, downloader.name
            )


def increment_download(cfg_ctrl):
    """Performs an incremental download of observations from all sites
    and controlers, based on configuration file."""
    logger = logging.getLogger("transfer_vn")
    cfg_site_list = cfg_ctrl.site_list
    cfg = list(cfg_site_list.values())[0]

    logger.info(_("Starting incremental download jobs"))
    # db_url = {
    #     "drivername": "postgresql+psycopg2",
    #     "username": cfg.db_user,
    #     "password": cfg.db_pw,
    #     "host": cfg.db_host,
    #     "port": cfg.db_port,
    #     "database": "postgres",
    # }

    jobs_o = Jobs(nb_executors=cfg.tuning_sched_executors)
    with jobs_o as jobs:
        # Start scheduler and wait for jobs to finish
        jobs.start()
        time.sleep(1)
        while jobs.count_jobs() > 0:
            time.sleep(1)
        jobs.shutdown()

    return None


def increment_schedule(cfg_ctrl):
    """Creates or modify the incremental download schedule,
    based on YAML controler configuration."""
    logger = logging.getLogger("transfer_vn")
    cfg_crtl_list = cfg_ctrl.ctrl_list
    cfg_site_list = cfg_ctrl.site_list
    cfg = list(cfg_site_list.values())[0]

    logger.info(_("Defining incremental download jobs"))
    # db_url = {
    #     "drivername": "postgresql+psycopg2",
    #     "username": cfg.db_user,
    #     "password": cfg.db_pw,
    #     "host": cfg.db_host,
    #     "port": cfg.db_port,
    #     "database": "postgres",
    # }
    jobs = Jobs(nb_executors=cfg.tuning_sched_executors)
    # Looping on sites
    for site, cfg in cfg_site_list.items():
        if cfg.enabled:
            logger.info(_("Scheduling increments on site %s"), site)
            for ctrl_name, ctrl_props in cfg_crtl_list.items():
                if ctrl_props.enabled:
                    logger.debug(
                        _("%s => Adding schedule for controler %s"), site, ctrl_name
                    )
                    jobs.add_job_schedule(
                        job_fn=increment_download_1,
                        args=[CTRL_DEFS[ctrl_name], cfg_crtl_list, cfg],
                        year=ctrl_props.schedule_year,
                        month=ctrl_props.schedule_month,
                        day=ctrl_props.schedule_day,
                        week=ctrl_props.schedule_week,
                        day_of_week=ctrl_props.schedule_day_of_week,
                        hour=ctrl_props.schedule_hour,
                        minute=ctrl_props.schedule_minute,
                        second=ctrl_props.schedule_second,
                    )
        else:
            logger.info(_("Skipping site %s"), site)

    # Print status
    jobs.start(paused=True)
    jobs.print_jobs()
    jobs.shutdown()

    return None


def status(cfg_ctrl):
    """Print download status, using logger."""
    logger = logging.getLogger("transfer_vn")
    cfg_site_list = cfg_ctrl.site_list
    cfg_site_list = cfg_ctrl.site_list
    cfg = list(cfg_site_list.values())[0]

    logger.info(_("Download jobs status"))
    # db_url = {
    #     "drivername": "postgresql+psycopg2",
    #     "username": cfg.db_user,
    #     "password": cfg.db_pw,
    #     "host": cfg.db_host,
    #     "port": cfg.db_port,
    #     "database": "postgres",
    # }
    jobs = Jobs(nb_executors=cfg.tuning_sched_executors)
    jobs.start(paused=True)
    jobs.print_jobs()


def count_observations(cfg_ctrl):
    """Count observations by site and taxo_group."""
    logger = logging.getLogger("transfer_vn")
    cfg_site_list = cfg_ctrl.site_list

    col_counts = None
    for site, cfg in cfg_site_list.items():
        try:
            if cfg.enabled:
                if col_counts is None:
                    manage_pg = PostgresqlUtils(cfg)
                    # print(tabulate(manage_pg.count_json_obs()))
                    col_counts = manage_pg.count_col_obs()

                logger.info(_("Getting counts from %s"), cfg.site)
                site_counts = list()
                if cfg.site == "Haute-Savoie":
                    for r in col_counts:
                        if r[0] == "Haute-Savoie":
                            site_counts.append([r[0], r[2], -1, r[3]])
                else:
                    url = cfg.base_url + "index.php?m_id=23"
                    page = requests.get(url)
                    soup = BeautifulSoup(page.text, "html.parser")

                    counts = soup.find_all("table")[2].contents[1].contents[3]
                    rows = counts.contents[5].contents[0].contents[0].contents[1:-1]
                    for i in range(0, len(rows)):
                        if i % 5 == 0:
                            taxo = rows[i].contents[0]["title"]
                        elif i % 5 == 4:
                            col_c = 0
                            for r in col_counts:
                                if r[0] == site and r[2] == taxo:
                                    col_c = r[3]
                            site_counts.append(
                                [
                                    cfg.site,
                                    taxo,
                                    int(
                                        rows[i].contents[0].contents[0].replace(" ", "")
                                    ),
                                    col_c,
                                ]
                            )
                print(
                    tabulate(
                        site_counts,
                        headers=[
                            _("Site"),
                            _("TaxoName"),
                            _("Remote count"),
                            _("Local count"),
                        ],
                        tablefmt="psql",
                    )
                )
        except Exception:  # pragma: no cover
            logger.error(_("Can not retrieve informations from %s"), cfg.site)

    return None


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    # Create $HOME/tmp directory if it does not exist
    (Path.home() / "tmp").mkdir(exist_ok=True)

    # Define logger format and handlers
    logger = logging.getLogger("transfer_vn")
    # create file handler which logs even debug messages
    fh = TimedRotatingFileHandler(
        str(Path.home()) + "/tmp/transfer_vn.log",
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

    # Start profiling if required
    if args.profile:
        yappi.start()
        logger.info(_("Started yappi"))

    # Define verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        sql_quiet = ""
        client_min_message = "debug1"
    else:
        logger.setLevel(logging.INFO)
        sql_quiet = "--quiet"
        client_min_message = "warning"

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
    logger.info(_("Getting configuration data from %s"), args.file)
    try:
        cfg_ctrl = EvnConf(args.file)
    except YAMLValidationError:
        logger.critical(_("Incorrect content in YAML configuration %s"), args.file)
        sys.exit(0)
    cfg_site_list = cfg_ctrl.site_list
    cfg = list(cfg_site_list.values())[0]
    # Check configuration consistency
    if cfg.db_enabled and cfg.json_format != "short":
        logger.critical(_("Storing to Postgresql cannot use long json_format."))
        logger.critical(_("Please modify YAML configuration and restart."))
        sys.exit(0)

    manage_pg = PostgresqlUtils(cfg)

    if args.db_drop:
        logger.info(_("Delete if exists database and roles"))
        manage_pg.drop_database()

    if args.db_create:
        logger.info(_("Create database and roles"))
        manage_pg.create_database()

    if args.json_tables_create:
        logger.info(_("Create, if not exists, json tables"))
        manage_pg.create_json_tables()

    if args.col_tables_create:
        logger.info(_("Creating or recreating vn columns based tables"))
        col_table_create(cfg, sql_quiet, client_min_message)

    if args.full:
        logger.info(_("Performing a full download"))
        full_download(cfg_ctrl)

    if args.schedule:
        logger.info(_("Creating or modifying incremental download schedule"))
        increment_schedule(cfg_ctrl)

    if args.update:
        logger.info(_("Performing an incremental download"))
        increment_download(cfg_ctrl)

    if args.status:
        logger.info(_("Printing download status"))
        status(cfg_ctrl)

    if args.count:
        logger.info(_("Counting observations"))
        count_observations(cfg_ctrl)

    # Stop and output profiling if required
    if args.profile:
        logger.info(_("Printing yappi results"))
        yappi.stop()
        yappi.get_func_stats().print_all()
        yappi.get_thread_stats().print_all()

    return None


def run():
    """Entry point for console_scripts"""
    main(sys.argv[1:])


# Main wrapper
if __name__ == "__main__":
    run()
