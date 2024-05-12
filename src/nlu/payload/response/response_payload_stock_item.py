import json


class ResponsePayloadStockItem:
    def __init__(
        self, id: int, name: str, unit: str, total_quantity: int, selling_price: float
    ):
        self.id = id
        self.name = name
        self.unit = unit
        self.total_quantity = total_quantity
        self.selling_price = selling_price

    def to_json(self):
        return json.dumps(
            {
                "id": self.id,
                "name": self.name,
                "unit": self.unit,
                "total_quantity": self.total_quantity,
                "sellingPrice": self.selling_price,
            },
            ensure_ascii=False,
        )
