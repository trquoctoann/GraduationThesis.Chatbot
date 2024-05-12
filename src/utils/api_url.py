from enum import Enum


class APIUrls(Enum):
    PRODUCT_SERVICE = "http://localhost:8082/api/products"
    CART_SERVICE = "http://localhost:8082/api/carts"
    CART_ITEM_SERVICE = "http://localhost:8082/api/cart-items"
