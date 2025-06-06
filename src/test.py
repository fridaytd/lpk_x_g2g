from app import config
from app.g2g.api_client import g2g_api_client
# from app.sheet.models import RowModel, BatchCellUpdatePayload

from app.lpk.api_client import lpk_api_client

# brands = g2g_api_client.get_brand(
#     service_id="90015a0f-3983-4953-8368-96ac181d9e92"
# ).payload.brand_list


# print(
#     g2g_api_client.get_product(
#         service_id="90015a0f-3983-4953-8368-96ac181d9e92",
#         brand_id="44d8846e-3777-4e8b-b932-98866e2389cb",
#     ).model_dump_json()
# )

# print(
#     g2g_api_client.get_attribute(
#         product_id="119b5f4f-1526-4056-b499-9ed51fedb98b"
#     ).payload.model_dump_json()
# )


print(lpk_api_client.get_all_products(country_code="sa"))
