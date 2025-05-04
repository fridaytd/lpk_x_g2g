from app.__config import Config

config = Config.from_env()

__all__ = ["config"]
