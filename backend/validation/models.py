from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

TransactionID = UUID
MerchantID = UUID
StoreID = UUID
SourceID = UUID
SnapshotID = UUID
OfferingID = UUID

MAX_FUTURE_TRANSACTION_DATE = timedelta(minutes=5)
MAX_PAST_TRANSACTION_AGE = timedelta(days=30)


class StrictModel(BaseModel):
    """Unknown fields raise instead of being silently accepted."""

    model_config = ConfigDict(extra="forbid")


class InputType(str, Enum):
    POS_TAP = "pos_tap"
    VOICE = "voice"
    MANUAL = "manual"
    PWA = "pwa"
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
    PWA = "pwa"
    CSV = "csv"
    MANUAL = "manual"


class Merchant(StrictModel):
    merchant_id: MerchantID
    business_name: str
    location: str | None = None
    tier: Tier = Tier.INSIGHTS
    created_at: AwareDatetime | None = None


class MerchantUser(StrictModel):
    user_id: UUID  # Neon Auth user id (JWT sub)
    merchant_id: MerchantID
    role: Role = Role.OWNER
    created_at: AwareDatetime | None = None


class Store(StrictModel):
    store_id: StoreID
    merchant_id: MerchantID
    store_name: str
    location: str | None = None
    created_at: AwareDatetime | None = None


class DataSource(StrictModel):
    source_id: SourceID
    store_id: StoreID
    source_name: str
    source_type: SourceType
    external_identifier: str | None = None
    is_active: bool = True
    created_at: AwareDatetime | None = None


class ConnectCode(StrictModel):
    code: str
    store_id: StoreID
    expires_at: AwareDatetime
    used_at: AwareDatetime | None = None
    created_at: AwareDatetime | None = None


class TransactionBase(StrictModel):
    store_id: StoreID  # merchant is derived via the store
    source_id: SourceID
    client_txn_id: UUID
    offering_id: OfferingID | None = None
    quantity: int | None = Field(default=None, gt=0)
    input_type: InputType
    # NUMERIC(12,2): reject extra precision here instead of letting Postgres round it
    amount_zar: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    payment_method: PaymentMethod

    @model_validator(mode="after")
    def validate_input_rules(self):
        if self.quantity is not None and self.offering_id is None:
            raise ValueError("offering_id is required when quantity is provided")
        return self


class TransactionCreate(TransactionBase):
    """Validate this BEFORE inserting. Postgres generates transaction_id."""

    transaction_date: AwareDatetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("transaction_date")
    @classmethod
    def validate_transaction_date(cls, value):
        now = datetime.now(timezone.utc)
        if value > now + MAX_FUTURE_TRANSACTION_DATE:
            raise ValueError("transaction_date cannot be more than 5 minutes in the future")
        if value < now - MAX_PAST_TRANSACTION_AGE:
            raise ValueError("transaction_date cannot be more than 30 days in the past")
        return value


class Transaction(TransactionBase):
    """A row read back from the database."""

    transaction_id: TransactionID
    is_voided: bool = False
    voided_at: AwareDatetime | None = None
    void_reason: str | None = None
    transaction_date: AwareDatetime
    created_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_void_state(self):
        if self.is_voided != (self.voided_at is not None):
            raise ValueError("is_voided must match whether voided_at is set")
        return self


class Offering(StrictModel):
    offering_id: OfferingID
    store_id: StoreID
    offering_name: str
    created_at: AwareDatetime | None = None


class FinancialSnapshot(StrictModel):
    snapshot_id: SnapshotID
    store_id: StoreID
    period_start: date
    period_end: date
    total_revenue_zar: Decimal = Field(ge=0)
    transaction_count: int = Field(ge=0)
    average_transaction_zar: Decimal = Field(ge=0)
    cash_revenue_zar: Decimal = Field(ge=0)
    digital_revenue_zar: Decimal = Field(ge=0)
    revenue_growth_pct: Decimal | None = None
    revenue_volatility: Decimal | None = None
    created_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self