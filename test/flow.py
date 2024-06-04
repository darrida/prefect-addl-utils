from __future__ import annotations

from httpx import get
from prefect import flow, get_run_logger


@flow
def main():
    logger = get_run_logger()
    logger.info("Flow ran successfully!")
