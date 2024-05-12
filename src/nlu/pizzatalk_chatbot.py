import json
import random

import torch

from models.entities.entities_recognizer import EntitiesRecognizer
from models.intents.intents_recognizer import IntentsRecognizer
from nlu.payload.request.request_payload_cart_item import (
    RequestPayloadCartItem,
)
from utils.chatbot_utils import (
    InvalidProductName,
    standardize_result,
    verify_product_name,
)

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")


class PizzaTalkChatbot:
    def __init__(self, model_entity_path, model_intent_path, responses_template_path):
        self.model_entity = self._load_model_entity(model_entity_path)
        self.model_intent = self._load_model_intent(model_intent_path)
        self.responses_template = self._load_response_template(responses_template_path)

    def _load_model_entity(self, model_path):
        model = EntitiesRecognizer(model_path)
        return model

    def _load_model_intent(self, model_path):
        model = IntentsRecognizer()
        model.load_state_dict(torch.load(model_path))
        return model.to(device)

    def _load_response_template(self, responses_template_path):
        with open(responses_template_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def identify_intent(self, message):
        return self.model_intent.predict(message)

    def identify_entities(self, message):
        return self.model_entity.predict(message)

    def get_response(self, intent: str, detected_entity: dict):
        if not intent:
            return random.choice(self.responses_template["Unknown"]["responses"])

        print(detected_entity)
        if (
            not detected_entity
            or intent == "confirm_order"
            or intent == "track_order"
            or intent == "cancel_order"
        ):
            return random.choice(
                self.responses_template[intent]["Unknown"]["responses"]
            )

        if intent == "view_menu" or intent == "view_cart":
            if "Pizza" in detected_entity:
                try:
                    verify_product_name(detected_entity)
                except InvalidProductName as e:
                    return (
                        "Xin lỗi. Cửa hàng chúng mình không có pizza "
                        + e.product_name
                        + " ạ"
                    )
                return random.choice(
                    self.responses_template[intent]["Pizza"]["responses"]
                )
            else:
                return random.choice(
                    self.responses_template[intent]["Others"]["responses"]
                )

        if intent == "add_to_cart":
            try:
                verify_product_name(detected_entity)
            except InvalidProductName as e:
                if e.message == "Invalid pizza":
                    return (
                        "Xin lỗi. Cửa hàng chúng mình không có pizza "
                        + e.product_name
                        + " ạ"
                    )
                elif e.message == "Invalid size":
                    return "Xin lỗi. Cửa hàng chúng mình chỉ phục vụ pizza cỡ S, X, XL thôi ạ"
                elif e.message == "Invalid crust":
                    return "Xin lỗi. Cửa hàng chúng mình chỉ phục vụ pizza có đế mỏng hoặc dày thôi ạ"

            missing_entities = [
                key
                for key in ["Pizza", "Quantity", "Size", "Crust", "Topping"]
                if key not in detected_entity
            ]
            if not missing_entities:
                response = (
                    random.choice(self.responses_template[intent]["All"]["responses"])
                    .format(**{k: v for k, v in detected_entity.items()})
                    .replace("[pizza]", standardize_result(detected_entity["Pizza"][0]))
                    .replace(
                        "[quantity]", standardize_result(detected_entity["Quantity"][0])
                    )
                    .replace("[size]", standardize_result(detected_entity["Size"][0]))
                    .replace("[crust]", standardize_result(detected_entity["Crust"][0]))
                    .replace(
                        "[topping]",
                        standardize_result(", ".join(detected_entity["Topping"])),
                    )
                    .title()
                )

            else:
                missing_details = ", ".join(
                    [
                        random.choice(
                            self.responses_template[intent][
                                f"missing_{entity.lower()}"
                            ]["responses"]
                        )
                        for entity in missing_entities
                    ]
                )
                template = random.choice(
                    self.responses_template[intent]["missing_template"]["responses"]
                )
                response = template.replace("[missing_entity]", missing_details)
            return response

        if intent == "remove_from_cart":
            if "Pizza" in detected_entity and "Quantity" in detected_entity:
                return (
                    random.choice(
                        self.responses_template[intent]["Pizza_Quantity"]["responses"]
                    )
                    .replace("[pizza]", standardize_result(detected_entity["Pizza"][0]))
                    .replace(
                        "[quantity]", standardize_result(detected_entity["Quantity"][0])
                    )
                )
            elif "Pizza" in detected_entity:
                return random.choice(
                    self.responses_template[intent]["Pizza"]["responses"]
                ).replace("[pizza]", standardize_result(detected_entity["Pizza"][0]))

        if intent == "modify_cart_item":
            pass

        if intent == "provide_info":
            pass

        return random.choice(self.responses_template["Unknown"]["responses"])

    def handle_view_menu(self, message):
        entities = self.identify_entities(message)
        if "Pizza" in entities:
            pass
        pass

    def handle_message(self, message):
        message_intent = self.identify_intent(message)
        if not message_intent:
            return random.choice(self.responses_template["Unknown"]["responses"])
        elif message_intent == "view_menu":
            return self.handle_view_menu(message)
