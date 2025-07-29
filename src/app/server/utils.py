from app.sheet.models import G2GTopUpProduct
from .models import G2GProductMapping, ProductMap, EliProduct


def load_product_mapping_and_rates_from_sheet(
    sheet_id: str,
    sheet_name: str,
    start_row: int,
) -> tuple[G2GProductMapping, float, float]:
    all_g2g_top_up_products, IDR_to_USE_rate, SGD_to_USE_rate = (
        G2GTopUpProduct.get_all_from_sheet(
            sheet_id=sheet_id, sheet_name=sheet_name, start_row=start_row
        )
    )

    mapping_dict: dict[str, dict[str, dict[str, ProductMap]]] = {}

    for product in all_g2g_top_up_products:
        if product.product_id not in mapping_dict:
            mapping_dict[product.product_id] = {}

        if product.attribute_group_id not in mapping_dict[product.product_id]:
            mapping_dict[product.product_id][product.attribute_group_id] = {}

        __eli_product: EliProduct = {
            "game": product.eli_game,
            "denom": product.eli_denomination,
        }

        __product_map: ProductMap = {
            "lapakgaming": product.lapak_codes,
            "elitedias": __eli_product,
            "provider_mode": product.provider_mode,
        }

        # Use sub_attribute_id if exists
        if product.sub_attribute_id:
            mapping_dict[product.product_id][product.attribute_group_id][
                product.sub_attribute_id
            ] = __product_map

        # Use attribute_id if sub_attribute_id not exists
        elif product.attribute_id:
            mapping_dict[product.product_id][product.attribute_group_id][
                product.attribute_id
            ] = __product_map

    return mapping_dict, IDR_to_USE_rate, SGD_to_USE_rate
