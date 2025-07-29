from pydantic import BaseModel


class LpkStoreModel(BaseModel):
    order_id: str
    delivery_id: str
    quantity: int
    log_index: int


class EliStoreModel(BaseModel):
    g2g_order_id: str
    eli_order_ids: list[str]
    delivery_id: str
    quantity: int
    log_index: int
