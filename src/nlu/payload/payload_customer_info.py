import json


class PayloadCustomerInfo:
    def __init__(
        self,
        customer_name: str,
        phone_number: str,
        address: str,
        payment_method: str,
    ):
        self.customer_name = customer_name
        self.phone_number = phone_number
        self.address = address
        self.payment_method = payment_method

    def __str__(self):
        return f"CustomerInfo:\nCustomer Name: {self.customer_name}\nPhone Number: {self.phone_number}\nAddress: {self.address}\nPayment Method: {self.payment_method}"

    def to_json(self):
        return json.dumps(
            {
                "customerName": self.customer_name,
                "phoneNumber": self.phone_number,
                "address": self.address,
                "paymentMethod": self.payment_method,
            },
            ensure_ascii=False,
        )
