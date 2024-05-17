from enum import Enum


class APIUrls(Enum):
    PRODUCT_SERVICE = "http://localhost:8082/api/products/all?categoryId.equals=1"
    CART_SERVICE = "http://localhost:8082/api/carts/all"
    CART_ITEM_SERVICE = "http://localhost:8082/api/cart-items"
    OPTION_DETAIL_SERVICE = "ttp://localhost:8082/api/option-details/all"
