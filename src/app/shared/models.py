from pydantic import BaseModel


class StoreModel(BaseModel):
    order_id: str
    delivery_id: str
    quantity: int


class EliStoreModel(BaseModel):
    g2g_order_id: str
    eli_order_ids: list[str]
    delivery_id: str
    quantity: int
