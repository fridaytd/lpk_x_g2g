import json

from app.server.utils import load_product_mapping_and_rates_from_sheet
from app import config

print(
    json.dumps(
        load_product_mapping_and_rates_from_sheet(
            config.SHEET_ID, config.MAPPING_SHEET_NAME, 2
        ),
    )
)
