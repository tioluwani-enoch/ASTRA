from datetime import datetime, date


def today_str() -> str:
    return date.today().isoformat()


def now_str() -> str:
    return datetime.now().isoformat()


def friendly_date() -> str:
    return date.today().strftime("%A, %B %d %Y")
