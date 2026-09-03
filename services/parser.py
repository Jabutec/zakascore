import re
from word2number import w2n


def extract_amount(message: str) -> float | None:
    digit_matches = re.findall(r'\d+(?:[.,]\d{1,2})?', message)

    if len(digit_matches) == 1:
        return float(digit_matches[0].replace(',', '.'))
    elif len(digit_matches) > 1:
        return None

    try:
        return float(w2n.word_to_num(message))
    except ValueError:
        return None