import json
import pathlib

from typing import TypeVar, Type, Generic

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


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


class ModelKeyValueStore(KeyValueStore, Generic[T]):
    type: Type[T]

    def __init__(
        self,
        name: str,
        save_dir: pathlib.Path,
        model: Type[T],
    ) -> None:
        super().__init__(name, save_dir)

        self.type = model

    def get(self, key: str) -> T | None:
        value = super().get(key)
        if value:
            return self.type.model_validate_json(value)
        return None

    def set(self, key: str, value: T) -> None:
        super().set(key=key, value=value.model_dump_json())
