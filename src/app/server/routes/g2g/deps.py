from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app import config

from . import logger
from .utils import generate_signature


def verify_signature(
    g2g_signature: Annotated[str, Header()],
    g2g_timestamp: Annotated[str, Header()],
) -> None:
    logger.info(g2g_signature)
    logger.info(g2g_timestamp)

    signature = generate_signature(
        config.G2G_WEBHOOK_URL,
        user_id=config.G2G_ACCOUNT_ID,
        timestamp=g2g_timestamp,
        secret_token=config.G2G_WEBHOOOK_SECRET_TOKEN,
    )

    if signature != g2g_signature:
        logger.error("Can't verify signature")
        raise HTTPException(status_code=401, detail="Can't verify signature")


VerifySignatureDep = Annotated[None, Depends(verify_signature)]
