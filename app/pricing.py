def calculate_total(price: float, quantity: int) -> float:
    if price < 0:
        raise ValueError("Price cannot be negative")
    if quantity <= 0:
        raise ValueError("Quantity must be positive")
    return round(price * quantity, 2)


def apply_discount(total: float, percent: float) -> float:
    if percent < 0 or percent > 100:
        raise ValueError("Discount must be between 0 and 100")
    return round(total * (1 - percent / 100), 2)


def delivery_fee(total: float, express: bool = False) -> float:
    if total < 0:
        raise ValueError("Total cannot be negative")
    if total >= 200:
        return 0.0
    if express:
        return 25.0
    return 10.0


def order_total(
    price: float,
    quantity: int,
    discount: float = 0,
    express: bool = False
) -> float:
    subtotal = calculate_total(price, quantity)
    discounted = apply_discount(subtotal, discount)
    return round(
        discounted + delivery_fee(discounted, express), 2
    )
