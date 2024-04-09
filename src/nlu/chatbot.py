import torch
from transformers import AutoTokenizer
from utils.chatbot_utils import translate_result
from nlu.payload.payload_cart_item import PayloadCartItem
from nlu.payload.payload_customer_info import PayloadCustomerInfo
from models.intents.phobert_pizza_intent import PhoBertPizzaIntent
from models.entities.crf_pizza_entity import CRFPizzaEntity

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
    def __init__(self, model_entity_path, model_intent_path):
        self.model_entity = self._load_model_entity(model_entity_path)
        self.model_intent = self._load_model_intent(model_intent_path)
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

    def predict_entity(self, text):
        result = self.model_entity.predict(text)
        quantities = result.get("Quantity", [])
        pizza = result.get("Pizza", [])
        size = result.get("Size", [])
        topping = result.get("Topping", [])
        crust = result.get("Crust", [])
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
                return translate_result(intent_labels[idx])
        return "Không nhận diện được ý định"

    def predict(self, text):
        intent = self.predict_intent(text)

        entity = None
        if intent in [
            "View Menu",
            "View Cart",
            "Add To Cart",
            "Remove From Cart",
            "Modify Cart Item",
            "Provide Info",
        ]:
            entity = self.predict_entity(text)

        return f"Intent: {intent}\nEntity: {entity}"
