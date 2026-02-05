import asyncio
from datetime import datetime, timedelta
from threading import Lock
import iss_moex.iss_moex as iss_moex
from aiogram.fsm.context import FSMContext

USER_ID = None
lock_state = Lock()

async def set_user_id(user_id):
    global USER_ID
    USER_ID = user_id


async def get_support_instruments():
    FUTURES_LIST = ['si', 'cr']
    return FUTURES_LIST


async def get_support_signals():
    TYPES_SIGNAL = {'Price': {'param': '-p'}, 'Volume': {'param': '-v'}}
    try:
        return TYPES_SIGNAL
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


async def update_current_ticker(state):
    global lock_state
    curr_instr = {}
    supp_instr = await get_support_instruments()
    for short_ticker in supp_instr:
        status, ret_val, err_msg = await get_ticker_family(short_ticker)
        if status:
            return -1, err_msg
        ret_val['date_update'] = datetime.now().strftime("%Y-%m-%d")
        curr_instr[short_ticker] = ret_val

    lock_state.acquire()
    await state.update_data(supp_tools=curr_instr)
    lock_state.release()
    return 0, None


async def task_upd_curr_ticker(state):
    global USER_ID
    global lock_state
    while True:
        ret_val, err_msg = await update_current_ticker(state)
        if ret_val:
            lock_state.acquire()
            data = await state.get_data()
            lock_state.release()
            try:
                bot = data['bot']
                await bot.send_message(USER_ID, f"❌ <b>ОШИБКА:</b> update_current_ticker(): {err_msg}")
            except KeyError:
                pass

        # Run every 1 hour
        await asyncio.sleep(1*60*60)


# Define your infinite loop function
async def moex_infinite_loop(state: FSMContext):
    global USER_ID

    asyncio.create_task(task_upd_curr_ticker(state))

    while True:
        if USER_ID is not None:
            print("Infinite loop is running...", flush=True)
            # Add your desired logic here
        await asyncio.sleep(5)  # Sleep for 5 seconds to avoid busy-waiting
