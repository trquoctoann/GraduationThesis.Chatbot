import json
import re
import unicodedata


def read_tokenize_dictionary(dictionary_path="utils/tokenize_dictionary.json"):
    with open(dictionary_path, "r", encoding="utf-8") as file:
        tokenize_dictionary = json.load(file)
    return tokenize_dictionary


def read_stop_word_dictionary(dictionary_path="utils/vietnamese-stopwords.txt"):
    with open(dictionary_path, "r", encoding="utf-8") as file:
        stopwords_dictionary = file.read()
    return set(stopwords_dictionary.split("\n"))


def lowercase_text(text: str):
    return text.lower()


def remove_diacritic(text: str):
    nfkd_form = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).replace(
        "đ", "d"
    )


def tokenize(text: str, tokenize_dictionary: dict):
    sorted_items = sorted(
        tokenize_dictionary.items(), key=lambda x: len(x[0]), reverse=True
    )
    for original, token in sorted_items:
        pattern = re.compile(r"\b" + re.escape(original) + r"\b", re.IGNORECASE)
        text = pattern.sub(token, text)
    return text


def combined_tokenize(text: str, tokenize_dictionary: dict):
    tokenized_text = tokenize(text, tokenize_dictionary)

    list_token_tokenized_text = tokenized_text.split()
    token_diacritic_map = {}
    no_diacritic_text = ""
    for index, token in enumerate(list_token_tokenized_text):
        if "_" not in token:
            token_diacritic_map[remove_diacritic(token)] = index
            no_diacritic_text += remove_diacritic(token) + " "
    no_diacritic_text = no_diacritic_text.strip()

    no_diacritic_tokenized_text = tokenize(no_diacritic_text, tokenize_dictionary)
    for no_diacritic_token in no_diacritic_tokenized_text.split():
        if "_" in no_diacritic_token:
            start_of_word = float("inf")
            end_of_word = float("-inf")
            for part_token in no_diacritic_token.split("_"):
                part_token = remove_diacritic(part_token)
                start_of_word = min(start_of_word, token_diacritic_map.get(part_token))
                end_of_word = max(end_of_word, token_diacritic_map.get(part_token)) + 1
            list_token_tokenized_text[start_of_word:end_of_word] = [no_diacritic_token]

    return " ".join([token for token in list_token_tokenized_text])


def remove_stopwords(text: str, stopwords_dictionary: set):
    stopwords_regex = "|".join(
        re.escape(stopword)
        for stopword in sorted(stopwords_dictionary, key=len, reverse=True)
    )
    text = re.sub(r"\b(?:" + stopwords_regex + r")(?:\W|$)", " ", text)
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def ner_preprocessing(
    text: str,
    tokenize_dictionary: dict = read_tokenize_dictionary(),
    stopwords_dictionary: set = read_stop_word_dictionary(),
):
    text = lowercase_text(text)
    text = combined_tokenize(text, tokenize_dictionary)
    text = remove_stopwords(text, stopwords_dictionary)
    return text
