from typing import TypedDict, TypeAlias
from enum import Enum


class EliProduct(TypedDict):
    game: str | None
    denom: str | None


class ProductMap(TypedDict):
    lapakgaming: str | None
    elitedias: EliProduct
    provider_mode: str | None


# Mapping following rule: dict[<G2G_product_ID>, dict[<attribute_group_id>, dict[<attribute_value_id>, ProductMap]]]
G2GProductMapping: TypeAlias = dict[str, dict[str, dict[str, ProductMap]]]


class ProviderMode(Enum):
    LAPAKGAMING = "lapakgaming"
    ELITEDIAS = "elitedias"
    AUTO = "auto"
