from datetime import datetime

from fastapi import APIRouter, BackgroundTasks

from .models import ProductCallbackPayload, OrderCallbackPayload
from . import logger
from .utiles import is_success_order
from ...background_tasks import check_lpk_order_status_cron_job

from app import kv_store
from app.shared.models import LpkStoreModel
from app.g2g.models import PatchDeliveryPayload
from app.g2g.api_client import g2g_api_client
from app.sheet.models import LogToSheet

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
async def order_callback(
    payload: OrderCallbackPayload, background_tasks: BackgroundTasks
) -> dict:
    tid = payload.data.tid
    mapped_order: LpkStoreModel | None = kv_store.get(tid)
    if mapped_order is None:
        return {
            "message": "SUCCESS",
        }
    if is_success_order(payload):
        g2g_api_client.patch_delivery_order(
            order_id=mapped_order.order_id,
            delivery_id=mapped_order.delivery_id,
            payload=PatchDeliveryPayload(
                delivered_qty=mapped_order.quantity,
                delivered_at=int(
                    datetime.now().timestamp(),
                ),
            ),
        )
        LogToSheet.note_delivery(
            mapped_order.log_index,
            f"Delivery success for order id: {mapped_order.order_id}",
        )
        kv_store.delete(tid)
    else:
        background_tasks.add_task(check_lpk_order_status_cron_job, tid)

    return {
        "message": "SUCCESS",
    }
