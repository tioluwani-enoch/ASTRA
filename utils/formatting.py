def truncate(text: str, max_len: int = 80) -> str:
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"• {item}" for item in items)
