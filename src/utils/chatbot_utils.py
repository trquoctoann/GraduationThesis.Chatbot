from fuzzywuzzy import fuzz, process

from utils.custom_exception import InvalidProductName


def get_pure_info(raw_result: str):
    raw_result = (
        raw_result.replace("_", " ")
        .replace("đế bánh", "")
        .replace("vỏ bánh", "")
        .replace("đáy bánh", "")
        .replace("loại bánh", "")
        .replace("đế pizza", "")
        .replace("vỏ pizza", "")
        .replace("lớp vỏ", "")
        .replace("viền bánh", "")
        .replace("nền bánh", "")
        .replace("đế", "")
        .replace("đáy", "")
        .replace("vỏ", "")
        .replace("viền", "")
        .replace("vành", "")
        .replace("nền", "")
        .replace("loại", "")
        .strip()
    )
    return raw_result


def verify_product_name(entity: dict):
    topping_name = {
        "phômát",
        "thịt hun khói",
        "jăm bông",
        "gà",
        "xúc xích Đức",
        "xúc xích Mỹ",
        "dứa",
        "nấm rơm",
        "ôliu đen",
        "thịt bò xay",
        "cá",
        "tôm",
        "mực",
        "ngao",
        "ớt xanh",
        "hành tây",
        "cá thu",
        "cá cơm",
        "bắp",
        "ba chỉ bò nướng",
        "thanh Cua",
        "sò điệp",
    }
    return


def get_correct_pizza_name(ordered_pizzas: list):
    def filter_pizza_name(ordered_pizza: str):
        return (
            ordered_pizza.replace("_", " ")
            .replace("bánh pizza", "")
            .replace("chiếc pizza", "")
            .replace("cái pizza", "")
            .replace("bánh", "")
            .replace("cái", "")
            .replace("chiếc", "")
            .replace("pizza", "")
        )

    result = []
    for ordered_pizza in ordered_pizzas:
        ordered_pizza = filter_pizza_name(ordered_pizza)
        correct_pizza_names = [
            "margherita",
            "hawaiian",
            "tropicana seafood",
            "bbq beefy",
            "bbq chicken",
            "new oceania",
            "double cheese burger",
            "meat lovers",
            "seafood",
            "seafood deluxe",
            "pepperoni",
        ]
        best_match = process.extractOne(
            ordered_pizza, correct_pizza_names, scorer=fuzz.ratio
        )
        if best_match[1] < 50:
            raise InvalidProductName("Invalid pizza", ordered_pizza)
        result.append(best_match[0])
    return result


def get_correct_size(specified_size: str):
    def filter_size(specified_size: str):
        return (
            specified_size.replace("_", " ")
            .replace("size", "")
            .replace("kích cỡ", "")
            .replace("kích thước", "")
            .replace("độ lớn", "")
            .replace("cỡ", "")
            .replace("bé", "s")
            .replace("nhỏ", "s")
            .replace("vừa", "l")
            .replace("bình thường", "l")
            .replace("thường", "l")
            .replace("trung bình", "l")
            .replace("lớn", "xl")
            .replace("bự", "xl")
            .replace("to", "xl")
        )

    specified_size = filter_size(specified_size)
    size_name = {"s", "l", "xl"}
    if specified_size not in size_name:
        raise InvalidProductName("Invalid size", specified_size)
    return specified_size


def get_quantity_in_number(ordered_quantity: str):
    def translate_quantity(ordered_quantity: str):
        return (
            ordered_quantity.replace("_", " ")
            .replace("mười một", 11)
            .replace("mười hai", 12)
            .replace("mười ba", 13)
            .replace("mười bốn", 14)
            .replace("mười lăm", 15)
            .replace("mười sáu", 16)
            .replace("mười bảy", 17)
            .replace("mười tám", 18)
            .replace("mười chín", 19)
            .replace("hai mươi", 20)
            .replace("không", 0)
            .replace("một", 1)
            .replace("hai", 2)
            .replace("ba", 3)
            .replace("bốn", 4)
            .replace("năm", 5)
            .replace("sáu", 6)
            .replace("bảy", 7)
            .replace("tám", 8)
            .replace("chín", 9)
        )
