import json
import re
import unicodedata


def read_tokenize_dictionary(dictionary_path="models/utils/tokenize_dictionary.json"):
    with open(dictionary_path, "r", encoding="utf-8") as file:
        tokenize_dictionary = json.load(file)
    return tokenize_dictionary


def read_stop_word_dictionary(dictionary_path="models/utils/vietnamese-stopwords.txt"):
    with open(dictionary_path, "r", encoding="utf-8") as file:
        stopwords_dictionary = file.read()
    return set(stopwords_dictionary.split("\n"))


def read_acronym_dictionary(dictionary_path="models/utils/acronym_dictionary.json"):
    with open(dictionary_path, "r", encoding="utf-8") as file:
        acronym_dictionary = json.load(file)
    return acronym_dictionary


def lowercase_text(text: str):
    return text.lower()


def remove_diacritic(text: str):
    nfkd_form = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).replace(
        "đ", "d"
    )


def replace_tokens(text: str, replacement_dictionary: dict):
    pattern = r"(?<=\d)/(?=\d)"
    text = re.sub(pattern, " kiệt ", text)
    sorted_items = sorted(
        replacement_dictionary.items(), key=lambda x: len(x[0]), reverse=True
    )
    for original, token in sorted_items:
        pattern = re.compile(r"\b" + re.escape(original) + r"\b", re.IGNORECASE)
        text = pattern.sub(token, text)
    return text


def translate_sentences(text: str, dictionary: dict):
    tokenized_text = replace_tokens(text, dictionary)

    list_token_tokenized_text = tokenized_text.split()
    token_diacritic_map = {}
    no_diacritic_text = ""
    for index, token in enumerate(list_token_tokenized_text):
        if "_" not in token:
            token_diacritic_map[remove_diacritic(token)] = index
            no_diacritic_text += remove_diacritic(token) + " "
    no_diacritic_text = no_diacritic_text.strip()

    no_diacritic_tokenized_text = replace_tokens(no_diacritic_text, dictionary)
    for no_diacritic_token in no_diacritic_tokenized_text.split():
        if "_" in no_diacritic_token:
            start_of_word = float("inf")
            end_of_word = float("-inf")
            for part_token in no_diacritic_token.split("_"):
                part_token = remove_diacritic(part_token)
                start_of_word = min(start_of_word, token_diacritic_map.get(part_token))
                end_of_word = max(end_of_word, token_diacritic_map.get(part_token)) + 1

            skip = False
            for word in list_token_tokenized_text[start_of_word:end_of_word]:
                if "_" in word:
                    skip = True
                    break

            if not skip:
                list_token_tokenized_text[start_of_word:end_of_word] = [
                    no_diacritic_token
                ]

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


def preprocessing(
    text: str,
    is_process_entity: bool = False,
    tokenize_dictionary: dict = read_tokenize_dictionary(),
    stopwords_dictionary: set = read_stop_word_dictionary(),
    acronym_dictionary: dict = read_acronym_dictionary(),
):
    text = lowercase_text(text)
    text = translate_sentences(text, acronym_dictionary)
    if is_process_entity:
        text = translate_sentences(text, tokenize_dictionary)
        text = remove_stopwords(text, stopwords_dictionary)
    return text
