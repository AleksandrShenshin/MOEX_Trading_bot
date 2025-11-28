import ast
import asyncio
from decouple import config
from datetime import datetime, timedelta
import iss_moex.iss_moex as iss_moex

USER_ID = None


async def set_user_id(user_id):
    global USER_ID
    USER_ID = user_id


async def get_support_instruments():
    return config('FUTURES_LIST', cast=lambda v: [s.strip() for s in v.split(',')])


async def get_support_signals():
    try:
        return ast.literal_eval(config('TYPES_SIGNAL'))
    except (SyntaxError, ValueError) as e:
        return None


async def get_precision_from_value(value):
    # 1.0 - precision=0
    # 0.001 - precision=3
    try:
        float(value)

        val1, oper, val2 = str(value).partition(".")
        if oper:
            if int(val2) == 0:
                return 0, None
            else:
                val2 = val2.rstrip('0 ')
                return len(val2), None
        else:
            return 0, None
    except ValueError:
        return -1, f"ERROR: get_precision_from_value() not correct format value for partition {value}"


async def get_ticker_family(short_ticker):
    DAYS_BEFORE_EXCHANGE = 4
    ticker_family = {'all_list': '', 'current_ticker': '', 'precision': ''}
    list_ticker = iss_moex.get_list_definite_futures(short_ticker)
    ticker_family['all_list'] = list_ticker
    for full_ticker in list_ticker:
        try:
            data_fut = iss_moex.get_data_future(full_ticker)
            if len(data_fut) == 0:
                continue

            precision, err_val = await get_precision_from_value(data_fut['minstep'])
            if precision == -1:
                return -1, None, err_val
            else:
                ticker_family['precision'] = str(precision)

            if len(ticker_family['current_ticker']) == 0:
                if (datetime.strptime(data_fut['lasttradedate'], '%Y-%m-%d') - datetime.now()) > timedelta(days=DAYS_BEFORE_EXCHANGE):
                    ticker_family['current_ticker'] = data_fut['ticker']
                    date_in_current_ticker = datetime.strptime(data_fut['lasttradedate'], '%Y-%m-%d')
            else:
                date_next_ticker = datetime.strptime(data_fut['lasttradedate'], '%Y-%m-%d')
                if date_next_ticker < date_in_current_ticker and (date_next_ticker - datetime.now()) > timedelta(days=DAYS_BEFORE_EXCHANGE):
                    ticker_family['current_ticker'] = data_fut['ticker']
                    date_in_current_ticker = datetime.strptime(data_fut['lasttradedate'], '%Y-%m-%d')
        except KeyError as e:
            return -1, None, f"get_ticker_family(): KeyError: {e}"
    return 0, ticker_family, ''


# Define your infinite loop function
async def moex_infinite_loop():
    global USER_ID

    while True:
        if USER_ID is not None:
            print("Infinite loop is running...", flush=True)
#            await bot.send_message(USER_ID, "Infinite loop is running...")
            # Add your desired logic here
        await asyncio.sleep(5)  # Sleep for 5 seconds to avoid busy-waiting
