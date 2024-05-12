import json

from nlu.payload.response.response_payload_stock_item import (
    ResponsePayloadStockItem,
)


class ResponsePayloadOptionDetail:
    def __init__(
        self, id: int, name: str, size: str, stock_items: set[ResponsePayloadStockItem]
    ):
        self.id = id
        self.name = name
        self.size = size
        self.stock_items = stock_items

    def to_json(self):
        return json.dumps(
            {
                "id": self.id,
                "name": self.name,
                "size": self.size,
                "stockItems": self.stock_items,
            },
            ensure_ascii=False,
        )
