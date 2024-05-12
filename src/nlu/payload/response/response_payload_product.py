import json

from nlu.payload.response.response_payload_option import ResponsePayloadOption
from nlu.payload.response.response_payload_option_detail import (
    ResponsePayloadOptionDetail,
)
from nlu.payload.response.response_payload_stock_item import (
    ResponsePayloadStockItem,
)


class ResponsePayloadProduct:
    def __init__(
        self,
        id: int,
        name: str,
        size: str,
        description: str,
        image_path: str,
        options: set[ResponsePayloadOption],
        option_details: set[ResponsePayloadOptionDetail],
        stock_items: set[ResponsePayloadStockItem],
    ):
        self.id = id
        self.name = name
        self.size = size
        self.description = description
        self.image_path = image_path
        self.options = options
        self.option_details = option_details
        self.stock_items = stock_items

    def to_json(self):
        return json.dumps(
            {
                "id": self.id,
                "name": self.name,
                "size": self.size,
                "description": self.description,
                "imagePath": self.image_path,
                "options": self.options,
                "optionDetails": self.option_details,
                "stockItems": self.stock_items,
            },
            ensure_ascii=False,
        )
