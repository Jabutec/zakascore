from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse
from datetime import datetime
import sqlite3
import os

from settings.onboarding import get_merchant_by_number, create_merchant, generate_next_transaction_id
from services.parser import extract_amount
from services.transcription import transcribe_audio
from config.tiers import has_reached_limit
from validation.models import Transaction, InputType

app = FastAPI()

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "zakascore.db")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")


def get_db():
    return sqlite3.connect(DB_PATH)


@app.post("/webhook")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(""),
    NumMedia: str = Form("0"),
    MediaUrl0: str = Form(None)
):
    whatsapp_number = From.replace("whatsapp:", "")
    conn = get_db()

    merchant = get_merchant_by_number(whatsapp_number, conn)

    if merchant is None:
        if Body.lower().startswith("register:"):
            business_name = Body.split(":", 1)[1].strip()
            create_merchant(whatsapp_number, business_name, conn)
            reply = "Registered! Now send your sale amounts anytime, e.g. 300"
        else:
            reply = "Welcome to ZakaScore. To get started, send: register: Your Business Name"
        conn.close()
        return PlainTextResponse(reply)

    if has_reached_limit(merchant.merchant_id, merchant.tier, conn):
        conn.close()
        return PlainTextResponse("Transaction not recorded — you've reached your daily limit.")

    if int(NumMedia) > 0 and MediaUrl0:
        text = transcribe_audio(MediaUrl0, (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        if text is None:
            conn.close()
            return PlainTextResponse("We couldn't process that voice note. Please try again.")
    else:
        text = Body

    amount = extract_amount(text)

    if amount is None:
        conn.close()
        return PlainTextResponse(
            "We couldn't log that — please send just the amount you made, e.g. 300"
        )

    transaction = Transaction(
    transaction_id=generate_next_transaction_id(conn),
    merchant_id=merchant.merchant_id,
    source_id="S005",
    input_type=InputType.WHATSAPP,
    amount_zar=amount,
    raw_message=text,
    transaction_date=datetime.now()
)

    conn.execute(
        """INSERT INTO transactions 
           (transaction_id, merchant_id, source_id, input_type, amount_zar, raw_message)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (transaction.transaction_id, transaction.merchant_id, transaction.source_id,
         transaction.input_type.value, transaction.amount_zar, transaction.raw_message)
    )
    conn.commit()
    conn.close()

    return PlainTextResponse(f"Logged: R{amount}")