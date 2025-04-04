#!/usr/bin/env python3
"""
Program managing VisioNature export to Postgresql database

"""
# ruff: noqa: S602

import argparse
import contextlib
import importlib.resources
import logging
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import psutil
import requests
import yappi
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_SUBMITTED
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers import SchedulerNotRunningError
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from dynaconf import Dynaconf, ValidationError, Validator
from jinja2 import Environment, PackageLoader
from pytz import utc
from tabulate import tabulate

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
from export_vn.store_all import StoreAll
from export_vn.store_file import StoreFile
from export_vn.store_postgresql import PostgresqlUtils, StorePostgresql

from . import __version__

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
DEFS_CTRL = {value: key for key, value in CTRL_DEFS.items()}

TIMEOUT = 30  # Requests.get timeout

logger = logging.getLogger(__name__)


class Jobs:
    """Class to manage jobs scheduling."""

    def _listener(self, event):
        if event.code == EVENT_JOB_SUBMITTED:
            logger.debug(_("The job %s started"), event.job_id)
            self._job_set.add(event.job_id)
        else:
            if event.job_id in self._job_set:
                self._job_set.remove(event.job_id)
            else:
                logger.error(_("The job %s is not in job_set"), event.job_id)  # pragma: no cover
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
        executors = {"default": ThreadPoolExecutor(nb_executors)}
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
        self._scheduler.add_listener(self._listener, EVENT_JOB_SUBMITTED | EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logger.info(_("Shutting down scheduler in __atexit__, if still running"))
        with contextlib.suppress(Exception):
            self._scheduler.shutdown(wait=False)

    def shutdown(self):
        logger.info(_("Shutting down scheduler"))
        with contextlib.suppress(SchedulerNotRunningError):
            self._scheduler.shutdown()

    def _handler(self, signum, frame):  # pragma: no cover
        logger.error(_("Signal handler called with signal %s"), signum)
        with contextlib.suppress(SchedulerNotRunningError):
            self._scheduler.shutdown(wait=False)

        with contextlib.suppress(SchedulerNotRunningError):
            parent_id = os.getpid()
            for child in psutil.Process(parent_id).children(recursive=True):
                child.kill()

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
        job_name = args[0]
        logger.debug(_("Adding immediate job %s"), job_name)
        self._scheduler.add_job(
            job_fn,
            args=args,
            kwargs=kwargs,
            id=job_name,
            jobstore="once",
        )
        jobs = self._scheduler.get_jobs()
        logger.info(_("Number of jobs scheduled, %s"), len(jobs))
        for j in jobs:
            logger.info(_("Job %s, scheduled: %s"), j.id, j.trigger)
        return None

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
        job_name = args[0]
        logger.debug(_("Adding scheduled job %s"), job_name)
        self._scheduler.add_job(
            job_fn,
            args=args,
            kwargs=kwargs,
            id=job_name,
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
                j.next_run_time - datetime.now(UTC),
            )
        logger.debug(_("Number of jobs running, %s"), len(self._job_set))
        return len(self._job_set)

    def print_jobs(self):
        jobs = self._scheduler.get_jobs()
        logger.info(_("Number of jobs scheduled, %s"), len(jobs))
        for j in jobs:
            logger.info(_("Job %s, scheduled: %s"), j.id, j.trigger)


def arguments(args):
    """Define and parse command arguments.

    Args:
        args ([str]): command line parameters as list of strings

    Returns:
        :obj:`argparse.Namespace`: command line parameters namespace
    """
    # Get options
    parser = argparse.ArgumentParser(
        description="Script that transfers data from Biolovision" + "and stores it to a Postgresql database."
    )
    parser.add_argument(
        "--version",
        help=_("Print version number"),
        action="version",
        version=f"%(prog)s {__version__}",
    )
    out_group = parser.add_mutually_exclusive_group()
    out_group.add_argument("--verbose", help=_("Increase output verbosity"), action="store_true")
    out_group.add_argument("--quiet", help=_("Reduce output verbosity"), action="store_true")
    parser.add_argument("--init", help=_("Initialize the YAML configuration file"), action="store_true")
    parser.add_argument("--db_drop", help=_("Delete if exists database and roles"), action="store_true")
    parser.add_argument("--db_create", help=_("Create database and roles"), action="store_true")
    parser.add_argument(
        "--db_migrate",
        help=_("Migrate database to current version"),
        action="store_true",
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
    download_group.add_argument("--full", help=_("Perform a full download"), action="store_true")
    download_group.add_argument("--update", help=_("Perform an incremental download"), action="store_true")
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
    parser.add_argument("--profile", help=_("Gather and print profiling times"), action="store_true")
    parser.add_argument("file", help=_("Configuration file name"))

    return parser.parse_args(args)


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


def col_table_create(
    db_host: str,
    db_port: str,
    db_name: str,
    db_user: str,
    db_pw: str,
    db_schema_import: str,
    db_schema_vn: str,
    db_group: str,
    db_out_proj: str,
    sql_quiet: str,
    client_min_message: str,
) -> None:
    """Create the column based tables, by running psql script.

    Parameters
    ----------
    db_host: str
        Hostname of the database.
    db_port: str
        Port number of the database.
    db_name: str
        Name of the database.
    db_user: str
        User name for the database.
    db_pw: str
        Password for the database.
    db_schema_import: str
        Schema for import tables.
    db_schema_vn: str
        Schema for VN tables.
    db_group: str
        Group for the database.
    db_out_proj: str
        Output projection for the database.
    sql_quiet: str
        SQL quiet option.
    client_min_message: str
        Client minimum message level.
    Return:
        None

    """
    logger.debug(_("Creating SQL file from template"))
    env = Environment(
        loader=PackageLoader("export_vn", "sql"),
        keep_trailing_newline=True,
        autoescape=True,
    )
    template = env.get_template("create-vn-tables.sql")
    cmd = template.render({
        "db_host": db_host,
        "db_port": db_port,
        "db_name": db_name,
        "db_schema_import": db_schema_import,
        "db_schema_vn": db_schema_vn,
        "db_group": db_group,
        "db_user": db_user,
        "db_pw": db_pw,
        "proj": db_out_proj,
    })
    tmp_sql = Path.home() / "tmp/create-vn-tables.sql"
    with tmp_sql.open(mode="w") as myfile:
        myfile.write(cmd)
    try:
        subprocess.run(
            ' PGPASSWORD="'
            + db_pw
            + '" PGOPTIONS="-c client-min-messages='
            + client_min_message
            + '" psql '
            + sql_quiet
            + " --host="
            + db_host
            + " --port="
            + db_port
            + " --dbname="
            + db_name
            + " --user="
            + db_user
            + " --file="
            + str(tmp_sql),
            check=True,
            shell=True,
        )
    except subprocess.CalledProcessError:  # pragma: no cover
        logger.exception()

    return None


def migrate(cfg, sql_quiet, client_min_message):
    """Create the column based tables, by running psql script."""
    logger.debug(_("Migrating database to current version"))
    Environment(
        loader=PackageLoader("export_vn", "sql"),
        keep_trailing_newline=True,
        autoescape=True,
    )
    try:
        subprocess.run(
            "alembic -x db_schema_import="
            + cfg.db_schema_import
            + " -x db_url=postgresql://"
            + cfg.db_user
            + ":"
            + cfg.db_pw
            + "@"
            + cfg.db_host
            + ":"
            + cfg.db_port
            + "/"
            + cfg.db_name
            + "--config src/alembic.ini upgrade head",
            check=True,
            shell=True,
        )
    except subprocess.CalledProcessError:  # pragma: no cover
        logger.exception()

    return None


def full_download_1(ctrl: str, settings: dict) -> None:
    """Downloads from a single controler."""
    logger.debug(_("Enter full_download_1: %s"), ctrl)
    with (
        StorePostgresql(
            settings["SITE"]["name"],
            settings["DATABASE"]["enabled"],
            settings["DATABASE"]["db_user"],
            settings["DATABASE"]["db_pw"],
            settings["DATABASE"]["db_host"],
            settings["DATABASE"]["db_port"],
            settings["DATABASE"]["db_name"],
            settings["DATABASE"]["db_schema_import"],
            settings["DATABASE"]["db_schema_vn"],
            settings["DATABASE"]["db_group"],
            settings["DATABASE"]["db_out_proj"],
        ) as store_pg,
        StoreFile(settings["FILE"]["enabled"], settings["FILE"]["file_store"]) as store_f,
    ):
        store_all = StoreAll(
            settings["DATABASE"]["enabled"], settings["FILE"]["enabled"], db_backend=store_pg, file_backend=store_f
        )
        if settings["CONTROLER"][ctrl]["enabled"]:
            logger.info(
                _("Starting download using controler %s"),
                ctrl,
            )
        if ctrl == "observations":
            taxo_exclude = list(key for key, value in settings["FILTER"]["taxo_download"].items() if value is False)
            logger.info(_("Excluded taxo_groups: %s"), taxo_exclude)
            CTRL_DEFS[ctrl](
                site=settings["SITE"]["name"],
                user_email=settings["SITE"]["user_email"],
                user_pw=settings["SITE"]["user_pw"],
                base_url=settings["SITE"]["URL"],
                client_key=settings["SITE"]["client_key"],
                client_secret=settings["SITE"]["client_secret"],
                db_enabled=settings["DATABASE"]["enabled"],
                db_user=settings["DATABASE"]["db_user"],
                db_pw=settings["DATABASE"]["db_pw"],
                db_host=settings["DATABASE"]["db_host"],
                db_port=settings["DATABASE"]["db_port"],
                db_name=settings["DATABASE"]["db_name"],
                db_schema_import=settings["DATABASE"]["db_schema_import"],
                db_schema_vn=settings["DATABASE"]["db_schema_vn"],
                db_group=settings["DATABASE"]["db_group"],
                db_out_proj=settings["DATABASE"]["db_out_proj"],
                backend=store_all,
                start_date=settings["FILTER"].get("start_date", None),
                end_date=settings["FILTER"].get("end_date", None),
                type_date=settings["FILTER"].get("type_date", "sighting"),
                max_list_length=settings["TUNING"]["max_list_length"],
                max_retry=settings["TUNING"]["max_retry"],
                max_requests=settings["TUNING"]["max_requests"],
                max_chunks=settings["TUNING"]["max_chunks"],
                unavailable_delay=settings["TUNING"]["unavailable_delay"],
                retry_delay=settings["TUNING"]["retry_delay"],
                pid_kp=settings["TUNING"]["pid_kp"],
                pid_ki=settings["TUNING"]["pid_ki"],
                pid_kd=settings["TUNING"]["pid_kd"],
                pid_setpoint=settings["TUNING"]["pid_setpoint"],
                pid_limit_min=settings["TUNING"]["pid_limit_min"],
                pid_limit_max=settings["TUNING"]["pid_limit_max"],
                pid_delta_days=settings["TUNING"]["pid_delta_days"],
            ).store(
                taxo_groups_ex=taxo_exclude,
                territorial_unit_ids=settings["FILTER"]["territorial_unit_ids"],
            )
        elif (ctrl == "local_admin_units") or (ctrl == "places"):
            logger.info(
                _("Included territorial_unit_ids: %s"),
                settings["FILTER"]["territorial_unit_ids"],
            )
            CTRL_DEFS[ctrl](
                site=settings["SITE"]["name"],
                user_email=settings["SITE"]["user_email"],
                user_pw=settings["SITE"]["user_pw"],
                base_url=settings["SITE"]["URL"],
                client_key=settings["SITE"]["client_key"],
                client_secret=settings["SITE"]["client_secret"],
                backend=store_all,
            ).store(
                territorial_unit_ids=settings["FILTER"]["territorial_unit_ids"],
            )
        else:
            CTRL_DEFS[ctrl](
                site=settings["SITE"]["name"],
                user_email=settings["SITE"]["user_email"],
                user_pw=settings["SITE"]["user_pw"],
                base_url=settings["SITE"]["URL"],
                client_key=settings["SITE"]["client_key"],
                client_secret=settings["SITE"]["client_secret"],
                backend=store_all,
            ).store()
        logger.info(_("Ending download using controler %s"), ctrl)

    return None


def full_download(settings: Dynaconf) -> None:
    """Performs a full download of all sites and controlers,
    based on configuration file.

    Parameters
    ----------
    settings: Dynaconf
    """

    logger.info(_("Defining full download jobs"))
    jobs_o = Jobs(url="sqlite:///" + settings.tuning.sched_sqllite_file, nb_executors=settings.tuning.sched_executors)
    with jobs_o as jobs:
        # Cleanup any existing job
        jobs.start(paused=True)
        jobs.remove_all_jobs()
        jobs.resume()
        # Schedule enabled jobs for immediate execution
        if settings.controler.entities.enabled:
            jobs.add_job_once(job_fn=full_download_1, args=["entities", settings.as_dict()])
        if settings.controler.families.enabled:
            jobs.add_job_once(job_fn=full_download_1, args=["families", settings.as_dict()])
        if settings.controler.fields.enabled:
            jobs.add_job_once(job_fn=full_download_1, args=["fields", settings.as_dict()])
        if settings.controler.local_admin_units.enabled:
            jobs.add_job_once(job_fn=full_download_1, args=["local_admin_units", settings.as_dict()])
        if settings.controler.observations.enabled:
            jobs.add_job_once(job_fn=full_download_1, args=["observations", settings.as_dict()])
        if settings.controler.observers.enabled:
            jobs.add_job_once(job_fn=full_download_1, args=["observers", settings.as_dict()])
        if settings.controler.places.enabled:
            jobs.add_job_once(job_fn=full_download_1, args=["places", settings.as_dict()])
        if settings.controler.species.enabled:
            jobs.add_job_once(job_fn=full_download_1, args=["species", settings.as_dict()])
        if settings.controler.taxo_groups.enabled:
            jobs.add_job_once(job_fn=full_download_1, args=["taxo_groups", settings.as_dict()])
        if settings.controler.territorial_units.enabled:
            jobs.add_job_once(job_fn=full_download_1, args=["territorial_units", settings.as_dict()])
        if settings.controler.validations.enabled:
            jobs.add_job_once(job_fn=full_download_1, args=["validations", settings.as_dict()])

        # Wait for jobs to finish
        while jobs.count_jobs() > 0:
            time.sleep(1)
        jobs.shutdown()

    return None


def increment_download_1(ctrl: str, settings: dict) -> None:
    """Download incremental updates from one site."""
    logger.debug(_("Enter increment_download_1: %s"), ctrl)
    with (
        StorePostgresql(
            settings["SITE"]["name"],
            settings["DATABASE"]["enabled"],
            settings["DATABASE"]["db_user"],
            settings["DATABASE"]["db_pw"],
            settings["DATABASE"]["db_host"],
            settings["DATABASE"]["db_port"],
            settings["DATABASE"]["db_name"],
            settings["DATABASE"]["db_schema_import"],
            settings["DATABASE"]["db_schema_vn"],
            settings["DATABASE"]["db_group"],
            settings["DATABASE"]["db_out_proj"],
        ) as store_pg,
        StoreFile(settings["FILE"]["enabled"], settings["FILE"]["file_store"]) as store_f,
    ):
        store_all = StoreAll(
            settings["DATABASE"]["enabled"], settings["FILE"]["enabled"], db_backend=store_pg, file_backend=store_f
        )
        if settings["CONTROLER"][ctrl]["enabled"]:
            logger.info(
                _("%s => Starting incremental download using controler %s"),
                settings["SITE"]["name"],
                ctrl,
            )

        if ctrl == "observations":
            taxo_exclude = list(key for key, value in settings["FILTER"]["taxo_download"].items() if value is False)
            logger.info(_("Excluded taxo_groups: %s"), taxo_exclude)
            CTRL_DEFS[ctrl](
                site=settings["SITE"]["name"],
                user_email=settings["SITE"]["user_email"],
                user_pw=settings["SITE"]["user_pw"],
                base_url=settings["SITE"]["URL"],
                client_key=settings["SITE"]["client_key"],
                client_secret=settings["SITE"]["client_secret"],
                db_enabled=settings["DATABASE"]["enabled"],
                db_user=settings["DATABASE"]["db_user"],
                db_pw=settings["DATABASE"]["db_pw"],
                db_host=settings["DATABASE"]["db_host"],
                db_port=settings["DATABASE"]["db_port"],
                db_name=settings["DATABASE"]["db_name"],
                db_schema_import=settings["DATABASE"]["db_schema_import"],
                db_schema_vn=settings["DATABASE"]["db_schema_vn"],
                db_group=settings["DATABASE"]["db_group"],
                db_out_proj=settings["DATABASE"]["db_out_proj"],
                backend=store_all,
                start_date=settings["FILTER"].get("start_date", None),
                end_date=settings["FILTER"].get("end_date", None),
                type_date=settings["FILTER"].get("type_date", "sighting"),
                max_list_length=settings["TUNING"]["max_list_length"],
                max_retry=settings["TUNING"]["max_retry"],
                max_requests=settings["TUNING"]["max_requests"],
                max_chunks=settings["TUNING"]["max_chunks"],
                unavailable_delay=settings["TUNING"]["unavailable_delay"],
                retry_delay=settings["TUNING"]["retry_delay"],
                pid_kp=settings["TUNING"]["pid_kp"],
                pid_ki=settings["TUNING"]["pid_ki"],
                pid_kd=settings["TUNING"]["pid_kd"],
                pid_setpoint=settings["TUNING"]["pid_setpoint"],
                pid_limit_min=settings["TUNING"]["pid_limit_min"],
                pid_limit_max=settings["TUNING"]["pid_limit_max"],
                pid_delta_days=settings["TUNING"]["pid_delta_days"],
            ).update(
                taxo_groups_ex=taxo_exclude,
            )
        elif ctrl == "places":
            CTRL_DEFS[ctrl](
                site=settings["SITE"]["name"],
                user_email=settings["SITE"]["user_email"],
                user_pw=settings["SITE"]["user_pw"],
                base_url=settings["SITE"]["URL"],
                client_key=settings["SITE"]["client_key"],
                client_secret=settings["SITE"]["client_secret"],
                backend=store_all,
            ).update(
                territorial_unit_ids=settings["FILTER"]["territorial_unit_ids"],
            )
        elif ctrl == "local_admin_units":
            CTRL_DEFS[ctrl](
                site=settings["SITE"]["name"],
                user_email=settings["SITE"]["user_email"],
                user_pw=settings["SITE"]["user_pw"],
                base_url=settings["SITE"]["URL"],
                client_key=settings["SITE"]["client_key"],
                client_secret=settings["SITE"]["client_secret"],
                backend=store_all,
            ).store(
                territorial_unit_ids=settings["FILTER"]["territorial_unit_ids"],
            )
        else:
            CTRL_DEFS[ctrl](
                site=settings["SITE"]["name"],
                user_email=settings["SITE"]["user_email"],
                user_pw=settings["SITE"]["user_pw"],
                base_url=settings["SITE"]["URL"],
                client_key=settings["SITE"]["client_key"],
                client_secret=settings["SITE"]["client_secret"],
                backend=store_all,
            ).store()
    logger.info(_("Ending download using controler %s"), ctrl)
    return None


def increment_download(settings: Dynaconf) -> None:
    """Performs an incremental download of observations from all sites
    and controlers, based on configuration file."""

    logger.info(_("Starting incremental download jobs"))

    jobs_o = Jobs(url="sqlite:///" + settings.tuning.sched_sqllite_file, nb_executors=settings.tuning.sched_executors)
    with jobs_o as jobs:
        # Start scheduler and wait for jobs to finish
        jobs.start()
        time.sleep(1)
        while jobs.count_jobs() > 0:
            time.sleep(1)
        jobs.shutdown()

    return None


def increment_schedule(settings: Dynaconf) -> None:
    """Creates or modify the incremental download schedule,
    based on controler configuration."""

    logger.info(_("Defining incremental download jobs in %s"), settings.tuning.sched_sqllite_file)

    jobs = Jobs(url="sqlite:///" + settings.tuning.sched_sqllite_file, nb_executors=settings.tuning.sched_executors)
    # Looping on sites
    logger.info(_("Scheduling increments on site %s"), settings.site.name)
    for ctrl_name, ctrl_props in settings.controler.items():
        if ctrl_props.enabled:
            logger.debug(_("Adding schedule for controler %s"), ctrl_name)
            logger.debug(ctrl_props.schedule)
            jobs.add_job_schedule(
                job_fn=increment_download_1,
                args=[ctrl_name, settings.as_dict()],
                year=ctrl_props.schedule.year if "year" in ctrl_props.schedule else "*",
                month=ctrl_props.schedule.month if "month" in ctrl_props.schedule else "*",
                day=ctrl_props.schedule.day if "day" in ctrl_props.schedule else "*",
                week=ctrl_props.schedule.week if "week" in ctrl_props.schedule else "*",
                day_of_week=ctrl_props.schedule.day_of_week if "day_of_week" in ctrl_props.schedule else "*",
                hour=ctrl_props.schedule.hour if "hour" in ctrl_props.schedule else "*",
                minute=ctrl_props.schedule.minute if "minute" in ctrl_props.schedule else "*",
                second=ctrl_props.schedule.second if "second" in ctrl_props.schedule else "0",
            )

    # Print status
    jobs.start(paused=True)
    jobs.print_jobs()
    jobs.shutdown()

    return None


def status(settings: Dynaconf):
    """Print download status, using logger."""

    logger.info(_("Download jobs status"))

    jobs = Jobs(url="sqlite:///" + settings.tuning.sched_sqllite_file, nb_executors=settings.tuning.sched_executors)
    jobs.start(paused=True)
    jobs.print_jobs()


def count_observations(cfg_ctrl):
    """Count observations by site and taxo_group."""
    cfg_site_list = cfg_ctrl.site_list

    col_counts = None
    for site, cfg in cfg_site_list.items():
        try:
            if cfg.enabled:
                if col_counts is None:
                    manage_pg = PostgresqlUtils(cfg)
                    col_counts = manage_pg.count_col_obs()

                logger.info(_("Getting counts from %s"), cfg.site)
                site_counts = []
                if cfg.site == "Haute-Savoie":
                    for r in col_counts:
                        if r[0] == "Haute-Savoie":
                            site_counts.append([r[0], r[2], -1, r[3]])
                else:
                    url = cfg.base_url + "index.php?m_id=23"
                    page = requests.get(
                        url,
                        timeout=TIMEOUT,
                    )
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
                            site_counts.append([
                                cfg.site,
                                taxo,
                                int(rows[i].contents[0].contents[0].replace(" ", "")),
                                col_c,
                            ])
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
            logger.exception(_("Can not retrieve informations from %s"), cfg.site)

    return None


def main(args) -> None:
    """Main entry point calling commands.

    Args:
      args ([str]): command line parameter list
    """
    # Get command line arguments
    args = arguments(args)

    # Start profiling if required
    if args.profile:
        yappi.start()
        logger.info(_("Started yappi"))

    # Create $HOME/tmp directory if it does not exist
    (Path.home() / "tmp").mkdir(exist_ok=True)

    # create file handler which logs even debug messages
    fh = TimedRotatingFileHandler(
        Path.home() / "tmp/transfer_vn.log",
        when="midnight",
        interval=1,
        backupCount=100,
    )
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the root logger
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, handlers=[fh, ch], force=True)

    # Define SQL verbosity
    if args.verbose:
        sql_quiet = ""
        client_min_message = "debug1"
    else:
        sql_quiet = "--quiet"
        client_min_message = "warning"

    logger.info(_("%s, version %s"), sys.argv[0], __version__)
    logger.debug(_("Arguments: %s"), sys.argv[1:])

    # If required, first create YAML file
    if args.init:
        logger.info(_("Creating TOML configuration file"))
        init(args.file)
        return None

    # Get configuration from file
    if not (Path.home() / args.file).is_file():
        logger.critical(_("File %s does not exist"), str(Path.home() / args.file))
        return None
    logger.info(_("Getting configuration data from %s"), args.file)
    settings = Dynaconf(
        settings_files=[args.file],
    )

    # Validation de tous les paramètres

    settings.validators.register(
        Validator("SITE.ENABLED", default=True, cast=bool),
        Validator("SITE.NAME", len_min=1, cast=str),
        Validator("SITE.URL", len_min=10, startswith="https://", cast=str),
        Validator("SITE.USER_EMAIL", len_min=5, cont="@", cast=str),
        Validator("SITE.USER_PW", len_min=5, cast=str),
        Validator("SITE.CLIENT_KEY", len_min=20, cast=str),
        Validator("SITE.CLIENT_SECRET", len_min=5, cast=str),
    )
    # settings.validators.register(
    #     Validator("FILTER.START_DATE", cast=datetime),
    #     Validator("FILTER.END_DATE", cast=datetime),
    # )
    settings.validators.register(
        Validator("FILE.ENABLED", default=True, cast=bool),
        Validator("FILE.FILE_STORE", len_min=1, cast=str),
        Validator("DATABASE.ENABLED", default=True, cast=bool),
        Validator("DATABASE.DB_HOST", len_min=1, cast=str),
        Validator("DATABASE.DB_PORT", len_min=1, cast=str),
        Validator("DATABASE.DB_NAME", len_min=1, cast=str),
        Validator("DATABASE.DB_USER", len_min=1, cast=str),
        Validator("DATABASE.DB_PW", len_min=6, cast=str),
        Validator("DATABASE.DB_SCHEMA_IMPORT", len_min=1, cast=str),
        Validator("DATABASE.DB_SCHEMA_VN", len_min=1, cast=str),
        Validator("DATABASE.DB_GROUP", len_min=1, cast=str),
        Validator("DATABASE.DB_OUT_PROJ", len_min=1, cast=str),
        Validator("TUNING.MAX_LIST_LENGTH", gte=1, default=100, cast=int),
        Validator("TUNING.MAX_CHUNKS", gte=1, default=1000, cast=int),
        Validator("TUNING.MAX_RETRY", gte=1, default=5, cast=int),
        Validator("TUNING.MAX_REQUESTS", gte=0, default=0, cast=int),
        Validator("TUNING.RETRY_DELAY", gte=1, default=5, cast=int),
        Validator("TUNING.UNAVAILABLE_DELAY", gte=1, default=600, cast=int),
        Validator("TUNING.LRU_MAXSIZE", gte=1, default=32, cast=int),
        Validator("TUNING.PID_KP", gte=0, default=0.0, cast=float),
        Validator("TUNING.PID_KI", gte=0, default=0.003, cast=float),
        Validator("TUNING.PID_KD", gte=0, default=0.0, cast=float),
        Validator("TUNING.SETPOINT", gte=0, default=10000, cast=int),
        Validator("TUNING.PID_LIMIT_MIN", gte=0, default=5, cast=int),
        Validator("TUNING.PID_LIMIT_MAX", gte=0, default=2000, cast=int),
        Validator("TUNING.PID_DELTA_DAYS", gte=0, default=10, cast=int),
        Validator("TUNING.SCHED_EXECUTORS", gte=1, default=1, cast=int),
        Validator("TUNING.SCHED_SQLLITE_FILE", default="jobstore.sqllite", cast=str),
    )
    try:
        settings.validators.validate_all()
    except ValidationError as e:
        accumulative_errors = e.details
        logger.exception(accumulative_errors)
        raise ValueError(_("Incorrect configuration file")) from e

    cfg_site_list = settings.site
    cfg = next(iter(cfg_site_list.values()))
    # Check configuration consistency
    if settings.database.enabled and settings.filter.json_format != "short":
        logger.critical(_("Storing to Postgresql cannot use long json_format."))
        logger.critical(_("Please modify YAML configuration and restart."))
        sys.exit(0)

    manage_pg = PostgresqlUtils(
        settings.database.enabled,
        settings.database.db_user,
        settings.database.db_pw,
        settings.database.db_host,
        settings.database.db_port,
        settings.database.db_name,
        settings.database.db_schema_import,
        settings.database.db_schema_vn,
        settings.database.db_group,
    )

    if args.db_drop:
        logger.info(_("Delete if exists database and roles"))
        manage_pg.drop_database()

    if args.db_create:
        logger.info(_("Create database and roles"))
        manage_pg.create_database()

    if args.db_migrate:
        logger.info(_("Migrating database to current version"))
        migrate(cfg, sql_quiet, client_min_message)

    if args.json_tables_create:
        logger.info(_("Create, if not exists, json tables"))
        manage_pg.create_json_tables()

    if args.col_tables_create:
        logger.info(_("Creating or recreating vn columns based tables"))
        col_table_create(
            db_host=settings.database.db_host,
            db_port=settings.database.db_port,
            db_name=settings.database.db_name,
            db_user=settings.database.db_user,
            db_pw=settings.database.db_pw,
            db_schema_import=settings.database.db_schema_import,
            db_schema_vn=settings.database.db_schema_vn,
            db_group=settings.database.db_group,
            db_out_proj=settings.database.db_out_proj,
            sql_quiet=sql_quiet,
            client_min_message=client_min_message,
        )

    if args.full:
        logger.info(_("Performing a full download"))
        full_download(settings)
        logger.info(_("Finished full download"))

    if args.schedule:
        logger.info(_("Creating or modifying incremental download schedule"))
        increment_schedule(settings)

    if args.update:
        logger.info(_("Performing an incremental download"))
        increment_download(settings)

    if args.status:
        logger.info(_("Printing download status"))
        status(settings)

    # if args.count:
    #     logger.info(_("Counting observations"))
    #     count_observations(cfg_ctrl)

    # Stop and output profiling if required
    if args.profile:
        logger.info(_("Printing yappi results"))
        yappi.stop()
        yappi.get_func_stats().print_all()
        yappi.get_thread_stats().print_all()

    return None


def run() -> None:
    """Entry point for console_scripts."""
    main(sys.argv[1:])


# Main wrapper
if __name__ == "__main__":
    run()
