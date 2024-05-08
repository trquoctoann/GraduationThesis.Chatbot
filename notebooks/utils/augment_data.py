import copy
import json
import random
import unicodedata


def randomly_remove_accents(word):
    if random.random() < 0.5:
        nfkd_form = unicodedata.normalize("NFKD", word)
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    else:
        return word


def process_sentence(sentence):
    new_sentence = copy.deepcopy(sentence)
    new_sentence["words"] = [
        randomly_remove_accents(word) for word in new_sentence["words"]
    ]
    return new_sentence


def augment_data(data):
    num_sentences = len(data)
    sentences_to_process_indexes = random.sample(
        range(num_sentences), k=int(0.2 * num_sentences)
    )

    augmented_sentences = [
        process_sentence(data[i]) for i in sentences_to_process_indexes
    ]
    return augmented_sentences


def increase_data_and_save(data, new_file):
    augmented_data = augment_data(data)
    combined_data = data + augmented_data

    with open(
        "../data/labeled/entity/order/" + new_file + ".json", "w", encoding="utf-8"
    ) as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=4)
    return combined_data
