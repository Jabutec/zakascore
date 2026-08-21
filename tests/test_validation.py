from datetime import date, datetime
import pytest
from pydantic import ValidationError
from validation.models import(
    Transaction,
    Merchant,
    DataSource,
    FinancialSnapshot
)

@pytest.mark.parametrize("amount", [-100, -450, -0.01, 0])
def test_invalid_transaction_amount(amount):
    with pytest.raises(ValidationError):
        Transaction(
            transaction_id="T001",
            merchant_id="M001",
            source_id="S001",
            input_type="pos_tap",
            amount_zar=amount,
            payment_method="digital",
            transaction_date=datetime.now()
        )

@pytest.mark.parametrize("amount", [0.01, 1, 450, 1000])
def test_valid_transaction_amount(amount):
    transaction = Transaction(
        transaction_id="T001",
        merchant_id="M001",
        source_id="S001",
        input_type="pos_tap",
        amount_zar=amount,
        payment_method="digital",
        transaction_date=datetime.now()
    )

    assert transaction.amount_zar == amount

@pytest.mark.parametrize("payment_method", ["banana", "cheque", "Crypto"])
def test_invalid_payment_method(payment_method):
    with pytest.raises(ValidationError):
        Transaction(
            transaction_id="T001",
            merchant_id="M001",
            source_id="S001",
            input_type="pos_tap",
            amount_zar=100,
            payment_method=payment_method,
            transaction_date=datetime.now()
        )

@pytest.mark.parametrize("payment_method", ["cash", "digital"])
def test_valid_payment_method(payment_method):
    transaction = Transaction(
        transaction_id="T001",
        merchant_id="M001",
        source_id="S001",
        input_type="pos_tap",
        amount_zar=100,
        payment_method=payment_method,
        transaction_date=datetime.now()
    )
    
    assert transaction.payment_method == payment_method

@pytest.mark.parametrize("input_type", ["banana", "cheque", "inventory"])
def test_invalid_input_type(input_type):
    with pytest.raises(ValidationError):
        Transaction(
            transaction_id="T001",
            merchant_id="M001",
            source_id="S001",
            input_type=input_type,
            amount_zar=100,
            payment_method="digital",
            transaction_date=datetime.now()
        )

@pytest.mark.parametrize("input_type", ["pos_tap", "voice", "manual"])
def test_valid_input_type(input_type):
    transaction = Transaction(
        transaction_id="T001",
        merchant_id="M001",
        source_id="S001",
        input_type=input_type,
        amount_zar=100,
        payment_method="digital",
        transaction_date=datetime.now()
    )
    
    assert transaction.input_type == input_type

def test_merchant():
    merchant = Merchant(
        merchant_id= "M001",
        business_name= "vertical",
        location= "Joburg",
        created_at= datetime.now()   
    )
    
    assert merchant.merchant_id == "M001"
    
@pytest.mark.parametrize("source_type", ["cash", "object", "banana", "car"])
def test_invalid_source_type(source_type):
    with pytest.raises(ValidationError):
        DataSource(
            source_id= "S001",
            source_name = "Vertical",
            source_type=source_type,
            created_at= datetime.now()
        )
        
@pytest.mark.parametrize("source_type", ["pos", "bank_statement", "accounting_software", "online_store"])
def test_valid_source_type(source_type):
    datasource = DataSource(
        source_id= "S001",
        source_name = "Vertical",
        source_type=source_type,
        created_at= datetime.now()
    )

@pytest.mark.parametrize(
    "field", 
    [
        "total_revenue_zar",
        "cash_revenue_zar",
        "digital_revenue_zar",
        "transaction_count",
        "average_transaction_zar",
    ]
)
def test_non_negative_fields(field):
    data = {
        "snapshot_id": "S001",
        "merchant_id": "M001",
        "period_start": date(2026, 1, 1),
        "period_end": date(2026, 1, 31),
        "total_revenue_zar": 1000,
        "transaction_count": 50,
        "average_transaction_zar": 20,
        "cash_revenue_zar": 500,
        "digital_revenue_zar": 500,
        "created_at": datetime.now()
    }

    data[field] = -1

    with pytest.raises(ValidationError):
        FinancialSnapshot(**data)
        
@pytest.mark.parametrize(
    "field", 
    [
        "total_revenue_zar",
        "cash_revenue_zar",
        "digital_revenue_zar",
        "transaction_count",
        "average_transaction_zar",
    ]
)
def test_non_negative_accept_valid_fields(field):
    data = {
        "snapshot_id": "S001",
        "merchant_id": "M001",
        "period_start": date(2026, 1, 1),
        "period_end": date(2026, 1, 31),
        "total_revenue_zar": 1000,
        "cash_revenue_zar": 500,
        "digital_revenue_zar": 500,
        "transaction_count": 50,
        "average_transaction_zar": 20,
        "created_at": datetime.now()
    }
    data[field] = 100

    snapshot = FinancialSnapshot(**data)
   
    assert getattr(snapshot, field) == 100