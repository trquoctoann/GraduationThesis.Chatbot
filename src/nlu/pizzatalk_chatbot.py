import json
import random

import requests
import torch

from models.utils.preprocessing import preprocessing
from models.entities.entities_recognizer import EntitiesRecognizer
from models.intents.intents_recognizer import IntentsRecognizer
from nlu.payload.requests import RequestPayloadCartItem
from nlu.payload.responses import (
    ResponsePayloadCart,
    ResponsePayloadCartItem,
    ResponsePayloadOption,
    ResponsePayloadOptionDetail,
    ResponsePayloadProduct,
    ResponsePayloadStockItem,
)
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

    def identify_order_entities(self, message: str) -> str:
        return self.model_order_entity.predict(preprocessing(message, True))

    def identify_customer_entities(self, message: str) -> str:
        return self.model_customer_entity.predict(preprocessing(message, True))

    #     if intent == "add_to_cart":
    #         try:
    #             verify_product_name(detected_entity)
    #         except InvalidProductName as e:
    #             if e.message == "Invalid pizza":
    #                 return "Xin lỗi. Cửa hàng chúng mình không có pizza " + e.product_name + " ạ"
    #             elif e.message == "Invalid size":
    #                 return "Xin lỗi. Cửa hàng chúng mình chỉ phục vụ pizza cỡ S, X, XL thôi ạ"
    #             elif e.message == "Invalid crust":
    #                 return "Xin lỗi. Cửa hàng chúng mình chỉ phục vụ pizza có đế mỏng hoặc dày thôi ạ"

    #         missing_entities = [
    #             key
    #             for key in ["Pizza", "Quantity", "Size", "Crust", "Topping"]
    #             if key not in detected_entity
    #         ]
    #         if not missing_entities:
    #             response = (
    #                 random.choice(self.responses_template[intent]["All"]["responses"])
    #                 .format(**{k: v for k, v in detected_entity.items()})
    #                 .replace("[pizza]", standardize_result(detected_entity["Pizza"][0]))
    #                 .replace("[quantity]", standardize_result(detected_entity["Quantity"][0]))
    #                 .replace("[size]", standardize_result(detected_entity["Size"][0]))
    #                 .replace("[crust]", standardize_result(detected_entity["Crust"][0]))
    #                 .replace(
    #                     "[topping]",
    #                     standardize_result(", ".join(detected_entity["Topping"])),
    #                 )
    #                 .title()
    #             )

    #         else:
    #             missing_details = ", ".join(
    #                 [
    #                     random.choice(
    #                         self.responses_template[intent][f"missing_{entity.lower()}"]["responses"]
    #                     )
    #                     for entity in missing_entities
    #                 ]
    #             )
    #             template = random.choice(
    #                 self.responses_template[intent]["missing_template"]["responses"]
    #             )
    #             response = template.replace("[missing_entity]", missing_details)
    #         return response

    #     if intent == "remove_from_cart":
    #         if "Pizza" in detected_entity and "Quantity" in detected_entity:
    #             return (
    #                 random.choice(self.responses_template[intent]["Pizza_Quantity"]["responses"])
    #                 .replace("[pizza]", standardize_result(detected_entity["Pizza"][0]))
    #                 .replace("[quantity]", standardize_result(detected_entity["Quantity"][0]))
    #             )
    #         elif "Pizza" in detected_entity:
    #             return random.choice(self.responses_template[intent]["Pizza"]["responses"]).replace(
    #                 "[pizza]", standardize_result(detected_entity["Pizza"][0])
    #             )

    def get_specified_pizza(self, pizza_name: str, size: str = None) -> dict:
        request_url = f"http://localhost:8082/api/products/all?categoryId.equals=1&name.contains=pizza {pizza_name}"
        if size:
            request_url += "&size.equals=" + size.upper()
        response = requests.get(request_url)

        if response.status_code == 200 and response.json():
            pizza_info = ResponsePayloadProduct.from_json(response.json()[0])
            price, quantity = 0, 0
            for stock_item in pizza_info.stock_items:
                if stock_item.store_id == 1 and stock_item.product_id == pizza_info.id:
                    price, quantity = stock_item.selling_price, stock_item.total_quantity
                    break
            return {
                "name": pizza_info.name.lower().title(),
                "description": pizza_info.description,
                "size": size,
                "crust": ", ".join([od.name for od in pizza_info.option_details if od.option_id == 1]),
                "toppings": ", ".join(
                    [od.name for od in pizza_info.option_details if od.option_id == 2]
                ),
                "price": price,
                "quantity": quantity,
            }
        else:
            return {"error": "Hệ thống xảy ra lỗi khi tải thông tin pizza."}

    def get_full_menu_pizza(self) -> list[ResponsePayloadProduct]:
        response = requests.get("http://localhost:8082/api/products/all?categoryId.equals=1")
        if response.status_code == 200 and response.json():
            return [
                ResponsePayloadProduct.from_json(pizza) for pizza in response.json() if not pizza["size"]
            ]
        else:
            return {"error": "Hệ thống xảy ra lỗi khi tải thông tin pizza."}

    def get_active_cart(self, user_id: int) -> ResponsePayloadCart:
        response = requests.get(
            f"http://localhost:8082/api/carts/all?userId.equals={str(user_id)}&status.equals=ACTIVE"
        )
        if response.status_code == 200 and response.json():
            return ResponsePayloadCart.from_json(response.json()[0])
        else:
            return {"error": "Hệ thống xảy ra lỗi khi tải thông tin giỏ hàng."}

    def get_full_topping(self, size: str) -> list[ResponsePayloadOptionDetail]:
        response = requests.get(
            f"http://localhost:8082/api/option-details/all?optionId.equals=2&size.equals={size}"
        )
        if response.status_code == 200 and response.json():
            return [ResponsePayloadOptionDetail.from_json(topping) for topping in response.json()]
        else:
            return {"error": "Hệ thống xảy ra lỗi khi tải thông tin giỏ hàng."}

    def format_pizza_response(self, pizza_info: dict) -> str:
        details = {
            "Mô tả": pizza_info["description"],
            "Giá cả": str(pizza_info["price"]) + " ₫",
            "Số lượng còn lại": pizza_info["quantity"],
            "Các loại đế bánh": pizza_info["crust"],
            "Topping có thể thêm": pizza_info["toppings"],
        }
        details_response = "\n".join([f"{key}: {value}" for key, value in details.items()])
        return details_response

    def format_cart_item_response(self, cart_item_info: str) -> str:
        details = {
            "Tên món": cart_item_info,
            "Số lượng": cart_item_info["quantity"],
            "Size": cart_item_info["size"],
            "Đế bánh": cart_item_info["crust"],
            "Topping": cart_item_info["toppings"],
            "Giá cả": str(cart_item_info["price"]) + " ₫",
        }
        details_response = "\n".join([f"{key}: {value}" for key, value in details.items()])
        return details_response

    def handle_view_menu(self, message: str) -> str:
        entities = self.identify_order_entities(message)
        if "Pizza" in entities:
            pizzas = entities["Pizza"]
            correct_pizzas, wrong_pizzas = get_correct_pizza_name(pizzas)
            if wrong_pizzas:
                return random.choice(self.responses_template["wrong_name_pizza"]).format(
                    pizza_name=", ".join(wrong_pizzas)
                )

            size = entities["Size"][0] if "Size" in entities else "l"
            correct_sizes, wrong_sizes = get_correct_size([size])
            if wrong_sizes:
                return random.choice(self.responses_template["wrong_size_pizza"]).format(
                    pizza_name=correct_pizzas[0], size=", ".join(wrong_sizes)
                )

            pizza_info = self.get_specified_pizza(correct_pizzas[0], correct_sizes[0])
            if "error" in pizza_info:
                return pizza_info["error"]

            response = random.choice(
                self.responses_template["view_menu"]["Pizza_Size" if "Size" in entities else "Pizza"]
            ).format(pizza_name=pizza_info["name"], size=pizza_info["size"])
            return f"{response}\n{self.format_pizza_response(pizza_info)}"
        else:
            full_menu_pizza = self.get_full_menu_pizza()
            if "error" in full_menu_pizza:
                return full_menu_pizza["error"]
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
        pass

    def _process_single_pizza(self, entities: dict) -> dict:
        cart_item = {"Pizza": entities["Pizza"][0][0]}

        # need check number of entity
        if "Quantity" in entities:
            cart_item["Quantity"] = entities["Quantity"][0][0]
        if "Size" in entities:
            cart_item["Size"] = [size[0] for size in entities["Size"]]
        if "Quantity" in entities:
            cart_item["Quantity"] = [quantity[0] for quantity in entities["Quantity"]]
        if "Topping" in entities:
            cart_item["Topping"] = [topping[0] for topping in entities["Topping"]]

        return cart_item

    def _build_cart_items_detail(self, message: str) -> list:
        entities = self.identify_order_entities(message)
        number_of_pizza_types = len(entities["Pizza"])
        number_of_quantity = len(entities["Quantity"])
        if number_of_pizza_types == 1 and number_of_quantity == 1 and entities["Quantity"][0][0] == 1:
            return [self._process_single_pizza(entities)]
        elif number_of_pizza_types == 1:
            pass
        return []
    
    def get_topping_ids(self, list_topping)


    def handle_add_to_cart(self, message: str) -> str:
        cart = self.get_active_cart(1)
        cart_items = self._build_cart_items_detail(message)
        for cart_item in cart_items:
            cart_item_dto = RequestPayloadCartItem(quantity=cart_item["Quantity"], cart_id=cart.id, product_id=cart_item[""])


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
