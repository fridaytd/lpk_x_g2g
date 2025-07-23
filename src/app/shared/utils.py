import asyncio

import json
from typing import Awaitable, Callable, TypeVar, ParamSpec


import time
from datetime import datetime

from app import logger

from ..paths import DATA_PATH

T_Rt = TypeVar("T_Rt")
T_Pr = ParamSpec("T_Pr")


def sleep_for(delay: float) -> None:
    logger.info(f"Sleep for {delay} seconds")
    time.sleep(delay)


def formated_datetime(
    now: datetime,
) -> str:
    formatted_date = now.strftime("%d/%m/%Y %H:%M:%S")
    return formatted_date


def split_list(lst: list, chunk_size: int) -> list[list]:
    """
    Split a list into smaller chunks of specified size

    Args:
        lst (list): Input list to split
        chunk_size (int): Size of each chunk

    Returns:
        list: List containing sublists of specified chunk size
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def load_delivery_method_list_mapping() -> dict:
    with open(DATA_PATH / "delivery_method_list_mapping.json") as f:
        return json.load(f)


def load_eli_delivery_method_list_mapping() -> dict:
    with open(DATA_PATH / "eli_delivery_method_list_mapping.json") as f:
        return json.load(f)


def load_eli_product_mapping() -> dict[str, dict[str, dict[str, dict[str, str]]]]:
    with open(DATA_PATH / "eli_product_mapping.json") as f:
        return json.load(f)


def afunc_retry(
    afunc: Callable[T_Pr, Awaitable[T_Rt]],
    max_retry: int = 3,
    sleep_interval: float = 1,
) -> Callable[T_Pr, Awaitable[T_Rt]]:
    async def wrapper(*args: T_Pr.args, **kwargs: T_Pr.kwargs) -> T_Rt:
        retry_time: int = 0
        while retry_time <= max_retry:
            try:
                return await afunc(*args, **kwargs)
            except Exception as e:
                logger.error(f"Retried: {retry_time} time(s). Error: {e}")
                if retry_time == max_retry:
                    raise e
            finally:
                retry_time += 1
                await asyncio.sleep(sleep_interval)

        raise

    return wrapper
