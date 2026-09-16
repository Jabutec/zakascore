import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


def extract_transaction_details(message: str) -> dict | None:
    prompt = f"""Extract the item or service sold, quantity, and amount in ZAR from this message.
Always return the item name in its singular form (e.g. "shirts" becomes "shirt").
Return ONLY valid JSON in this exact format: {{"item": "string", "quantity": number, "amount": number}}
If you cannot confidently extract all three (item, quantity, AND amount), return: {{"item": null, "quantity": null, "amount": null}}

Message: "{message}"
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    try:
        result = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return None

    if result.get("item") is None or result.get("quantity") is None or result.get("amount") is None:
        return None

    return result