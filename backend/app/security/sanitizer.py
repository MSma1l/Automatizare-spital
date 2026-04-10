import bleach
import re

ALLOWED_TAGS = ["b", "i", "u", "em", "strong", "p", "br"]
ALLOWED_ATTRIBUTES = {}


def sanitize_html(text: str) -> str:
    if not text:
        return text
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)


def sanitize_string(text: str) -> str:
    if not text:
        return text
    text = text.strip()
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('\x00', '')
    return text


def sanitize_filename(filename: str) -> str:
    filename = re.sub(r'[^\w\s\-.]', '', filename)
    filename = filename.strip('. ')
    return filename if filename else 'unnamed'
