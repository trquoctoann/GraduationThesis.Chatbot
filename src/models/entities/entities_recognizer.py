import re

from joblib import load

from models.utils.preprocessing import preprocessing

order_labels = ["Quantity", "Pizza", "Topping", "Size", "Crust", "O"]
customer_info_labels = [
    "B-Cus",
    "I-Cus",
    "B-Phone",
    "B-Address",
    "I-Address",
    "B-Payment",
    "I-Payment",
    "O",
]


class EntitiesRecognizer:
    def __init__(self, model_path: str, is_order: bool):
        self.model = self._load_model(model_path)
        self.labels = order_labels if is_order else customer_info_labels
        self.is_order = is_order

    def _load_model(self, model_path):
        return load(model_path)

    def word2features(self, sentence, i):
        word = sentence[i]
        features = {
            "bias": 1.0,
            "word.lower()": word.lower(),
            "word[-3:]": word[-3:],
            "word[-2:]": word[-2:],
            "word.isupper()": word.isupper(),
            "word.isdigit()": word.isdigit(),
        }
        if i > 0:
            word1 = sentence[i - 1]
            features.update(
                {
                    "-1:word.lower()": word1.lower(),
                    "-1:word.isupper()": word1.isupper(),
                    "-1:word.isdigit()": word1.isdigit(),
                }
            )
        else:
            features["BOS"] = True

        if i < len(sentence) - 1:
            word1 = sentence[i + 1]
            features.update(
                {
                    "+1:word.lower()": word1.lower(),
                    "+1:word.isupper()": word1.isupper(),
                    "+1:word.isdigit()": word1.isdigit(),
                }
            )
        else:
            features["EOS"] = True

        return features

    def sentence_features(self, words):
        return [self.word2features(words, i) for i in range(len(words))]

    def sentence_labels(self, labels):
        return labels

    def process_sentence(self, sentence):
        tokens = re.findall(r"[\w']+|[.,!?;]", sentence)
        return {
            "words": tokens,
            "label": ["O"] * len(tokens),
        }

    def predict(self, text):
        text = preprocessing(text, True)
        processed_sentence = self.process_sentence(text)
        words = processed_sentence["words"]
        features = self.sentence_features(words)

        labels = self.model.predict([features])[0]

        result = {
            "words": words,
            "label": labels,
        }
        if self.is_order:
            return self.reformat_order_result(result)
        return self.reformat_customer_result(result)

    def reformat_order_result(self, predicted_result):
        output_dict = {}
        for index, (word, label) in enumerate(
            zip(predicted_result["words"], predicted_result["label"])
        ):
            if label == "O":
                continue
            if label not in output_dict:
                output_dict[label] = []
            output_dict[label].append((word, index))
        return output_dict

    def reformat_customer_result(self, predicted_result):
        aggregated_entities = {}
        current_entity = None
        current_label = None

        for word, label in zip(predicted_result["words"], predicted_result["label"]):
            if label.startswith("B-"):
                if current_entity is not None and current_label is not None:
                    if current_label in aggregated_entities:
                        aggregated_entities[current_label].append(
                            " ".join(current_entity)
                        )
                    else:
                        aggregated_entities[current_label] = [" ".join(current_entity)]

                current_entity = [word]
                current_label = label[2:]
            elif (
                label.startswith("I-")
                and current_entity is not None
                and label[2:] == current_label
            ):
                current_entity.append(word)
            else:
                if current_entity is not None and current_label is not None:
                    if current_label in aggregated_entities:
                        aggregated_entities[current_label].append(
                            " ".join(current_entity)
                        )
                    else:
                        aggregated_entities[current_label] = [" ".join(current_entity)]
                    current_entity = None
                    current_label = None
                if label == "O":
                    continue
                else:
                    aggregated_entities[label] = aggregated_entities.get(label, []) + [
                        word
                    ]

        if current_entity is not None and current_label is not None:
            if current_label in aggregated_entities:
                aggregated_entities[current_label].append(" ".join(current_entity))
            else:
                aggregated_entities[current_label] = [" ".join(current_entity)]

        return aggregated_entities
