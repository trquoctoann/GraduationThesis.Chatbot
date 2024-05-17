import json


class RequestPayloadCartItem:
    def __init__(
        self,
        id: int,
        quantity: int,
        price: float,
        cart_id: int,
        product_id: int,
        option_detail_ids: set[int],
    ):
        self.id = id
        self.quantity = quantity
        self.price = price
        self.cart_id = cart_id
        self.product_id = product_id
        self.option_detail_ids = option_detail_ids

    def to_dict(self):
        return {
            "id": self.id,
            "quantity": self.quantity,
            "price": self.price,
            "cartId": self.cart_id,
            "productId": self.product_id,
            "optionDetailIds": list(self.option_detail_ids),
        }
