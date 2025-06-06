import time
from datetime import datetime

from app import logger


def sleep_for(delay: float) -> None:
    logger.info(f"Sleep for {delay} seconds")
    time.sleep(delay)


def formated_datetime(
    now: datetime,
) -> str:
    formatted_date = now.strftime("%d/%m/%Y %H:%M:%S")
    return formatted_date
