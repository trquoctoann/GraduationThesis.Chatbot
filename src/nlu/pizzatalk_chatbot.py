import difflib
import json
import random

import requests
import torch

from models.entities.entities_recognizer import EntitiesRecognizer
from models.intents.intents_recognizer import IntentsRecognizer
from models.utils.preprocessing import preprocessing
from nlu.payload.requests import RequestPayloadCartItem
from nlu.payload.responses import (
    ResponsePayloadCart,
    ResponsePayloadCartItem,
    ResponsePayloadOption,
    ResponsePayloadOptionDetail,
    ResponsePayloadProduct,
    ResponsePayloadStockItem,
)
from utils.api_url import APIUrls
from utils.correct_entity_name import (
    get_correct_crust_type,
    get_correct_pizza_name,
    get_correct_size,
    get_correct_topping_name,
    get_quantity_in_number,
)

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")


class PizzaTalkChatbot:
    def __init__(
        self,
        model_entity_path: str,
        model_intent_path: str,
        responses_template_path: str,
    ):
        self.model_order_entity = self._load_model_entity(model_entity_path, True)
        self.model_customer_entity = self._load_model_entity(model_entity_path, False)
        self.model_intent = self._load_model_intent(model_intent_path)
        self.responses_template = self._load_response_template(responses_template_path)

    def _load_model_entity(self, model_path: str, is_order: bool) -> EntitiesRecognizer:
        model = EntitiesRecognizer(model_path, is_order)
        return model

    def _load_model_intent(self, model_path: str) -> IntentsRecognizer:
        model = IntentsRecognizer()
        model.load_state_dict(torch.load(model_path))
        return model.to(device)

    def _load_response_template(self, responses_template_path: str) -> dict:
        with open(responses_template_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def identify_intent(self, message: str) -> dict:
        return self.model_intent.predict(preprocessing(message))

    def identify_order_entities(self, message: str) -> dict:
        return self.model_order_entity.predict(preprocessing(message, True))

    def identify_customer_entities(self, message: str) -> str:
        return self.model_customer_entity.predict(preprocessing(message, True))

    def get_specified_pizza(
        self, pizza_name: str, size: str = None
    ) -> ResponsePayloadProduct:
        request_url = (
            APIUrls.PRODUCT_SERVICE.value + f"&name.contains=pizza {pizza_name}"
        )
        if size:
            request_url += "&size.equals=" + size.upper()
        response = requests.get(request_url)

        if response.status_code == 200 and response.json():
            return ResponsePayloadProduct.from_json(response.json()[0])
        return None

    def get_full_menu_pizza(self) -> list[ResponsePayloadProduct]:
        response = requests.get(APIUrls.PRODUCT_SERVICE.value)
        if response.status_code == 200 and response.json():
            return [
                ResponsePayloadProduct.from_json(pizza)
                for pizza in response.json()
                if not pizza["size"]
            ]
        return []

    def get_active_cart(self, user_id: int) -> ResponsePayloadCart:
        response = requests.get(
            APIUrls.CART_SERVICE.value
            + f"?userId.equals={str(user_id)}&status.equals=ACTIVE"
        )
        if response.status_code == 200 and response.json():
            return ResponsePayloadCart.from_json(response.json()[0])
        return None

    def get_full_topping(self, size: str) -> list[ResponsePayloadOptionDetail]:
        response = requests.get(
            APIUrls.OPTION_DETAIL_SERVICE.value
            + f"?optionId.equals=2&size.equals={size}"
        )
        if response.status_code == 200 and response.json():
            return [
                ResponsePayloadOptionDetail.from_json(topping)
                for topping in response.json()
            ]
        return []

    def get_all_cart_items(self, cart_id: int) -> list[ResponsePayloadCartItem]:
        response = requests.get(
            APIUrls.CART_ITEM_SERVICE.value + f"/all?cartId.equals={cart_id}"
        )
        if response.status_code == 200 and response.json():
            return [
                ResponsePayloadCartItem.from_json(cart_item)
                for cart_item in response.json()
            ]
        return None

    def throw_request_error(self, endpoint_name: str) -> dict:
        return {"error": f"Hệ thống xảy ra lỗi khi tải thông tin {endpoint_name}"}

    def format_pizza_response(self, pizza_info: ResponsePayloadProduct) -> str:
        price, quantity = 0, 0
        for stock_item in pizza_info.stock_items:
            if stock_item.store_id == 1 and stock_item.product_id == pizza_info.id:
                price, quantity = stock_item.selling_price, stock_item.total_quantity
                break
        details = {
            "Mô tả": pizza_info.description,
            "Giá cả": str(price) + " ₫",
            "Số lượng còn lại": quantity,
            "Các loại đế bánh": ", ".join(
                [od.name for od in pizza_info.option_details if od.option_id == 1]
            ),
            "Topping có thể thêm": ", ".join(
                [od.name for od in pizza_info.option_details if od.option_id == 2]
            ),
        }
        details_response = "\n".join(
            [f"{key}: {value}" for key, value in details.items()]
        )
        return details_response

    def format_cart_item_response(self, cart_item_info: ResponsePayloadCartItem) -> str:
        details = {
            "Tên món": cart_item_info.product.name.lower().title(),
            "Số lượng": cart_item_info.quantity,
            "Size": cart_item_info.product.size,
            "Đế bánh": ", ".join(
                [od.name for od in cart_item_info.option_details if od.option_id == 1]
            ),
            "Topping": ", ".join(
                [od.name for od in cart_item_info.option_details if od.option_id == 2]
            ),
            "Giá cả": str(cart_item_info.price) + " ₫",
        }
        details_response = "\n".join(
            [f"{key}: {value}" for key, value in details.items()]
        )
        return details_response

    def announce_invalid_pizza(self, list_invalid_pizza: list):
        return random.choice(self.responses_template["wrong_name_pizza"]).format(
            pizza_name=", ".join(list_invalid_pizza)
        )

    def annouce_invalid_option(
        self, pizza: str, option_type: str, list_invalid_option: list
    ):
        if option_type == "size":
            return random.choice(self.responses_template["wrong_size_pizza"]).format(
                pizza_name=pizza, size=", ".join(list_invalid_option)
            )
        elif option_type == "crust":
            return random.choice(self.responses_template["wrong_crust_pizza"]).format(
                pizza_name=pizza, size=", ".join(list_invalid_option)
            )
        elif option_type == "topping":
            return random.choice(self.responses_template["wrong_topping_pizza"]).format(
                pizza_name=pizza, size=", ".join(list_invalid_option)
            )

    def clean_recognized_entities(self, entities: dict) -> dict:
        for key, value in entities.items():
            entities[key] = [name[0] for name in value]

        if "Pizza" in entities:
            correct_pizzas, wrong_pizzas = get_correct_pizza_name(entities["Pizza"])
            if wrong_pizzas:
                return self.announce_invalid_pizza(wrong_pizzas)
            entities["Pizza"] = correct_pizzas

        if "Size" in entities:
            entities["Size"] = get_correct_size(entities["Size"])[0]

        if "Quantity" in entities:
            entities["Quantity"] = get_quantity_in_number(entities["Quantity"])

        if "Topping" in entities:
            entities["Topping"] = get_correct_topping_name(entities["Topping"])[0]

        if "Crust" in entities:
            entities["Crust"] = get_correct_crust_type(entities["Crust"])[0]

        return entities

    def handle_view_menu(self, message: str) -> str:
        entities = self.identify_order_entities(message)
        cleaned_entities = self.clean_recognized_entities(entities)

        if "Pizza" in entities:
            pizza = cleaned_entities["Pizza"][0]
            size = cleaned_entities["Size"][0] if "Size" in entities else "l"

            pizza_info = self.get_specified_pizza(pizza, size)
            if not pizza_info:
                return self.throw_request_error("pizza")["error"]

            response = random.choice(
                self.responses_template["view_menu"][
                    "Pizza_Size" if "Size" in cleaned_entities else "Pizza"
                ]
            ).format(pizza_name=pizza_info.name.lower().title(), size=pizza_info.size)
            return f"{response}\n{self.format_pizza_response(pizza_info)}"
        else:
            full_menu_pizza = self.get_full_menu_pizza()
            if not full_menu_pizza:
                return self.throw_request_error("pizza")["error"]

            response = random.choice(self.responses_template["view_menu"]["unknown"])
            menu_details = "\n".join(
                [
                    f" - {item.name.lower().title()}. Mô tả: {item.description}"
                    for item in full_menu_pizza
                ]
            )
            return f"{response}\n{menu_details}"

    def handle_view_cart(self, message):
        entities = self.identify_order_entities(message)
        cleaned_entities = self.clean_recognized_entities(entities)

        cart_info = self.get_active_cart(user_id=1)
        cart_items = self.get_all_cart_items(cart_id=cart_info.id)
        if "Pizza" in entities:
            pizzas = entities["Pizza"]

            for cart_item in cart_items:
                if (
                    cart_item.product.name.lower().replace("pizza ", "")
                    == pizzas[0].strip()
                ):
                    response = random.choice(
                        self.responses_template["view_cart"]["Pizza"]["exist"]
                    ).format(pizza_name=pizzas[0])
                    return f"{response}\n{self.format_cart_item_response(cart_item)}"

            return random.choice(
                self.responses_template["view_cart"]["Pizza"]["nonexist"]
            ).format(pizza_name=pizzas[0])
        else:
            response = random.choice(self.responses_template["view_cart"]["unknown"])
            cart_details = "\n".join(
                [
                    f" - {cart_item.quantity} {cart_item.product.name.lower().title()}"
                    for cart_item in cart_items
                ]
            )
            return f"{response}\n{cart_details}"

    def _process_single_pizza(self, entities: dict) -> dict:
        cart_item = {"Pizza": entities["Pizza"][0]}

        if "Quantity" in entities:
            cart_item["Quantity"] = int(entities["Quantity"][0])
        if "Size" in entities:
            cart_item["Size"] = [size for size in entities["Size"]]
        if "Topping" in entities:
            cart_item["Topping"] = [topping for topping in entities["Topping"]]

        return cart_item

    def _build_cart_items_detail(self, message: str) -> list:
        entities = self.identify_order_entities(message)
        cleaned_entities = self.clean_recognized_entities(entities)
        number_of_pizza_types = len(cleaned_entities["Pizza"])
        number_of_quantity = len(cleaned_entities["Quantity"])
        if (
            number_of_pizza_types == 1
            and number_of_quantity == 1
            and cleaned_entities["Quantity"][0] == 1
        ):
            return [self._process_single_pizza(cleaned_entities)]
        elif number_of_pizza_types == 1:
            pass
        return []

    def get_topping_ids(
        self, pizza_info: ResponsePayloadProduct, toppings_list: list
    ) -> list:
        topping_ids = []
        for option_detail in pizza_info.option_details:
            if (
                option_detail.option_id == 2
                and option_detail.name.lower() in toppings_list
            ):
                topping_ids.append(option_detail.id)
        return topping_ids

    def post_cart_item(self, cart_item: RequestPayloadCartItem) -> None:
        response = requests.post(
            APIUrls.CART_ITEM_SERVICE.value, json=cart_item.to_dict()
        )

    def handle_add_to_cart(self, message: str) -> str:
        cart = self.get_active_cart(1)
        cart_items = self._build_cart_items_detail(message)
        for cart_item in cart_items:
            pizza_info = self.get_specified_pizza(
                cart_item["Pizza"], cart_item["Size"][0]
            )
            cart_item_dto = RequestPayloadCartItem(
                id=None,
                price=100000,
                quantity=cart_item.get("Quantity", 1),
                cart_id=cart.id,
                product_id=pizza_info.id,
                option_detail_ids=self.get_topping_ids(
                    pizza_info, cart_item.get("Topping", [])
                ),
            )
            self.post_cart_item(cart_item_dto)

    def handle_remove_from_cart(self, message):
        entities = self.identify_order_entities(message)
        pass

    def handle_modify_cart_item(self, message):
        pass

    def handle_confirm_order(self, message):
        pass

    def handle_track_order(self, message):
        pass

    def handle_cancel_order(self, message):
        pass

    def handle_provide_info(self, message):
        pass

    def handle_message(self, message):
        message_intent = self.identify_intent(message)
        if message_intent == "view_menu":
            return self.handle_view_menu(message)
        elif message_intent == "view_cart":
            return self.handle_view_cart(message)
        elif message_intent == "add_to_cart":
            return self.handle_add_to_cart(message)
        elif message_intent == "remove_from_cart":
            return self.handle_remove_from_cart(message)
        elif message_intent == "modify_cart_item":
            return self.handle_modify_cart_item(message)
        elif message_intent == "confirm_order":
            return self.handle_confirm_order(message)
        elif message_intent == "track_order":
            return self.handle_track_order(message)
        elif message_intent == "cancel_order":
            return self.handle_cancel_order(message)
        elif message_intent == "provide_info":
            return self.handle_provide_info(message)
        else:
            return random.choice(self.responses_template["unknown"])
