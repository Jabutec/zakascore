import re
from datetime import date, datetime, timezone
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

E164_PATTERN = re.compile(r"^\+[1-9][0-9]{7,14}$")
# 8 characters, unambiguous alphabet (no I, O, 0, 1). Generate with `secrets`.
CODE_PATTERN = r"^[A-HJ-NP-Z2-9]{8}$"


class StrictModel(BaseModel):
    """Unknown fields raise instead of being silently accepted."""

    model_config = ConfigDict(extra="forbid")


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


class ConnectCodePurpose(str, Enum):
    LINK_WHATSAPP = "link_whatsapp"
    CLAIM_MERCHANT = "claim_merchant"


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
    external_identifier: str | None = None  # WhatsApp: E.164 number
    is_active: bool = True
    created_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_whatsapp_number(self):
        if self.source_type == SourceType.WHATSAPP:
            if not self.external_identifier or not E164_PATTERN.match(
                self.external_identifier
            ):
                raise ValueError(
                    "whatsapp data sources need an E.164 number, e.g. +27821234567"
                )
        return self


class ConnectCode(StrictModel):
    code: str = Field(pattern=CODE_PATTERN)
    purpose: ConnectCodePurpose
    store_id: StoreID
    created_by_user_id: UUID | None = None  # required for link_whatsapp
    expires_at: AwareDatetime
    used_at: AwareDatetime | None = None
    used_by_user_id: UUID | None = None     # required once a claim_merchant code is used
    created_at: AwareDatetime | None = None

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value):
        # Users type codes by hand into WhatsApp / the dashboard.
        return value.strip().upper() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_purpose_rules(self):
        if (
            self.purpose == ConnectCodePurpose.LINK_WHATSAPP
            and self.created_by_user_id is None
        ):
            raise ValueError("link_whatsapp codes require created_by_user_id")
        if (
            self.purpose == ConnectCodePurpose.CLAIM_MERCHANT
            and self.used_at is not None
            and self.used_by_user_id is None
        ):
            raise ValueError("used claim_merchant codes require used_by_user_id")
        return self

    @property
    def used(self) -> bool:
        return self.used_at is not None


class TransactionBase(StrictModel):
    store_id: StoreID  # merchant is derived via the store
    source_id: SourceID
    offering_id: OfferingID | None = None
    quantity: int | None = Field(default=None, gt=0)
    input_type: InputType
    # NUMERIC(12,2): reject extra precision here instead of letting Postgres round it
    amount_zar: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    payment_method: PaymentMethod | None = None
    raw_message: str | None = None
    whatsapp_message_id: str | None = None

    @model_validator(mode="after")
    def validate_input_rules(self):
        if self.input_type == InputType.WHATSAPP:
            if self.offering_id is None or self.quantity is None:
                raise ValueError(
                    "offering_id and quantity are required for whatsapp transactions"
                )
            if not self.whatsapp_message_id:
                raise ValueError(
                    "whatsapp_message_id (Twilio MessageSid) is required for "
                    "whatsapp transactions"
                )
        elif self.payment_method is None:
            raise ValueError(
                f"payment_method is required for input_type '{self.input_type.value}'"
            )
        return self


class TransactionCreate(TransactionBase):
    """Validate this BEFORE inserting. Postgres generates transaction_id."""

    transaction_date: AwareDatetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


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