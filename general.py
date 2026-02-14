import ast
import asyncio
from decouple import config
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
    ticker_family = {'all_list': '', 'current_ticker': ''}
    list_ticker = iss_moex.get_list_definite_futures(short_ticker)
    ticker_family['all_list'] = list_ticker
    for full_ticker in list_ticker:
        try:
            data_fut = iss_moex.get_data_future(full_ticker)
            if len(data_fut) == 0:
                continue

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


async def fetch_data(id):
    while True:
        print(f"***** Run work Task {id}", flush=True)
        await asyncio.sleep(3) # Имитация сетевого запроса


# Define your infinite loop function
async def moex_infinite_loop(state: FSMContext):
    global USER_ID
    curr_tasks = {}

    asyncio.create_task(task_upd_curr_ticker(state))

    # TODO: Что будет если идет опрос тикера которого больше нет
    while True:
        if USER_ID is not None:
            # Add your desired logic here
            lock_state.acquire()
            data = await state.get_data()
            bot = data['bot']
            debug_param = data['debug']
            await state.update_data(debug=None)
            lock_state.release()

            if debug_param == "get_tasks":
                msg_to_print = f"🍳 <b>Список опрашеваемых ID сигналов:</b>\n"
                for param_curr_tasks in curr_tasks.values():
                    msg_to_print += f"{param_curr_tasks['id']}\n"
                await bot.send_message(USER_ID, msg_to_print)

            list_unique_id = []

            # В случае появления нового сигнала - создаём для него задачу
            for id_signal, param_signal in data['signals'].items():
                list_unique_id.append(param_signal['unique_id'])
                if param_signal['unique_id'] not in curr_tasks:
                    curr_param_task = {}
                    task = asyncio.create_task(fetch_data(id_signal))
                    curr_param_task['id'] = id_signal
                    curr_param_task['task'] = task
                    curr_tasks[param_signal['unique_id']] = curr_param_task.copy()

            # В случае удаления сигнала - удаляем задачу
            for unique_id in list(curr_tasks.keys()):
                if unique_id not in list_unique_id:
                    task = curr_tasks[unique_id]['task']
                    task.cancel()
                    curr_tasks.pop(unique_id, None)

        await asyncio.sleep(5)  # Sleep for 5 seconds to avoid busy-waiting
