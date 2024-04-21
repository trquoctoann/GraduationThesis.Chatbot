import json
import random

import torch
from transformers import AutoTokenizer

from models.entities.crf_pizza_entity import CRFPizzaEntity
from models.intents.phobert_pizza_intent import PhoBertPizzaIntent
from nlu.payload.payload_cart_item import PayloadCartItem
from nlu.payload.payload_customer_info import PayloadCustomerInfo
from utils.chatbot_utils import (
    InvalidProductName,
    standardize_result,
    verify_product_name,
)

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

MAX_LEN = 128
TRAIN_BATCH_SIZE = 16
VALID_BATCH_SIZE = 16
TEST_BATCH_SIZE = 16
EPOCHS = 10
LEARNING_RATE = 1e-05
THRESHOLD = 0.5

intent_labels = [
    "view_menu",
    "view_cart",
    "add_to_cart",
    "remove_from_cart",
    "modify_cart_item",
    "confirm_order",
    "track_order",
    "cancel_order",
    "provide_info",
    "none",
]


class Chatbot:
    def __init__(self, model_entity_path, model_intent_path, responses_template_path):
        self.model_entity = self._load_model_entity(model_entity_path)
        self.model_intent = self._load_model_intent(model_intent_path)
        self.responses_template = self._load_response_template(responses_template_path)
        self.intent_tokenizer = AutoTokenizer.from_pretrained(
            "vinai/phobert-base", use_fast=False
        )

    def _load_model_entity(self, model_path):
        model = CRFPizzaEntity(model_path)
        return model

    def _load_model_intent(self, model_path):
        model = PhoBertPizzaIntent()
        model.load_state_dict(torch.load(model_path))
        return model.to(device)

    def _load_response_template(self, responses_template_path):
        with open(responses_template_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def predict_entity(self, text):
        result = self.model_entity.predict(text)
        return result

    def predict_intent(self, text):
        encoded_text = self.intent_tokenizer.encode_plus(
            text,
            max_length=MAX_LEN,
            add_special_tokens=True,
            return_token_type_ids=True,
            pad_to_max_length=True,
            return_attention_mask=True,
            return_tensors="pt",
        )
        input_ids = encoded_text["input_ids"].to(device)
        attention_mask = encoded_text["attention_mask"].to(device)
        token_type_ids = encoded_text["token_type_ids"].to(device)
        output = self.model_intent(input_ids, attention_mask, token_type_ids)
        output = torch.sigmoid(output).detach().cpu()
        output = output.flatten().round().numpy()

        for idx, p in enumerate(output):
            if p == 1:
                return intent_labels[idx]
        return None

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

    def predict(self, text):
        intent = self.predict_intent(text)

        entity = None
        if intent in [
            "view_menu",
            "view_cart",
            "add_to_cart",
            "remove_from_cart",
            "modify_cart_item",
            "provide_info",
        ]:
            entity = self.predict_entity(text)

        return self.get_response(intent, entity)
