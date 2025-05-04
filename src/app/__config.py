import os

from dotenv import load_dotenv

from pydantic import BaseModel


class Config(BaseModel):
    APP_TITLE: str

    @staticmethod
    def from_env(dotenv_path: str = "settings.env") -> "Config":
        load_dotenv(dotenv_path)
        return Config.model_validate(os.environ)
