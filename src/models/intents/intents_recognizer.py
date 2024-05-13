import torch
import torch.nn as nn
import numpy as np
from transformers import AutoModel, AutoTokenizer
from models.utils.preprocessing import preprocessing

THRESHOLD = 0.99
MAX_LEN = 128
device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")


class IntentsRecognizer(nn.Module):
    def __init__(self):
        super(IntentsRecognizer, self).__init__()
        self.phobert = AutoModel.from_pretrained("vinai/phobert-base")
        self.dropout = nn.Dropout(p=0.3)
        self.linear = nn.Linear(768, 9)
        self.intent_labels = [
            "view_menu",
            "view_cart",
            "add_to_cart",
            "remove_from_cart",
            "modify_cart_item",
            "confirm_order",
            "track_order",
            "cancel_order",
            "provide_info",
        ]
        self.intent_tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base", use_fast=False)

    def forward(self, input_ids, attn_mask, token_type_ids):
        output = self.phobert(input_ids, attention_mask=attn_mask, token_type_ids=token_type_ids)
        output_dropout = self.dropout(output.pooler_output)
        output = self.linear(output_dropout)
        return output

    def predict(self, text):
        text = preprocessing(text, False)
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
        output = self(input_ids, attention_mask, token_type_ids)
        probabilities = torch.softmax(output, dim=-1).detach().cpu().numpy().flatten()

        max_prob = np.max(probabilities)
        max_prob_index = np.argmax(probabilities)

        if max_prob >= THRESHOLD:
            return self.intent_labels[max_prob_index]
        else:
            return None
