def normalize_currency(code: str) -> str:
    equivalents = {
        "USD": "USDT",
    }
    return equivalents.get(code, code)
