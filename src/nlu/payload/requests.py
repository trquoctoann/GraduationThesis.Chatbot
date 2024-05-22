import json


class RequestPayloadCartItem:
    def __init__(
        self,
        quantity: int,
        cart_id: int,
        product_id: int,
        option_detail_ids: set[int],
        id: int = None,
    ):
        self.quantity = quantity
        self.cart_id = cart_id
        self.product_id = product_id
        self.option_detail_ids = option_detail_ids
        self.id = id

    def to_dict(self):
        return {
            "quantity": self.quantity,
            "cartId": self.cart_id,
            "productId": self.product_id,
            "optionDetailIds": list(self.option_detail_ids),
            "id": self.id,
        }
