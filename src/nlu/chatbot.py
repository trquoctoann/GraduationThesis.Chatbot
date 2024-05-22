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
    ResponsePayloadOptionDetail,
    ResponsePayloadProduct,
)
from utils.api_url import APIUrls
from utils.correct_entity_name import (
    get_correct_crust_type,
    get_correct_pizza_name,
    get_correct_size,
    get_correct_topping_name,
    get_quantity_in_number,
)
from utils.invalid_product import InvalidProduct

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")


class Chatbot:
    def __init__(
        self,
        model_order_entity_path: str,
        model_customer_entity_path: str,
        model_intent_path: str,
        responses_template_path: str,
    ):
        self.model_order_entity = self._load_model_entity(model_order_entity_path, True)
        self.model_customer_entity = self._load_model_entity(model_customer_entity_path, False)
        self.model_intent = self._load_model_intent(model_intent_path)
        self.responses_template = self._load_response_template(responses_template_path)
        self.pending_information = {
            "add_to_cart": [],
            "provide_info": {},
            "remove_from_cart": [],
            "modify_cart_item": [],
        }
        self.pending_cus_info = False
        self.pending_confirmation = None

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

    def identify_intent(self, message: str) -> str:
        return self.model_intent.predict(preprocessing(message))

    def identify_order_entities(self, message: str, check_field: list) -> dict:
        entities = self.model_order_entity.predict(preprocessing(message, True))
        return self.verify_product_info(entities, check_field)

    def identify_order_entities_with_index(self, message: str, check_field: list) -> dict:
        entities = self.model_order_entity.predict_order_with_index(preprocessing(message, True))
        return self.verify_product_info_with_index(entities, check_field)

    def identify_customer_entities(self, message: str) -> dict:
        entities = self.model_customer_entity.predict(preprocessing(message, True))
        return self.clean_customer_entities(entities)

    def get_specified_pizza(self, pizza_name: str, size: str = None) -> ResponsePayloadProduct:
        request_url = APIUrls.PRODUCT_SERVICE.value + f"&name.contains=pizza {pizza_name}"
        if size:
            request_url += "&size.equals=" + size.upper()
        response = requests.get(request_url)

        if response.status_code == 200 and response.json():
            return ResponsePayloadProduct.from_json(response.json()[0])
        elif response.status_code != 200:
            raise InvalidProduct("Hệ thống xảy ra lỗi khi tải thông tin pizza " + pizza_name, "API")

    def get_full_menu_pizza(self) -> list[ResponsePayloadProduct]:
        response = requests.get(APIUrls.PRODUCT_SERVICE.value)
        if response.status_code == 200 and response.json():
            return [ResponsePayloadProduct.from_json(pizza) for pizza in response.json() if not pizza["size"]]
        elif response.status_code != 200:
            raise InvalidProduct("Hệ thống xảy ra lỗi khi tải thông tin toàn bộ pizza", "API")

    def get_active_cart(self, user_id: int) -> ResponsePayloadCart:
        response = requests.get(APIUrls.CART_SERVICE.value + f"?userId.equals={str(user_id)}&status.equals=ACTIVE")
        if response.status_code == 200 and response.json():
            return ResponsePayloadCart.from_json(response.json()[0])
        elif response.status_code != 200:
            raise InvalidProduct("Hệ thống xảy ra lỗi khi tải thông tin giỏ hàng của bạn", "API")

    def get_full_topping(self, size: str) -> list[ResponsePayloadOptionDetail]:
        response = requests.get(APIUrls.OPTION_DETAIL_SERVICE.value + f"?optionId.equals=2&size.equals={size}")
        if response.status_code == 200 and response.json():
            return [ResponsePayloadOptionDetail.from_json(topping) for topping in response.json()]
        elif response.status_code != 200:
            raise InvalidProduct("Hệ thống xảy ra lỗi khi tải thông tin toppings", "API")

    def get_all_cart_items(self, cart_id: int) -> list[ResponsePayloadCartItem]:
        response = requests.get(APIUrls.CART_ITEM_SERVICE.value + f"/all?cartId.equals={cart_id}")
        if response.status_code == 200 and response.json():
            return [ResponsePayloadCartItem.from_json(cart_item) for cart_item in response.json()]
        elif response.status_code != 200:
            raise InvalidProduct("Hệ thống xảy ra lỗi khi tải thông tin chi tiết giỏ hàng của bạn", "API")

    def get_specified_cart_item(self, cart_item_id: int) -> ResponsePayloadCartItem:
        response = requests.get(APIUrls.CART_ITEM_SERVICE.value + f"/{str(cart_item_id)}")
        if response.status_code == 200 and response.json():
            return ResponsePayloadCartItem.from_json(response.json())
        elif response.status_code != 200:
            raise InvalidProduct(
                "Hệ thống xảy ra lỗi khi tải thông tin chi tiết sản phẩm trong giỏ hàng của bạn", "API"
            )

    def get_topping_ids(self, pizza_info: ResponsePayloadProduct, toppings_list: list) -> list:
        if "Không" in toppings_list:
            return []
        topping_ids = []
        for option_detail in pizza_info.option_details:
            if option_detail.option_id == 2 and option_detail.name.lower() in toppings_list:
                topping_ids.append(option_detail.id)
        return topping_ids

    def post_cart_item(self, cart_item: RequestPayloadCartItem) -> None:
        response = requests.post(APIUrls.CART_ITEM_SERVICE.value, json=cart_item.to_dict())
        if response.status_code == 201:
            return None
        raise InvalidProduct("Hệ thống xảy ra lỗi khi thêm món vào giỏ hàng", "API")

    def update_cart_item(self, cart_item_id: int, cart_item_new_info: dict) -> None:
        specified_cart_item = self.get_specified_cart_item(cart_item_id)
        old_pizza = specified_cart_item.product.name.lower().replace("pizza ", "")
        old_size = specified_cart_item.product.size.lower()
        if cart_item_new_info["Pizza"] and cart_item_new_info["Pizza"] != old_pizza:
            if cart_item_new_info["Size"]:
                pizza_info = self.get_specified_pizza(cart_item_new_info["Pizza"], cart_item_new_info["Size"])
            else:
                pizza_info = self.get_specified_pizza(cart_item_new_info["Pizza"], old_size)
        else:
            if cart_item_new_info["Size"]:
                pizza_info = self.get_specified_pizza(old_pizza, cart_item_new_info["Size"])
            else:
                pizza_info = self.get_specified_pizza(old_pizza, old_size)

        option_detail_ids = set()
        if cart_item_new_info["Crust"]:
            if cart_item_new_info["Crust"].lower() == "dày":
                option_detail_ids.add(1)
            elif cart_item_new_info["Crust"].lower() == "mỏng":
                option_detail_ids.add(2)

        if cart_item_new_info["Topping"]:
            option_detail_ids.update(self.get_topping_ids(pizza_info, cart_item_new_info["Topping"]))
        cart_item_dto = RequestPayloadCartItem(
            id=cart_item_id,
            quantity=cart_item_new_info["Quantity"] if cart_item_new_info["Quantity"] else specified_cart_item.quantity,
            cart_id=1,
            product_id=pizza_info.id,
            option_detail_ids=option_detail_ids,
        )
        response = requests.put(APIUrls.CART_ITEM_SERVICE.value + "/" + str(cart_item_id), json=cart_item_dto.to_dict())
        if response.status_code == 204:
            return None
        raise InvalidProduct("Hệ thống xảy ra lỗi khi sửa món trong giỏ hàng", "API")

    def delete_cart_item(self, cart_item_id: int) -> None:
        response = requests.delete(APIUrls.CART_ITEM_SERVICE.value + "/" + str(cart_item_id))
        if response.status_code == 204:
            return None
        raise InvalidProduct("Hệ thống xảy ra lỗi khi xoá món khỏi giỏ hàng", "API")

    def format_menu_item_response(self, pizza_info: ResponsePayloadProduct) -> str:
        price, quantity = 0, 0
        for stock_item in pizza_info.stock_items:
            if stock_item.store_id == 1 and stock_item.product_id == pizza_info.id:
                price, quantity = stock_item.selling_price, stock_item.total_quantity
                break
        details = {
            "Mô tả": pizza_info.description,
            "Giá": str(price) + " ₫",
            "Số lượng còn lại": quantity,
            "Các loại đế bánh": ", ".join([od.name for od in pizza_info.option_details if od.option_id == 1]),
            "Topping có thể thêm": ", ".join([od.name for od in pizza_info.option_details if od.option_id == 2]),
        }
        details_response = "\n".join([f"{key}: {value}" for key, value in details.items()])
        return details_response

    def format_cart_item_response(self, cart_item_info: ResponsePayloadCartItem) -> str:
        details = {
            "Tên món": cart_item_info.product.name.lower().title(),
            "Số lượng": cart_item_info.quantity,
            "Size": cart_item_info.product.size,
            "Đế bánh": ", ".join([od.name for od in cart_item_info.option_details if od.option_id == 1]),
            "Topping": ", ".join([od.name for od in cart_item_info.option_details if od.option_id == 2]),
            "Tạm tính": str(cart_item_info.price) + " ₫",
        }
        details_response = "\n".join([f"{key}: {value}" for key, value in details.items()])
        return details_response

    def format_pending_cart_item(self, cart_item: dict) -> str:
        details = {
            "Tên món": cart_item["Pizza"].lower().title() if cart_item["Pizza"] else "Chưa cung cấp",
            "Số lượng": cart_item["Quantity"] if cart_item["Quantity"] else "Chưa cung cấp",
            "Size": cart_item["Size"].upper() if cart_item["Size"] else "Chưa cung cấp",
            "Đế bánh": cart_item["Crust"] if cart_item["Crust"] else "Chưa cung cấp",
            "Topping": ", ".join(cart_item["Topping"]) if cart_item["Topping"] else "Chưa cung cấp",
        }
        details_response = "\n".join([f"{key}: {value}" for key, value in details.items()])
        return details_response

    def format_customer_info(self, customer_info: dict) -> str:
        details = {
            "Tên khách hàng": ", ".join(customer_info["Cus"]),
            "Địa chỉ nhận hàng": ", ".join(customer_info["Address"]),
            "Phương thức thanh toán": ", ".join(customer_info["Payment"]),
            "Số điện thoại": ", ".join(customer_info["Phone"]),
        }
        details_response = "\n".join([f"{key}: {value}" for key, value in details.items()])
        return details_response

    def verify_product_info(self, entities: dict, check_field: list) -> dict:
        if "Pizza" in entities:
            valid_pizzas, invalid_pizzas = get_correct_pizza_name(entities["Pizza"])
            if invalid_pizzas and "Pizza" in check_field:
                raise InvalidProduct(invalid_pizzas, "Pizza")
            entities["Pizza"] = valid_pizzas

        if "Quantity" in entities:
            entities["Quantity"] = get_quantity_in_number(entities["Quantity"])

        if "Size" in entities:
            valid_sizes, invalid_sizes = get_correct_size(entities["Size"])
            if invalid_sizes and "Size" in check_field:
                raise InvalidProduct(invalid_sizes, "Size")
            entities["Size"] = valid_sizes

        if "Crust" in entities:
            valid_crusts, invalid_crusts = get_correct_crust_type(entities["Crust"])
            if invalid_crusts and "Crust" in check_field:
                raise InvalidProduct(invalid_crusts, "Crust")
            entities["Crust"] = valid_crusts

        if "Topping" in entities:
            valid_toppings, invalid_toppings = get_correct_topping_name(entities["Topping"])
            if invalid_toppings and "Topping" in check_field:
                raise InvalidProduct(invalid_toppings, "Topping")
            entities["Topping"] = valid_toppings
        return entities

    def verify_product_info_with_index(self, entities: dict, check_field: list) -> dict:
        def update_entities(key, func, check_field, index_field=1):
            if key in entities:
                values = [item[0] for item in entities[key]]
                valid_values, invalid_values = func(values)
                if invalid_values and key in check_field:
                    raise InvalidProduct(invalid_values, key)
                entities[key] = [(valid_values[i], entities[key][i][index_field]) for i in range(len(valid_values))]

        update_entities("Pizza", get_correct_pizza_name, check_field)
        update_entities("Size", get_correct_size, check_field)
        update_entities("Crust", get_correct_crust_type, check_field)
        update_entities("Topping", get_correct_topping_name, check_field)

        if "Quantity" in entities:
            quantities = [item[0] for item in entities["Quantity"]]
            quantities_in_number = get_quantity_in_number(quantities)
            entities["Quantity"] = [
                (quantities_in_number[i], entities["Quantity"][i][1]) for i in range(len(quantities))
            ]

        return entities

    def clean_customer_entities(self, entities: dict):
        if "Cus" in entities:
            entities["Cus"] = [cus.replace("_", " ") for cus in entities["Cus"]]

        if "Address" in entities:
            entities["Address"] = [address.replace("_", " ") for address in entities["Address"]]

        if "Payment" in entities:
            entities["Payment"] = [payment.replace("_", " ") for payment in entities["Payment"]]

        return entities

    def handle_view_menu(self, message: str) -> str:
        entities_with_index = self.identify_order_entities_with_index(message, ["Pizza", "Size"])

        if "Pizza" in entities_with_index:
            parsed_items = self._process_multiple_pizzas(entities_with_index)

            response = ""
            for parsed_item in parsed_items:
                pizza_name = parsed_item["Pizza"]
                size = parsed_item["Size"]
                if pizza_name and size:
                    response += (
                        random.choice(self.responses_template["view_menu"]["Pizza_Size"]).format(
                            pizza_name=pizza_name.lower().title(), size=size.upper()
                        )
                        + "\n"
                    )
                    response += self.format_menu_item_response(self.get_specified_pizza(pizza_name, size))
                    response += "\n --------------------------------------------------------- \n"
                elif pizza_name:
                    response += (
                        random.choice(self.responses_template["view_menu"]["Pizza"]).format(
                            pizza_name=pizza_name.lower().title()
                        )
                        + "\n"
                    )
                    response += self.format_menu_item_response(self.get_specified_pizza(pizza_name, "l"))
                    response += "\n --------------------------------------------------------- \n"
            return response
        else:
            full_menu_pizza = self.get_full_menu_pizza()
            response = random.choice(self.responses_template["view_menu"]["unknown"])
            menu_details = "\n".join(
                [f"-- {item.name.lower().title()}. Mô tả: {item.description}" for item in full_menu_pizza]
            )
            return f"{response}\n{menu_details}"

    def handle_view_cart(self, message: str) -> str:
        entities = self.identify_order_entities(message, ["Pizza"])

        cart_info = self.get_active_cart(1)
        cart_items = self.get_all_cart_items(cart_info.id)
        if not cart_items:
            return "Giỏ hàng của bạn hiện tại đang trống."

        if "Pizza" in entities:
            pizzas = entities["Pizza"]
            nonexist_pizza = pizzas.copy()
            response = ""
            for cart_item in cart_items:
                pizza_name = cart_item.product.name.lower().replace("pizza ", "")
                if pizza_name in pizzas:
                    if pizza_name in nonexist_pizza:
                        nonexist_pizza.remove(pizza_name)
                    response += (
                        random.choice(self.responses_template["view_cart"]["Pizza"]["exist"]).format(
                            pizza_name=cart_item.product.name.lower().title()
                        )
                        + "\n"
                    )
                    response += self.format_cart_item_response(cart_item)
                    response += "\n --------------------------------------------------------- \n"

            if nonexist_pizza:
                response += random.choice(self.responses_template["view_cart"]["Pizza"]["nonexist"]).format(
                    pizza_name=", ".join(nonexist_pizza)
                )
            return response
        else:
            response = random.choice(self.responses_template["view_cart"]["unknown"])
            results = []
            count = 1
            for cart_item in cart_items:
                quantity = cart_item.quantity
                pizza_name = cart_item.product.name.lower().title()
                size = cart_item.product.size.upper()
                crust = ", ".join([od.name.lower() for od in cart_item.option_details if od.option_id == 1])
                topping = ", ".join([od.name.lower() for od in cart_item.option_details if od.option_id == 2])
                price = cart_item.price
                if topping:
                    results.append(
                        f"Món {count}. {quantity} {pizza_name} cỡ {size} đế {crust} với topping {topping}. Tạm tính: {price} ₫"
                    )
                else:
                    results.append(
                        f"Món {count}. {quantity} {pizza_name} cỡ {size} đế {crust} không topping. Tạm tính: {price} ₫"
                    )
                count += 1
            joined_results = "\n".join(results)
            return f"{response}\n{joined_results}"

    def _process_single_pizza(self, entities: dict) -> dict:
        cart_item = {}
        cart_item["Pizza"] = entities["Pizza"][0] if "Pizza" in entities else None
        cart_item["Quantity"] = int(entities["Quantity"][0]) if "Quantity" in entities else None
        cart_item["Size"] = entities["Size"][0] if "Size" in entities else None
        cart_item["Crust"] = entities["Crust"][0] if "Crust" in entities else None
        cart_item["Topping"] = entities["Topping"] if "Topping" in entities else []
        return [cart_item]

    def _split_entities_by_base_entity(self, entities: dict):
        def find_base_entity(entities: dict):
            priority_keys = ["Pizza", "Size", "Crust"]
            max_key = None
            max_length = 0

            for key, values in entities.items():
                if key != "Topping":
                    current_length = len(values)
                    if current_length > max_length or (current_length == max_length and key in priority_keys):
                        if current_length > max_length or (
                            max_key not in priority_keys or priority_keys.index(key) < priority_keys.index(max_key)
                        ):
                            max_length = current_length
                            max_key = key

            if "Size" in entities and "Crust" in entities and "Pizza" in entities:
                size_length = len(entities["Size"])
                crust_length = len(entities["Crust"])
                pizza_length = len(entities["Pizza"])
                if size_length == max_length and crust_length == max_length and pizza_length == max_length:
                    return "Pizza"
                if size_length == max_length and crust_length == max_length:
                    size_min_index = min([item[1] for item in entities["Size"]])
                    crust_min_index = min([item[1] for item in entities["Crust"]])
                    return "Size" if size_min_index < crust_min_index else "Crust"

            return max_key

        has_quantity = True
        indices = [index for _, index in entities.get("Quantity", [])]
        if not indices:
            max_key = find_base_entity(entities)
            indices = [index for _, index in entities[max_key]]
            has_quantity = False

        ranges = [(indices[i], indices[i + 1]) for i in range(len(indices) - 1)]
        ranges.append((indices[-1], -1))

        result = [{} for _ in ranges]
        for entity_type, values in entities.items():
            for value, index in values:
                for i, (start, end) in enumerate(ranges):
                    if (end == -1 and index >= start) or (start <= index < end):
                        if entity_type == "Topping":
                            if entity_type not in result[i]:
                                result[i][entity_type] = []
                            result[i][entity_type].append(value)
                        else:
                            result[i][entity_type] = value
                        break
        return result, has_quantity

    def _process_multiple_pizzas(self, entities: dict) -> dict:
        split_entities, has_quantity = self._split_entities_by_base_entity(entities)
        current_pizza_index = None
        for split_entity_index in range(len(split_entities)):
            split_entity = split_entities[split_entity_index]

            if "Pizza" in split_entity:
                current_pizza_index = split_entity_index
            elif "Pizza" not in split_entity and current_pizza_index is not None:
                split_entities[split_entity_index]["Pizza"] = split_entities[current_pizza_index]["Pizza"]
                if has_quantity:
                    split_entities[current_pizza_index]["Quantity"] -= split_entities[split_entity_index]["Quantity"]
                if "Size" not in split_entity:
                    split_entities[split_entity_index]["Size"] = split_entities[current_pizza_index]["Size"]
                if "Crust" not in split_entity:
                    split_entities[split_entity_index]["Crust"] = split_entities[current_pizza_index]["Crust"]
            elif "Pizza" not in split_entity and not current_pizza_index:
                split_entities[split_entity_index]["Pizza"] = None

            if not has_quantity:
                split_entities[split_entity_index]["Quantity"] = None
            if "Size" not in split_entity:
                split_entities[split_entity_index]["Size"] = None
            if "Crust" not in split_entity:
                split_entities[split_entity_index]["Crust"] = None
            if "Topping" not in split_entity:
                split_entities[split_entity_index]["Topping"] = []

        cart_items = []
        for cart_item in split_entities:
            if not has_quantity:
                cart_items.append(cart_item)
            else:
                if cart_item["Quantity"] > 0:
                    cart_items.append(cart_item)
        return cart_items

    def is_single_pizza(self, entities: dict):
        if len(entities.get("Pizza", [])) > 1:
            return False
        if len(entities.get("Quantity", [])) > 1:
            return False
        if len(entities.get("Size", [])) > 1:
            return False
        if len(entities.get("Crust", [])) > 1:
            return False
        return True

    def _build_cart_items_detail(self, message: str) -> list:
        entities = self.identify_order_entities(message, ["Pizza", "Size", "Crust", "Topping"])
        if self.is_single_pizza(entities):
            self.pending_information["add_to_cart"].extend(self._process_single_pizza(entities))
        else:
            entities_with_index = self.identify_order_entities_with_index(
                message, ["Pizza", "Size", "Crust", "Topping"]
            )
            self.pending_information["add_to_cart"].extend(self._process_multiple_pizzas(entities_with_index))

    def handle_add_to_cart(self, message: str) -> str:
        self._build_cart_items_detail(message)
        header = "Dựa vào yêu cầu của bạn, có vẻ như bạn muốn đặt các món như sau:"
        footer = "Nếu đúng, bạn nhắn 'Y' để xác nhận nha. Nếu có gì sai, bạn nhắn 'N' giúp mình nhé."
        body = ""
        count = 1
        self.pending_confirmation = "add_to_cart"
        for cart_item in self.pending_information["add_to_cart"]:
            body += "Món " + str(count) + ". \n"
            body += (
                self.format_pending_cart_item(cart_item)
                + "\n --------------------------------------------------------- \n"
            )
            count += 1
        return header + "\n --------------------------------------------------------- \n" + body + footer

    def is_cart_item_missing_info(self, cart_item):
        if (
            cart_item["Quantity"]
            and cart_item["Pizza"]
            and cart_item["Size"]
            and cart_item["Crust"]
            and cart_item["Topping"]
        ):
            return False
        return True

    def check_missing_info_cart_item(self, is_first_time: bool) -> str:
        response = []
        if is_first_time:
            new_pending_cart_item = []
            count = 1
            for cart_item in self.pending_information["add_to_cart"]:
                if not self.is_cart_item_missing_info(cart_item):
                    response.append(self.finalize_add_to_cart(cart_item))
                else:
                    cart_item["id"] = count
                    new_pending_cart_item.append(cart_item)
                count += 1
            self.pending_information["add_to_cart"] = new_pending_cart_item
        else:
            cart_item = self.pending_information["add_to_cart"].pop(0)
            response.append(self.finalize_add_to_cart(cart_item))

        if self.pending_information["add_to_cart"]:
            missing_info = []
            if not self.pending_information["add_to_cart"][0]["Quantity"]:
                missing_info.append(random.choice(self.responses_template["add_to_cart"]["missing_quantity"]))
            if not self.pending_information["add_to_cart"][0]["Pizza"]:
                missing_info.append(random.choice(self.responses_template["add_to_cart"]["missing_pizza"]))
            if not self.pending_information["add_to_cart"][0]["Size"]:
                missing_info.append(random.choice(self.responses_template["add_to_cart"]["missing_size"]))
            if not self.pending_information["add_to_cart"][0]["Crust"]:
                missing_info.append(random.choice(self.responses_template["add_to_cart"]["missing_crust"]))
            if not self.pending_information["add_to_cart"][0]["Topping"]:
                missing_info.append(random.choice(self.responses_template["add_to_cart"]["missing_topping"]))
            response.append(
                random.choice(self.responses_template["add_to_cart"]["missing_template"]).format(
                    id=self.pending_information["add_to_cart"][0]["id"], missing_entity=", ".join(missing_info)
                )
            )
        return "\n --------------------------------------------------------- \n".join(response)

    def finalize_add_to_cart(self, cart_item: dict) -> str:
        cart = self.get_active_cart(1)
        pizza_info = self.get_specified_pizza(cart_item["Pizza"], cart_item["Size"])

        option_detail_ids = set()
        if cart_item["Crust"].lower() == "dày":
            option_detail_ids.add(1)
        elif cart_item["Crust"].lower() == "mỏng":
            option_detail_ids.add(2)
        option_detail_ids.update(self.get_topping_ids(pizza_info, cart_item.get("Topping", [])))

        cart_item_dto = RequestPayloadCartItem(
            quantity=cart_item["Quantity"],
            cart_id=cart.id,
            product_id=pizza_info.id,
            option_detail_ids=option_detail_ids,
        )
        self.post_cart_item(cart_item_dto)
        topping = ""
        if not cart_item.get("Topping") or cart_item.get("Topping") == ["Không"]:
            topping = "không thêm topping"
        return random.choice(self.responses_template["add_to_cart"]["all"]).format(
            quantity=cart_item["Quantity"],
            pizza_name=cart_item["Pizza"],
            size=cart_item["Size"],
            crust=cart_item["Crust"],
            topping=(("kèm " + ", ".join(cart_item.get("Topping"))) if not topping else "không topping thêm"),
        )

    def handle_pending_information_cart_item(self, message: str) -> str:
        entities = self.identify_order_entities(message, ["Pizza", "Size", "Crust", "Topping"])
        if "không topping" in message:
            self.pending_information["add_to_cart"][0]["Topping"] = ["Không"]

        fields = ["Pizza", "Quantity", "Size", "Crust", "Topping"]
        for field in fields:
            if field in entities and not self.pending_information["add_to_cart"][0][field]:
                if field == "Topping":
                    self.pending_information["add_to_cart"][0][field] = entities[field]
                else:
                    self.pending_information["add_to_cart"][0][field] = entities[field][0]
            elif field not in entities and not self.pending_information["add_to_cart"][0][field]:
                return random.choice(self.responses_template["add_to_cart"]["missing_template"]).format(
                    id=self.pending_information["add_to_cart"][0]["id"],
                    missing_entity=random.choice(self.responses_template["add_to_cart"][f"missing_{field.lower()}"]),
                )

        if not self.is_cart_item_missing_info(self.pending_information["add_to_cart"][0]):
            return self.check_missing_info_cart_item(False)

    def handle_remove_from_cart(self, message: str) -> str:
        entities = self.identify_order_entities(message, ["Pizza"])

        cart_info = self.get_active_cart(1)
        cart_items = self.get_all_cart_items(cart_info.id)
        if "Pizza" in entities:
            pizzas = entities["Pizza"]
            pizzas = set(pizzas)
            in_delete_demand_pizzas = []
            nonexist_pizza = []
            for pizza in pizzas:
                similar_pizza = []
                for cart_item in cart_items:
                    pizza_name = cart_item.product.name.lower().replace("pizza ", "")
                    if pizza_name == pizza:
                        similar_pizza.append(cart_item)
                if not similar_pizza:
                    nonexist_pizza.append(pizza)
                else:
                    in_delete_demand_pizzas.append(similar_pizza)
            response = ""
            if nonexist_pizza:
                response += random.choice(self.responses_template["remove_from_cart"]["nonexist"]).format(
                    pizza_name=", ".join(nonexist_pizza)
                )

            if in_delete_demand_pizzas:
                self.pending_confirmation = "remove_from_cart"
                self.pending_information["remove_from_cart"] = in_delete_demand_pizzas
                if nonexist_pizza:
                    response += "\n ---------------------------------------------------------"
                response += "\n"
            else:
                return response

            header = "Dựa vào yêu cầu của bạn, có vẻ như bạn muốn xoá các món như sau khỏi giỏ hàng:" + "\n"
            footer = "Nếu đúng, bạn nhắn 'Y' để xác nhận nha. Nếu có gì sai, bạn nhắn 'N' giúp mình nhé."
            body = ""
            count = 1
            for in_delete_demand_pizza in in_delete_demand_pizzas:
                body += str(count) + ". " + in_delete_demand_pizza[0].product.name.lower().title() + "\n"
            return response + header + body + footer
        else:
            response = random.choice(self.responses_template["remove_from_cart"]["unknown"])
            results = []
            count = 1
            for cart_item in cart_items:
                quantity = cart_item.quantity
                pizza_name = cart_item.product.name.lower().title()
                size = cart_item.product.size.upper()
                crust = ", ".join([od.name.lower() for od in cart_item.option_details if od.option_id == 1])
                topping = ", ".join([od.name.lower() for od in cart_item.option_details if od.option_id == 2])
                if topping:
                    results.append(f"Món {count}. {quantity} {pizza_name} cỡ {size} đế {crust} với topping {topping}")
                else:
                    results.append(f"Món {count}. {quantity} {pizza_name} cỡ {size} đế {crust} không topping")
                count += 1
            joined_results = "\n".join(results)
            return f"{response}\n{joined_results}"

    def check_if_correct_cart_item(self, action_type: str) -> str:
        response = []
        if action_type == "remove_from_cart":
            new_pending_remove_cart_item = []
            for pending_item in self.pending_information["remove_from_cart"]:
                if len(pending_item) == 1:
                    self.delete_cart_item(pending_item[0].id)
                    response.append(
                        random.choice(self.responses_template["remove_from_cart"]["Pizza"]).format(
                            pizza_name=pending_item[0].product.name.lower().title()
                        )
                    )
                else:
                    new_pending_remove_cart_item.append(pending_item)
            self.pending_information["remove_from_cart"] = new_pending_remove_cart_item
        elif action_type == "modify_cart_item":
            new_pending_modify_cart_item = []
            for pending_item in self.pending_information["modify_cart_item"]:
                if len(pending_item["similar_pizza"]) == 1:
                    self.update_cart_item(pending_item["similar_pizza"][0].id, pending_item["changes"])
                    response.append(
                        random.choice(self.responses_template["modify_cart_item"]["Pizza"]).format(
                            pizza_name=pending_item["similar_pizza"][0].product.name.lower().title()
                        )
                    )
                else:
                    new_pending_modify_cart_item.append(pending_item)
            self.pending_information["modify_cart_item"] = new_pending_modify_cart_item
        if self.pending_information[action_type]:
            response.append(self.ask_for_confused_pizza(action_type))
        return "\n --------------------------------------------------------- \n".join(response)

    def ask_for_confused_pizza(self, action_type: str):
        cart_items = []
        if action_type == "remove_from_cart":
            header = (
                "Trong giỏ hàng của bạn có nhiều hơn 1 món "
                + self.pending_information["remove_from_cart"][0][0].product.name.lower().title()
                + ". Sau đây là danh sách các món trùng khớp: \n"
            )
            footer = "Bạn vui lòng chỉ định món bạn muốn xoá bằng cách nhắn số tương ứng nhé."
            cart_items = self.pending_information[action_type][0]
        elif action_type == "modify_cart_item":
            header = (
                "Trong giỏ hàng của bạn có nhiều hơn 1 món "
                + self.pending_information["modify_cart_item"][0]["similar_pizza"][0].product.name.lower().title()
                + ". Sau đây là danh sách các món trùng khớp: \n"
            )
            footer = "Bạn vui lòng chỉ định món bạn muốn chỉnh sửa bằng cách nhắn số tương ứng nhé."
            cart_items = self.pending_information[action_type][0]["similar_pizza"]
        body = ""
        count = 1
        for cart_item in cart_items:
            quantity = cart_item.quantity
            pizza_name = cart_item.product.name.lower().title()
            size = cart_item.product.size.upper()
            crust = ", ".join([od.name.lower() for od in cart_item.option_details if od.option_id == 1])
            topping = ", ".join([od.name.lower() for od in cart_item.option_details if od.option_id == 2])
            if topping:
                body += f"{count}. {quantity} {pizza_name} cỡ {size} đế {crust} với topping {topping} \n"
            else:
                body += f"{count}. {quantity} {pizza_name} cỡ {size} đế {crust} không topping \n"
            count += 1
        if action_type == "remove_from_cart":
            body += f"{count}. Xoá hết \n"
        return header + body + footer

    def choose_pizza_to_take_action(self, message, action_type: str) -> str:
        response = []
        try:
            choosen_number = int(message) - 1
        except ValueError:
            return random.choice(self.responses_template["ask_for_info"])
        if action_type == "remove_from_cart":
            if choosen_number > len(self.pending_information["remove_from_cart"][0]) or choosen_number < 0:
                return "Bạn vui lòng chọn số trong danh sách mình đã liệt kê ở trên nhé."
            elif choosen_number == len(self.pending_information["remove_from_cart"][0]):
                for cart_item in self.pending_information["remove_from_cart"].pop(0):
                    self.delete_cart_item(cart_item.id)
                    response.append(
                        random.choice(self.responses_template["remove_from_cart"]["Pizza"]).format(
                            pizza_name=cart_item.product.name.lower()
                        )
                    )
            else:
                cart_item = self.pending_information["remove_from_cart"].pop(0)[choosen_number]
                self.delete_cart_item(cart_item.id)
                response.append(
                    random.choice(self.responses_template["remove_from_cart"]["Pizza"]).format(
                        pizza_name=cart_item.product.name.lower()
                    )
                )

        elif action_type == "modify_cart_item":
            if choosen_number >= len(self.pending_information["modify_cart_item"][0]) or choosen_number < 0:
                return "Bạn vui lòng chọn số trong danh sách mình đã liệt kê ở trên nhé."
            changes = self.pending_information["modify_cart_item"][0]["changes"]
            cart_item = self.pending_information["modify_cart_item"].pop(0)["similar_pizza"][choosen_number]
            self.update_cart_item(cart_item.id, changes)
            response.append(
                random.choice(self.responses_template["modify_cart_item"]["Pizza"]).format(
                    pizza_name=cart_item.product.name.lower()
                )
            )
        if self.pending_information[action_type]:
            response.append(self.ask_for_confused_pizza(action_type))
        return "\n --------------------------------------------------------- \n".join(response)

    def handle_modify_cart_item(self, message: str) -> str:
        entities = self.identify_order_entities(message, ["Pizza", "Size", "Crust", "Topping"])
        if self.is_single_pizza(entities):
            parsed_items = self._process_single_pizza(entities)
        else:
            entities_with_index = self.identify_order_entities_with_index(
                message, ["Pizza", "Size", "Crust", "Topping"]
            )
            parsed_items = self._process_multiple_pizzas(entities_with_index)

        cart_info = self.get_active_cart(1)
        cart_items = self.get_all_cart_items(cart_info.id)
        if "Pizza" in entities:
            in_modify_demand_pizzas = []
            nonexist_pizza = []
            for parsed_item in parsed_items:
                similar_pizza = []
                for cart_item in cart_items:
                    pizza_name = cart_item.product.name.lower().replace("pizza ", "")
                    if pizza_name == parsed_item["Pizza"]:
                        similar_pizza.append(cart_item)
                if not similar_pizza:
                    nonexist_pizza.append(pizza_name)
                else:
                    in_modify_demand_pizzas.append({"changes": parsed_item, "similar_pizza": similar_pizza})
            response = ""
            if nonexist_pizza:
                response += random.choice(self.responses_template["modify_cart_item"]["nonexist"]).format(
                    pizza_name=", ".join(nonexist_pizza)
                )

            if in_modify_demand_pizzas:
                self.pending_confirmation = "modify_cart_item"
                self.pending_information["modify_cart_item"] = in_modify_demand_pizzas
                if nonexist_pizza:
                    response += "\n ---------------------------------------------------------"
                response += "\n"
            else:
                return response
            header = "Dựa vào yêu cầu của bạn, có vẻ như bạn muốn chinh sửa các món sau:" + "\n"
            footer = "Nếu đúng, bạn nhắn 'Y' để xác nhận nha. Nếu có gì sai, bạn nhắn 'N' giúp mình nhé."
            body = ""
            count = 1
            for in_modify_demand_pizza in in_modify_demand_pizzas:
                body += (
                    str(count) + ". " + in_modify_demand_pizza["similar_pizza"][0].product.name.lower().title() + "\n"
                )
            return response + header + body + footer
        else:
            response = random.choice(self.responses_template["modify_cart_item"]["unknown"])
            results = []
            count = 1
            for cart_item in cart_items:
                quantity = cart_item.quantity
                pizza_name = cart_item.product.name.lower().title()
                size = cart_item.product.size.upper()
                crust = ", ".join([od.name.lower() for od in cart_item.option_details if od.option_id == 1])
                topping = ", ".join([od.name.lower() for od in cart_item.option_details if od.option_id == 2])
                if topping:
                    results.append(f"Món {count}. {quantity} {pizza_name} cỡ {size} đế {crust} với topping {topping}")
                else:
                    results.append(f"Món {count}. {quantity} {pizza_name} cỡ {size} đế {crust} không topping")
                count += 1
            joined_results = "\n".join(results)
            return f"{response}\n{joined_results}"

    def handle_confirm_order(self):
        cart_info = self.get_active_cart(user_id=1)
        cart_items = self.get_all_cart_items(cart_id=cart_info.id)
        header = random.choice(self.responses_template["confirm_order"]["header"])
        footer = random.choice(self.responses_template["confirm_order"]["footer"])
        body = ""
        count = 1
        total_price = 0
        self.pending_confirmation = "confirm_order"
        for cart_item in cart_items:
            body += "Món " + str(count) + ". \n"
            body += (
                self.format_cart_item_response(cart_item)
                + "\n --------------------------------------------------------- \n"
            )
            count += 1
            total_price += cart_item.price
        return (
            header
            + "\n --------------------------------------------------------- \n"
            + body
            + "\n"
            + "Tổng: "
            + str(total_price)
            + "₫ \n"
            + footer
        )

    def handle_track_order(self):
        return random.choice(self.responses_template["track_order"]["unknown"])

    def handle_cancel_order(self):
        return random.choice(self.responses_template["cancel_order"]["unknown"])

    def handle_provide_info(self, message: str) -> str:
        entities = self.identify_customer_entities(message)
        fields = ["Cus", "Address", "Phone", "Payment"]
        missing_info = []

        for field in fields:
            if field not in entities and field not in self.pending_information["provide_info"]:
                missing_info.append(random.choice(self.responses_template["provide_info"][f"missing_{field.lower()}"]))
            elif field in entities:
                self.pending_information["provide_info"][field] = entities[field]

        if not missing_info:
            header = random.choice(self.responses_template["provide_info"]["confirm_info"]["header"])
            footer = random.choice(self.responses_template["provide_info"]["confirm_info"]["footer"])
            customer_info = self.format_customer_info(self.pending_information["provide_info"])
            cart_info = self.get_active_cart(1)
            cart_items = self.get_all_cart_items(cart_info.id)
            for cart_item in cart_items:
                self.delete_cart_item(cart_item.id)
            self.pending_cus_info = False
            return f"{header}\n{customer_info}\n{footer}"

        return random.choice(self.responses_template["provide_info"]["missing_template"]).format(
            missing_entity=", ".join(missing_info)
        )

    def handle_pending_information_provide_info(self, message: str) -> str:
        entities = self.identify_customer_entities(message)

        fields = ["Cus", "Address", "Phone", "Payment"]

        for field in fields:
            if field in entities and field not in self.pending_information["provide_info"]:
                self.pending_information["provide_info"][field] = entities[field]
            elif field not in entities and field not in self.pending_information["provide_info"]:
                return random.choice(self.responses_template["provide_info"]["missing_template"]).format(
                    missing_entity=random.choice(self.responses_template["provide_info"][f"missing_{field.lower()}"])
                )

        if len(self.pending_information["provide_info"]) == 4:
            header = random.choice(self.responses_template["provide_info"]["confirm_info"]["header"])
            footer = random.choice(self.responses_template["provide_info"]["confirm_info"]["footer"])
            customer_info = self.format_customer_info(self.pending_information["provide_info"])
            cart_info = self.get_active_cart(1)
            cart_items = self.get_all_cart_items(cart_info.id)
            for cart_item in cart_items:
                self.delete_cart_item(cart_item.id)
            self.pending_cus_info = False
            return f"{header}\n{customer_info}\n{footer}"

    def handle_pending_confirmation(self, message: str):
        response = ""
        if message.lower() == "y":
            if self.pending_confirmation == "confirm_order":
                if (
                    not self.pending_information["provide_info"]
                    or 0 < len(self.pending_information["provide_info"]) < 4
                ):
                    response = "Và cuối cùng, để hoàn tất quá trình xác nhận đơn, bạn vui lòng cung cấp thông tin để chúng mình giao hàng nhé."
                    self.pending_cus_info = True
                else:
                    response = random.choice(self.responses_template["confirm_order"]["yes"])
            elif self.pending_confirmation == "add_to_cart":
                response = self.check_missing_info_cart_item(True)
            elif self.pending_confirmation == "remove_from_cart":
                response = self.check_if_correct_cart_item("remove_from_cart")
            elif self.pending_confirmation == "modify_cart_item":
                response = self.check_if_correct_cart_item("modify_cart_item")
            self.pending_confirmation = None
        elif message.lower() == "n":
            if self.pending_confirmation == "confirm_order":
                response = random.choice(self.responses_template["confirm_order"]["no"])
            elif self.pending_confirmation == "add_to_cart":
                self.pending_information["add_to_cart"] = []
                response = random.choice(self.responses_template["add_to_cart"]["no"])
            elif self.pending_confirmation == "remove_from_cart":
                self.pending_information["remove_from_cart"] = []
                response = random.choice(self.responses_template["remove_from_cart"]["no"])
            elif self.pending_confirmation == "modify_cart_item":
                self.pending_information["modify_cart_item"] = []
                response = random.choice(self.responses_template["modify_cart_item"]["no"])
            self.pending_confirmation = None
        else:
            response = random.choice(self.responses_template["yes_no_loop"])
        return response

    def handle_message(self, message: str):
        try:
            if self.pending_cus_info or 0 < len(self.pending_information["provide_info"]) < 4:
                return self.handle_pending_information_provide_info(message)
            if self.pending_confirmation:
                return self.handle_pending_confirmation(message)

            if self.pending_information["add_to_cart"]:
                return self.handle_pending_information_cart_item(message)
            elif self.pending_information["remove_from_cart"]:
                return self.choose_pizza_to_take_action(message, "remove_from_cart")
            elif self.pending_information["modify_cart_item"]:
                return self.choose_pizza_to_take_action(message, "modify_cart_item")

            message_intent = self.identify_intent(message)
            intent_handlers_with_param = {
                "view_menu": self.handle_view_menu,
                "view_cart": self.handle_view_cart,
                "add_to_cart": self.handle_add_to_cart,
                "remove_from_cart": self.handle_remove_from_cart,
                "modify_cart_item": self.handle_modify_cart_item,
                "provide_info": self.handle_provide_info,
            }

            intent_handlers_without_param = {
                "confirm_order": self.handle_confirm_order,
                "track_order": self.handle_track_order,
                "cancel_order": self.handle_cancel_order,
            }

            if message_intent in intent_handlers_with_param:
                return intent_handlers_with_param[message_intent](message)
            elif message_intent in intent_handlers_without_param:
                return intent_handlers_without_param[message_intent]()
            else:
                return random.choice(self.responses_template["unknown"])

        except InvalidProduct as e:
            error_response_templates = {
                "Pizza": "invalid_pizza",
                "Size": "invalid_size",
                "Crust": "invalid_crust",
                "Topping": "invalid_topping",
                "API": None,
            }

            if e.message in error_response_templates:
                template_key = error_response_templates[e.message]
                if template_key:
                    return random.choice(self.responses_template[template_key]).format(
                        product_name=", ".join(e.product_name)
                    )
                else:
                    return e.product_name
