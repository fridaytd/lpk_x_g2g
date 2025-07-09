from pydantic import BaseModel


class StoreModel(BaseModel):
    order_id: str
    delivery_id: str
    quantity: int
