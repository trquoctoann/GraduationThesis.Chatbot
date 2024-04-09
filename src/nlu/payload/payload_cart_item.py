import json


class PayloadCartItem:
    def __init__(
        self,
        pizza: str,
        quantity: int,
        size: str,
        crust: str,
        topping: list,
    ):
        self.pizza = pizza
        self.quantity = quantity
        self.size = size
        self.crust = crust
        self.topping = topping

    def __str__(self):
        return f"CartItem:\nPizza: {self.pizza}\nQuantity: {self.quantity}\nSize: {self.size}\nCrust: {self.crust}\nTopping: {self.topping}"

    def to_json(self):
        return json.dumps(
            {
                "pizza": self.pizza,
                "quantity": self.quantity,
                "size": self.size,
                "crust": self.crust,
                "topping": self.topping,
            },
            ensure_ascii=False,
        )
