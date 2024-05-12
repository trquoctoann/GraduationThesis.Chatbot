class InvalidProductName(Exception):
    def __init__(self, message, product_name):
        self.message = message
        self.product_name = product_name
        super().__init__(f"{message}: {product_name}")
