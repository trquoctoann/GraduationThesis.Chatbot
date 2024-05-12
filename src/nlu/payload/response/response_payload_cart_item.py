import json

from nlu.payload.response.response_payload_option_detail import (
    ResponsePayloadOptionDetail,
)


class ResponsePayloadCartItem:
    def __init__(
        self,
        id: int,
        quantity: int,
        price: float,
        option_details: set[ResponsePayloadOptionDetail],
    ):
        self.id = id
        self.quantity = quantity
        self.price = price
        self.option_details = option_details

    def to_json(self):
        return json.dumps(
            {
                "id": self.id,
                "quantity": self.quantity,
                "price": self.price,
                "optionDetails": self.option_details,
            },
            ensure_ascii=False,
        )
