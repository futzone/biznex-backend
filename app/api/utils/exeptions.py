class InsufficientStockError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class PaymentRequiredError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
