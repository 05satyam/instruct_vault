def check_spec(spec: dict) -> list[str]:
    errors = []
    name = spec.get("name", "")
    if name.startswith("unsafe_"):
        errors.append("prompt name cannot start with 'unsafe_'")
    return errors

def check_render(text: str, context: dict) -> list[str]:
    errors = []
    forbidden = ["SSN", "credit card", "password"]
    lowered = text.lower()
    if any(f.lower() in lowered for f in forbidden):
        errors.append("rendered output contains forbidden phrase")
    return errors
