def standardize_result(raw_result: str):
    raw_result = (
        raw_result.replace("_", " ")
        .replace("bánh pizza", "")
        .replace("chiếc pizza", "")
        .replace("cái pizza", "")
        .replace("kích cỡ", "")
        .replace("kích thước", "")
        .replace("độ lớn", "")
        .replace("cỡ", "")
        .replace("size", "")
        .replace("đế bánh", "")
        .replace("vỏ bánh", "")
        .replace("đáy bánh", "")
        .replace("loại bánh", "")
        .replace("đế pizza", "")
        .replace("vỏ pizza", "")
        .replace("lớp vỏ", "")
        .replace("viền bánh", "")
        .replace("nền bánh", "")
        .replace("bánh", "")
        .replace("nhỏ", "s")
        .replace("lớn", "xl")
        .replace("vừa", "l")
        .replace("pizza", "")
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


class InvalidProductName(Exception):
    def __init__(self, message, product_name):
        self.message = message
        self.product_name = product_name
        super().__init__(f"{message}: {product_name}")


def verify_product_name(entity: dict):
    pizza_name = {
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
    }
    if "Pizza" in entity:
        for pizza in entity["Pizza"]:
            if standardize_result(pizza) not in pizza_name:
                raise InvalidProductName("Invalid pizza", standardize_result(pizza))

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

    size_name = {"s", "l", "xl"}
    if "Size" in entity:
        for size in entity["Size"]:
            if standardize_result(size) not in size_name:
                raise InvalidProductName("Invalid size", standardize_result(size))

    crust_name = {"dày", "mỏng"}
    if "Crust" in entity:
        for crust in entity["Crust"]:
            if standardize_result(crust) not in crust_name:
                raise InvalidProductName("Invalid crust", standardize_result(crust))
    return


def transform_to_payload_format():
    pass
