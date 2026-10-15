import re
import unicodedata


def capitalize(text):
    if not isinstance(text, str) or not text:
        return ""
    return text[0].upper() + text[1:].lower()


def calculate_average(numbers):
    if not numbers:
        return 0
    return round(sum(numbers) / len(numbers), 2)


def slugify(text):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))
