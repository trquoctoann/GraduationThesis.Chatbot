class InvalidProduct(Exception):
    def __init__(self, product_name, message):
        self.product_name = product_name
        self.message = message
        super().__init__(self.message)
