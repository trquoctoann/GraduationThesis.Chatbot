from fuzzywuzzy import fuzz, process


def get_correct_pizza_name(ordered_pizzas: list):
    def filter_pizza_name(ordered_pizza: str):
        return (
            ordered_pizza.replace("_", " ")
            .replace("bánh pizza", "")
            .replace("chiếc pizza", "")
            .replace("cái pizza", "")
            .replace("banh pizza", "")
            .replace("chiec pizza", "")
            .replace("cai pizza", "")
            .replace("bánh", "")
            .replace("cái", "")
            .replace("chiếc", "")
            .replace("banh", "")
            .replace("cai", "")
            .replace("chiec", "")
            .replace("pizza", "")
        )

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

    valid_results = []
    errors = []

    for ordered_pizza in ordered_pizzas:
        cleaned_pizza = filter_pizza_name(ordered_pizza)
        best_match = process.extractOne(
            cleaned_pizza, correct_pizza_names, scorer=fuzz.ratio
        )
        if best_match[1] < 50:
            errors.append(best_match[0])
        else:
            valid_results.append(best_match[0])

    return valid_results, errors


def get_correct_size(specified_sizes: list):
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
            .replace("co", "")
            .replace("be", "s")
            .replace("nho", "s")
            .replace("vua", "l")
            .replace("thuong", "l")
            .replace("lon", "xl")
            .replace("bu", "xl")
        )

    size_name = {"s", "l", "xl"}
    valid_results = []
    errors = []
    for specified_size in specified_sizes:
        cleaned_size = filter_size(specified_size).strip()
        if cleaned_size not in size_name:
            errors.append(cleaned_size)
        else:
            valid_results.append(cleaned_size)
    return valid_results, errors


def get_quantity_in_number(ordered_quantities: list):
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
            .replace("mười", 10)
            .replace("muoi mot", 11)
            .replace("muoi hai", 12)
            .replace("muoi ba", 13)
            .replace("muoi bon", 14)
            .replace("muoi lam", 15)
            .replace("muoi sau", 16)
            .replace("muoi bay", 17)
            .replace("muoi tam", 18)
            .replace("muoi chin", 19)
            .replace("hai muoi", 20)
            .replace("không", 0)
            .replace("mot", 1)
            .replace("hai", 2)
            .replace("ba", 3)
            .replace("bon", 4)
            .replace("nam", 5)
            .replace("sau", 6)
            .replace("bay", 7)
            .replace("tam", 8)
            .replace("chin", 9)
            .replace("muoi", 10)
        )

    valid_results = []
    for ordered_quantity in ordered_quantities:
        try:
            valid_results.append(int(ordered_quantity))
        except ValueError:
            valid_results.append(translate_quantity(ordered_quantity))
    return valid_results


def get_correct_crust_type(specified_crusts: list):
    def filter_crust(specified_crust: str):
        return (
            specified_crust.replace("_", " ")
            .replace("đế bánh", "")
            .replace("vỏ bánh", "")
            .replace("đáy bánh", "")
            .replace("loại bánh", "")
            .replace("vỏ pizza", "")
            .replace("đế pizza", "")
            .replace("đáy pizza", "")
            .replace("lớp vỏ", "")
            .replace("viền bánh", "")
            .replace("viền pizza", "")
            .replace("nền bánh", "")
            .replace("vỏ đế", "")
            .replace("vành bánh", "")
            .replace("đế", "")
            .replace("de", "")
            .replace("vỏ", "")
            .replace("vo", "")
            .replace("đáy", "")
            .replace("day", "")
            .replace("loại", "")
            .replace("loai", "")
            .replace("viền", "")
            .replace("vien", "")
            .replace("nền", "")
            .replace("nen", "")
            .replace("vành", "")
            .replace("vanh", "")
        )

    crust_names = {"dày", "mỏng"}
    valid_results = []
    errors = []

    for specified_crust in specified_crusts:
        cleaned_crust = filter_crust(specified_crust)
        if cleaned_crust not in crust_names:
            errors.append(cleaned_crust)
        else:
            valid_results.append(cleaned_crust)
    return valid_results, cleaned_crust


def get_correct_topping_name(specified_toppings: list):
    correct_topping_names = [
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
    ]

    valid_results = []
    errors = []
    for specified_topping in specified_toppings:
        specified_topping = specified_topping.replace("_", " ")
        best_match = process.extractOne(
            specified_topping, correct_topping_names, scorer=fuzz.ratio
        )
        if best_match[1] < 50:
            errors.append(best_match[0])
        else:
            valid_results.append(best_match[0])

    return valid_results, errors
