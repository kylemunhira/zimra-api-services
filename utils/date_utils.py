import datetime

def get_close_day_string_date() -> str:
    """
    Returns the current date in 'YYYY-MM-DD' format.

    This is typically used for closing a fiscal day with the ZIMRA API.

    Returns:
        str: Formatted current date as 'YYYY-MM-DD'.
    """
    return datetime.datetime.today().strftime("%Y-%m-%d")
