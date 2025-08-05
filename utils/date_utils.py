import datetime

def get_close_day_string_date() -> str:
    """
    Returns the current date in 'YYYY-MM-DDTHH:MM:SS' format.

    This is typically used for closing a fiscal day with the ZIMRA API.

    Returns:
        str: Formatted current date as 'YYYY-MM-DDTHH:MM:SS'.
    """
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
