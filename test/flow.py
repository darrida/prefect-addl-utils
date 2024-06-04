from __future__ import annotations

from prefect import flow, get_run_logger
from pydantic.v1 import BaseModel


class Parameters(BaseModel):
    test_mode: bool = False
    username: str = "user1"
    host: str = "host1"
    loop_sleep_ms: int = 600


@flow(name="test-flow2")
def main(test_mode: bool, username: str, host: str, loop_sleep_ms: int):
    logger = get_run_logger()
    logger.info("Flow ran successfully!")
    logger.info(f"test_mode={test_mode}")
    logger.info(f"username={username}")
    logger.info(f"host={host}")
    logger.info(f"loop_sleep_ms={loop_sleep_ms}")


if __name__ == "__main__":
    main(**Parameters().dict())
