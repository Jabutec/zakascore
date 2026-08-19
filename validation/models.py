from datetime import date, datetime
from pydantic import BaseModel, Field, model_validator
from enum import Enum
from typing import Annotated

TransactionID = Annotated[str,Field(pattern=r"^T\d{3}$")]
MerchantID = Annotated[str, Field(pattern=r"^M\d{3}$")]
SourceID = Annotated[str,Field(pattern=r"^S\d{3}$")]

class InputType(str, Enum):
    POS_TAP = "pos_tap"
    VOICE = "voice"
    MANUAL = "manual"

class PaymentMethod(str, Enum):
    CASH = "cash"
    DIGITAL = "digital"

class Transaction(BaseModel):
    transaction_id: TransactionID
    merchant_id: MerchantID
    source_id: SourceID
    input_type: InputType | None = None
    amount_zar: float = Field(gt=0)
    payment_method: PaymentMethod
    transaction_date: datetime
    
class Merchant(BaseModel):
    merchant_id: MerchantID
    business_name: str
    location: str
    created_at: datetime | None = None
    
class SourceType(str, Enum):
    POS = "pos"
    BANK_STATEMENT = "bank_statement"
    ACCOUNTING_SOFTWARE = "accounting_software"
    ONLINE_STORE = "online_store"

class DataSource(BaseModel):
    source_id: SourceID
    source_name: str
    source_type: SourceType
    created_at: datetime
    
class FinancialSnapshot(BaseModel):
    snapshot_id: str
    merchant_id: MerchantID
    period_start: date
    period_end: date
    total_revenue_zar: float = Field(ge=0)
    transaction_count: float = Field(ge=0)
    average_transaction_zar: float = Field(ge=0)
    cash_revenue_zar: float = Field(ge=0)
    digital_revenue_zar: float = Field(ge=0)
    revenue_growth_pct: float | None = None
    revenue_volatility: float | None = None
    created_at: datetime
    
    @model_validator(mode="after")
    def validate_period(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self
    
    
    
    