import re

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")
SSN = re.compile(r"\\b\\d{3}-\\d{2}-\\d{4}\\b")
CC = re.compile(r"\\b(?:\\d[ -]*?){13,16}\\b")

FORBIDDEN = ["password", "credit card", "ssn"]

def check_spec(spec: dict) -> list[str]:
    errors = []
    if spec.get("name", "").startswith("unsafe_"):
        errors.append("prompt name cannot start with 'unsafe_'")
    return errors

def check_render(text: str, context: dict) -> list[str]:
    errors = []
    if EMAIL.search(text):
        errors.append("PII detected: email")
    if SSN.search(text):
        errors.append("PII detected: ssn")
    if CC.search(text):
        errors.append("PII detected: credit card")
    lowered = text.lower()
    if any(f in lowered for f in FORBIDDEN):
        errors.append("forbidden phrase detected")
    return errors
