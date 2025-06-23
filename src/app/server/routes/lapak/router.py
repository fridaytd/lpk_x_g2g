from fastapi import APIRouter

from .models import ProductCallbackPayload, OrderCallbackPayload
from . import logger

router = APIRouter(
    prefix="/lpk",
    tags=[
        "Lapak",
    ],
)


@router.post("/product")
async def product_callback(payload: ProductCallbackPayload) -> dict:
    logger.info(payload.model_dump_json())
    return {
        "message": "SUCCESS",
    }


@router.post("/order")
async def order_callback(payload: OrderCallbackPayload) -> dict:
    logger.info(payload.model_dump_json())
    return {
        "message": "SUCCESS",
    }
