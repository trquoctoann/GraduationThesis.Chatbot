import json

from nlu.payload.response.response_payload_cart_item import (
    ResponsePayloadCartItem,
)


class ResponsePayloadCart:
    def __init__(self, id: int, cart_items: set[ResponsePayloadCartItem]):
        self.id = id
        self.cart_items = cart_items

    def to_json(self):
        return json.dumps(
            {
                "id": self.id,
                "cartItems": self.cart_items,
            },
            ensure_ascii=False,
        )
