import os

from dotenv import load_dotenv

from pydantic import BaseModel


class Config(BaseModel):
    APP_TITLE: str

    # Keys
    KEYS_PATH: str

    # Sheets
    SHEET_ID: str
    SHEET_NAME: str
    MAPPING_SHEET_NAME: str

    # Log sheets
    LOG_SHEET_ID: str
    LOG_SHEET_NAME: str

    # G2G KEYS
    G2G_ACCOUNT_ID: str
    G2G_API_KEY: str
    G2G_SECRET_KEY: str
    G2G_WEBHOOOK_SECRET_TOKEN: str
    G2G_WEBHOOK_URL: str

    # Lapak API key
    LAPAK_API_KEY: str

    @staticmethod
    def from_env(dotenv_path: str = "settings.env") -> "Config":
        load_dotenv(dotenv_path)
        return Config.model_validate(os.environ)
