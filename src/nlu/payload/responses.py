import json


class ResponsePayloadStockItem:
    def __init__(
        self,
        id: int,
        name: str,
        unit: str,
        total_quantity: int,
        selling_price: float,
        store_id: int,
        product_id: int,
    ):
        self.id = id
        self.name = name
        self.unit = unit
        self.total_quantity = total_quantity
        self.selling_price = selling_price
        self.store_id = store_id
        self.product_id = product_id

    def to_json(self):
        return json.dumps(
            {
                "id": self.id,
                "name": self.name,
                "unit": self.unit,
                "total_quantity": self.total_quantity,
                "sellingPrice": self.selling_price,
                "storeId": self.store_id,
                "productId": self.product_id,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(data):
        return ResponsePayloadStockItem(
            id=data["id"] if data["id"] else None,
            name=data["name"] if data["name"] else None,
            unit=data["unit"] if data["unit"] else None,
            total_quantity=data["totalQuantity"] if data["totalQuantity"] else None,
            selling_price=data["sellingPrice"] if data["sellingPrice"] else None,
            store_id=data["storeId"] if data["storeId"] else None,
            product_id=data["productId"] if data["productId"] else None,
        )


class ResponsePayloadOption:
    def __init__(self, id: int, name: str, is_multi: bool, is_required: bool):
        self.id = id
        self.name = name
        self.is_multi = is_multi
        self.is_required = is_required

    def to_json(self):
        return json.dumps(
            {
                "id": self.id,
                "name": self.name,
                "isMulti": self.is_multi,
                "isRequired": self.is_required,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(data):
        return ResponsePayloadOption(
            id=data["id"] if data["id"] else None,
            name=data["name"] if data["name"] else None,
            is_multi=data["isMulti"] if data["isMulti"] else None,
            is_required=data["isRequired"] if data["isRequired"] else None,
        )


class ResponsePayloadOptionDetail:
    def __init__(
        self,
        id: int,
        name: str,
        size: str,
        option_id: int,
        stock_items: set[ResponsePayloadStockItem],
    ):
        self.id = id
        self.name = name
        self.size = size
        self.option_id = option_id
        self.stock_items = stock_items

    def to_json(self):
        return json.dumps(
            {
                "id": self.id,
                "name": self.name,
                "size": self.size,
                "optionId": self.option_id,
                "stockItems": self.stock_items,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(data):
        return ResponsePayloadOptionDetail(
            id=data["id"] if data["id"] else None,
            name=data["name"] if data["name"] else None,
            size=data["size"] if data["size"] else None,
            option_id=data["optionId"] if data["optionId"] else None,
            stock_items=(
                [
                    ResponsePayloadStockItem.from_json(item)
                    for item in data.get("stockItems", [])
                ]
                if data.get("stockItems")
                else None
            ),
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

    @staticmethod
    def from_json(data):
        return ResponsePayloadProduct(
            id=data["id"] if data["id"] else None,
            name=data["name"] if data["name"] else None,
            size=data["size"] if data["size"] else None,
            description=data["description"] if data["description"] else None,
            image_path=data["imagePath"] if data["imagePath"] else None,
            options=(
                [
                    ResponsePayloadOption.from_json(item)
                    for item in data.get("options", [])
                ]
                if data.get("options")
                else None
            ),
            option_details=(
                [
                    ResponsePayloadOptionDetail.from_json(item)
                    for item in data.get("optionDetails", [])
                ]
                if data.get("optionDetails")
                else None
            ),
            stock_items=(
                [
                    ResponsePayloadStockItem.from_json(item)
                    for item in data.get("stockItems", [])
                ]
                if data.get("stockItems")
                else None
            ),
        )


class ResponsePayloadCartItem:
    def __init__(
        self,
        id: int,
        quantity: int,
        price: float,
        product: ResponsePayloadProduct,
        option_details: set[ResponsePayloadOptionDetail],
    ):
        self.id = id
        self.quantity = quantity
        self.price = price
        self.product = product
        self.option_details = option_details

    def to_json(self):
        return json.dumps(
            {
                "id": self.id,
                "quantity": self.quantity,
                "price": self.price,
                "product": self.product,
                "optionDetails": self.option_details,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(data):
        return ResponsePayloadCartItem(
            id=data["id"] if data["id"] else None,
            quantity=data["quantity"] if data["quantity"] else None,
            price=data["price"] if data["price"] else None,
            product=ResponsePayloadProduct.from_json(data["product"])
            if data["product"]
            else None,
            option_details=(
                [
                    ResponsePayloadOptionDetail.from_json(item)
                    for item in data.get("optionDetails", [])
                ]
                if data.get("optionDetails")
                else []
            ),
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

    @staticmethod
    def from_json(data):
        return ResponsePayloadCart(
            id=data["id"] if data["id"] else None,
            cart_items=(
                [
                    ResponsePayloadCartItem.from_json(item)
                    for item in data.get("cartItems", [])
                ]
                if data.get("cartItems")
                else None
            ),
        )
