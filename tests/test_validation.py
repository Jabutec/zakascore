from datetime import datetime
from validation.models import Transaction

transaction = Transaction(
    transaction_id = "T001",
    merchant_id = "M001",
    source_id = "S001",
    input_type = "Pos",
    amount_zar = 450.00,
    payment_method = "digital",
    transaction_date = datetime.now()
)

print(transaction)