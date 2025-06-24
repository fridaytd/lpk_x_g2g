from fastapi import APIRouter


from . import logger
from .deps import VerifySignatureDep
from .models import OrderEvent, APIDeliveryPayload
from .enums import OrderEventType
from .handlers import api_delivery_hanlder

router = APIRouter(
    prefix="/g2g",
    tags=["G2G"],
)


@router.get("")
async def hello_from_g2g() -> str:
    return "Hello from G2G webhook"


@router.post("")
async def webhook(order_event: OrderEvent, _: VerifySignatureDep):
    match order_event.event_type:
        case OrderEventType.ORDER_API_DELIVERY:
            payload = APIDeliveryPayload.model_validate(order_event.payload)
            return api_delivery_hanlder(payload)
        case _:
            logger.info(order_event.model_dump_json())
            return


# @router.post("")
# async def webhook(order_event: OrderEvent):
#     match order_event.event_type:
#         case OrderEventType.ORDER_API_DELIVERY:
#             payload = APIDeliveryPayload.model_validate(order_event.payload)
#             return api_delivery_hanlder(payload)
#         case _:
#             logger.info(order_event.model_dump_json())
#             return
