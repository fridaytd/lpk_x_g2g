from app.server.routes.g2g.models import APIDeliveryPayload
from app.server.routes.g2g.handlers import api_delivery_hanlder
from app.g2g.api_client import g2g_api_client

from app.g2g.models import PatchDeliveryPayload, DeliveryCode
from app import kv_store
from app.shared.models import StoreModel

from app.lpk.api_client import lpk_api_client

payload = {
    "order_id": "1751809522083S48T-1",
    "seller_id": "3275359",
    "buyer_id": "1000289630",
    "offer_id": "G1751791278525FI",
    "purchased_qty": 1,
    "defected_qty": 0,
    "replacement_qty": 0,
    "refunded_qty": 0,
    "undelivered_qty": 1,
    "delivered_qty": 0,
    "delivery_summary": {
        "delivery_id": "D1751809602774",
        "delivery_mode": "normal",
        "case_id": "",
        "requested_qty": 1,
        "delivery_method_code": "direct_top_up",
        "requested_at": 1751809602774,
        "delivery_method_list": [
            {
                "attribute_group_id": "a488b0e9",
                "attribute_group_name": "UID",
                "value": "800322607",
                "attribute_key": "delivery_info_1",
            },
            {
                "attribute_group_id": "20c73c0f",
                "attribute_group_name": "Server",
                "attribute_id": "9a5c03c7",
                "attribute_value": "Asia",
                "attribute_key": "delivery_info_2",
            },
        ],
        "additional_info_list": [],
    },
}


# print(APIDeliveryPayload.model_validate(payload))

# api_delivery_hanlder(APIDeliveryPayload.model_validate(payload))

# print(
#     g2g_api_client.patch_delivery_order(
#         order_id="1751809522083S48T-1",
#         delivery_id="D1751809602774",
#         payload=PatchDeliveryPayload(
#             delivered_qty=1,
#             delivered_at=1751827618,
#         ),
#     ).model_dump_json()
# )

# print(
#     g2g_api_client.delivery_order_codes(
#         order_id="1751809522083S48T-1",
#         delivery_id="D1751809602774",
#         codes=[DeliveryCode(content="", reference_id="RA175181653476092092")],
#     )
# )

# print(g2g_api_client.get_offer("G1751791278525FI").model_dump_json())

# print(g2g_api_client.get_order("1751809522083S48T-1"))
# print(g2g_api_client.get_order_deliveries("1751809522083S48T-1"))

# kv_store.set("test", "test")

# print(lpk_api_client.get_order_status("RA175181653476092092"))

# kv_store.set("test", value=StoreModel(order_id="hihi", delivery_id="hihi"))
# print(kv_store.get("test"))


print(lpk_api_client.get_fx_rate())
