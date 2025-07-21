from app.sheet.models import G2GTopUpProduct


def load_product_mapping_from_sheet(
    sheet_id: str,
    sheet_name: str,
    start_row: int,
) -> dict[str, dict[str, dict[str, str]]]:
    all_g2g_top_up_products = G2GTopUpProduct.get_all_from_sheet(
        sheet_id=sheet_id, sheet_name=sheet_name, start_row=start_row
    )

    mapping_dict: dict[str, dict[str, dict[str, str]]] = {}

    for product in all_g2g_top_up_products:
        if product.lapak_code:
            if product.product_id not in mapping_dict:
                mapping_dict[product.product_id] = {}

            if product.attribute_group_id not in mapping_dict[product.product_id]:
                mapping_dict[product.product_id][product.attribute_group_id] = {}

            if product.sub_attribute_id:
                mapping_dict[product.product_id][product.attribute_group_id][
                    product.sub_attribute_id
                ] = product.lapak_code

            elif product.attribute_id:
                mapping_dict[product.product_id][product.attribute_group_id][
                    product.attribute_id
                ] = product.lapak_code

    return mapping_dict
