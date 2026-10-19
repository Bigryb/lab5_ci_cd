import pytest

from app.pricing import (
    apply_discount,
    calculate_total,
    delivery_fee,
    order_total,
)


def test_calculate_total():
    assert calculate_total(100, 2) == 200


def test_negative_price():
    with pytest.raises(ValueError):
        calculate_total(-1, 2)


def test_quantity_zero():
    with pytest.raises(ValueError):
        calculate_total(100, 0)


def test_apply_discount():
    assert apply_discount(100, 10) == 90


def test_delivery_normal():
    assert delivery_fee(100) == 10


def test_order_total():
    assert order_total(100, 1, 10) == 100


def test_invalid_discount():
    with pytest.raises(ValueError):
        apply_discount(100, 120)
