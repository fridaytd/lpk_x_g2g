from .models import APIDeliveryPayload
from ....sheet.models import LogToSheet


def api_delivery_hanlder(
    payload: APIDeliveryPayload,
):
    LogToSheet.write_log(payload.model_dump_json())

    return {"message": "ok"}
