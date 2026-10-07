from datetime import date, datetime
from pydantic import BaseModel, Field, model_validator
from enum import Enum
from typing import Annotated

TransactionID = Annotated[str, Field(pattern=r"^T\d{3}$")]
MerchantID = Annotated[str, Field(pattern=r"^M\d{3}$")]
StoreID = Annotated[str, Field(pattern=r"^ST\d{3}$")]
SourceID = Annotated[str, Field(pattern=r"^S\d{3}$")]
SnapshotID = Annotated[str, Field(pattern=r"^F\d{3}$")]
OfferingID = Annotated[str, Field(pattern=r"^O\d{3}$")]


class InputType(str, Enum):
    POS_TAP = "pos_tap"
    VOICE = "voice"
    MANUAL = "manual"
    WHATSAPP = "whatsapp"
    CSV = "csv"
    API = "api"


class PaymentMethod(str, Enum):
    CASH = "cash"
    DIGITAL = "digital"


class Tier(str, Enum):
    INSIGHTS = "insights"
    FULL = "full"


class Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EMPLOYEE = "employee"
    VIEWER = "viewer"


class SourceType(str, Enum):
    POS = "pos"
    BANK_STATEMENT = "bank_statement"
    ACCOUNTING_SOFTWARE = "accounting_software"
    ONLINE_STORE = "online_store"
    WHATSAPP = "whatsapp"
    CSV = "csv"
    MANUAL = "manual"


class Merchant(BaseModel):
    merchant_id: MerchantID
    business_name: str
    location: str | None = None
    tier: Tier = Tier.INSIGHTS
    created_at: datetime | None = None


class MerchantUser(BaseModel):
    user_id: str  # Neon Auth-issued UUID string
    merchant_id: MerchantID
    role: Role = Role.OWNER
    created_at: datetime | None = None


class Store(BaseModel):
    store_id: StoreID
    merchant_id: MerchantID
    store_name: str
    location: str | None = None
    created_at: datetime | None = None


class DataSource(BaseModel):
    source_id: SourceID
    store_id: StoreID
    source_name: str
    source_type: SourceType
    external_identifier: str | None = None  # e.g. the WhatsApp number
    created_at: datetime | None = None


class ConnectCode(BaseModel):
    code: str
    store_id: StoreID
    merchant_id: MerchantID | None = None
    used: bool = False
    expires_at: datetime
    created_at: datetime | None = None


class Transaction(BaseModel):
    transaction_id: TransactionID
    store_id: StoreID
    source_id: SourceID
    offering_id: OfferingID | None = None
    quantity: int | None = None
    input_type: InputType | None = None
    amount_zar: float = Field(gt=0)
    payment_method: PaymentMethod | None = None
    raw_message: str | None = None
    whatsapp_message_id: str | None = None
    is_voided: bool = False
    transaction_date: datetime

    @model_validator(mode="after")
    def validate_payment_method(self):
        if self.input_type != InputType.WHATSAPP and self.payment_method is None:
            raise ValueError(
                f"payment_method is required for input_type '{self.input_type}'"
            )
        if self.input_type == InputType.WHATSAPP:
            if self.offering_id is None or self.quantity is None:
                raise ValueError(
                    "offering_id and quantity are required for whatsapp transactions"
                )
        return self


class Offering(BaseModel):
    offering_id: OfferingID
    store_id: StoreID
    offering_name: str
    created_at: datetime | None = None


class FinancialSnapshot(BaseModel):
    snapshot_id: SnapshotID
    store_id: StoreID
    period_start: date
    period_end: date
    total_revenue_zar: float = Field(ge=0)
    transaction_count: int = Field(ge=0)
    average_transaction_zar: float = Field(ge=0)
    cash_revenue_zar: float = Field(ge=0)
    digital_revenue_zar: float = Field(ge=0)
    revenue_growth_pct: float | None = None
    revenue_volatility: float | None = None
    created_at: datetime | None = None

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self