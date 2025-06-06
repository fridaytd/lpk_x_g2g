import pathlib

import logging
from app import config


def get_logger(
    name: str | None = None,
    level: int | str = logging.INFO,
    is_log_file: bool = False,
) -> logging.Logger:
    logger = logging.getLogger(name=name)
    logger.setLevel(level)

    handler = logging.StreamHandler()
    formater = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s :: %(message)s"
    )

    handler.setFormatter(formater)

    logger.addHandler(handler)

    if is_log_file:
        file_handler = logging.FileHandler(
            filename=pathlib.Path(__file__)
            .parent.parent.parent.joinpath("logs")
            .joinpath(config.LOG_FILE_NAME),
            mode="a",
            encoding="utf-8",
        )
        file_handler.setFormatter(formater)
        logger.addHandler(file_handler)

    return logger
