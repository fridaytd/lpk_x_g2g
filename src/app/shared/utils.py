import json
import pathlib
import time
from datetime import datetime

from app import logger

from ..paths import DATA_PATH


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


def load_product_mapping() -> dict:
    with open(DATA_PATH / "product_mapping.json") as f:
        return json.load(f)


class KeyValueStore:
    def __init__(self, name: str, save_dir: pathlib.Path) -> None:
        self.name: str = name
        self.save_dir: pathlib.Path = save_dir
        self.data: dict[str, str] = {}

        save_file = self.get_save_file()
        if save_file.exists():
            self.load_data()
        else:
            self.write_data()

    def get_save_file(self) -> pathlib.Path:
        return self.save_dir / f"{self.name}.json"

    def load_data(self) -> None:
        with open(self.get_save_file()) as f:
            self.data = json.load(f)

    def write_data(self) -> None:
        with open(self.get_save_file(), "w") as f:
            json.dump(self.data, f)

    def get(self, key: str) -> str | None:
        self.load_data()
        return self.data.get(key)

    def set(self, key: str, value: str) -> None:
        self.data[key] = value
        self.write_data()

    def update(self, key: str, value: str) -> None:
        self.set(key, value)

    def delete(self, key: str) -> None:
        del self.data[key]
        self.write_data()
