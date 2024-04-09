import torch.nn as nn
from transformers import AutoModel


class PhoBertPizzaIntent(nn.Module):
    def __init__(self):
        super(PhoBertPizzaIntent, self).__init__()
        self.phobert = AutoModel.from_pretrained("vinai/phobert-base")
        self.dropout = nn.Dropout(p=0.3)
        self.linear = nn.Linear(768, 10)

    def forward(self, input_ids, attn_mask, token_type_ids):
        output = self.phobert(
            input_ids, attention_mask=attn_mask, token_type_ids=token_type_ids
        )
        output_dropout = self.dropout(output.pooler_output)
        output = self.linear(output_dropout)
        return output
