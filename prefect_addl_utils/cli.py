from __future__ import annotations

import click


@click.group()
def cli():
    ...


@cli.command("list", help="Lists available databases to open.")
@click.option(
    "-p",
    "--parameters",
    "parameters",
    hidden=True,
    help="Update cloud deployment from local parameters",
)
@click.option(
    "-s",
    "--schedules",
    "schedules",
    hidden=True,
    help="Update cloud deployment from local schedules",
)
@click.option(
    "-t",
    "--tags",
    "tags",
    hidden=True,
    help="Update cloud deployment from local tags",
)
@click.option(
    "-a",
    "--all",
    "all",
    hidden=True,
    help="Update cloud deployment from local parameters",
)
@click.option("-t", "--test", "test", is_flag=True, hidden=True)
def keepass_list(test, input_password=None):
    ...