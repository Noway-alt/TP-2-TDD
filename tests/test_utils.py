import pytest

from app.utils import calculate_average, capitalize, clamp, slugify


# ---------- capitalize ----------
@pytest.mark.parametrize(
    "text, expected",
    [
        ("hello", "Hello"),
        ("WORLD", "World"),
        ("hELLO wORLD", "Hello world"),
        ("", ""),
        (None, ""),
        (42, ""),
    ],
)
def test_should_capitalize_first_letter_and_lowercase_rest_when_given_text(text, expected):
    # Act
    result = capitalize(text)
    # Assert
    assert result == expected


# ---------- calculate_average ----------
@pytest.mark.parametrize(
    "numbers, expected",
    [
        ([10, 12, 14], 12),
        ([15], 15),
        ([], 0),
        ([10, 11, 12], 11),
        (None, 0),
        ([1, 2], 1.5),
        ([1, 2, 2], 1.67),
        ([-5, 5], 0),
    ],
)
def test_should_return_rounded_average_when_given_numbers(numbers, expected):
    assert calculate_average(numbers) == expected


# ---------- slugify ----------
@pytest.mark.parametrize(
    "text, expected",
    [
        ("Hello World", "hello-world"),
        ("  Spaces Everywhere  ", "spaces-everywhere"),
        ("C'est l'été !", "cest-lete"),
        ("", ""),
        (None, ""),
        ("a    b", "a-b"),
    ],
)
def test_should_return_url_slug_when_given_text(text, expected):
    assert slugify(text) == expected


# ---------- clamp ----------
@pytest.mark.parametrize(
    "value, low, high, expected",
    [
        (5, 0, 10, 5),
        (-5, 0, 10, 0),
        (15, 0, 10, 10),
        (0, 0, 0, 0),
        (10, 0, 10, 10),
        (-3.5, -5, -1, -3.5),
    ],
)
def test_should_keep_value_within_bounds_when_clamping(value, low, high, expected):
    assert clamp(value, low, high) == expected
