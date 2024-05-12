import json


class RequestPayloadCartItem:
    def __init__(
        self,
        id: int,
        quantity: int,
        cart_id: int,
        product_id: int,
        option_detail_ids: set[int],
    ):
        self.id = id
        self.quantity = quantity
        self.cart_id = cart_id
        self.product_id = product_id
        self.option_detail_ids = option_detail_ids

    def to_json(self):
        return json.dumps(
            {
                "id": self.id,
                "quantity": self.quantity,
                "cartId": self.cart_id,
                "productId": self.product_id,
                "optionDetailIds": self.option_detail_ids,
            },
            ensure_ascii=False,
        )
