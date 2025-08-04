import datetime


""" def get_fiscal_day_open_date_time(open_day_date_time:str):
    return get_fiscal_day_open_date_time_dao(open_day_date_time) """


def generate_counters(private_key: str, device_id: str, date_string: str , close_day_date : str , fiscal_day_no : int  ) -> list:
    current_date = datetime.datetime.today().strftime("%Y-%m-%d")
    """     current_datetime = get_fiscal_day_open_date_time(
        open_day_date_time=date_string
    ) """
    