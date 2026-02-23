from random import randint


def fetch_grn_rate(external_product_id: str) -> float:
    """
    MOCK GRN RATE FETCHER

    In future:
    - Replace this logic with actual GRN REST API call
    - Keep same function signature
    """

    # 🔥 Fake dynamic pricing simulation
    base_price = randint(3000, 8000)

    return float(base_price)
