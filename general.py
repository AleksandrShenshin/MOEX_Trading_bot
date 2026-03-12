import ast
import copy
import asyncio
import journal
from decouple import config
from datetime import datetime, timedelta, timezone
from threading import Lock
import t_invest_lib.tinv as tinv
import iss_moex.iss_moex as iss_moex
from aiogram.fsm.context import FSMContext

USER_ID = None
shared_tasks = {}
data_tasks_long5 = {}
lock_state = Lock()
lock_data_tasks = asyncio.Lock()
lock_data_long5 = asyncio.Lock()

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


async def fetch_data_ticker(lock, shared_tasks, param_signal, bot, user_id):
    fl_run_stream = False
    try:
        async with lock:
            if param_signal['ticker'] not in list(shared_tasks.keys()):
                new_task_sign = {'figi': param_signal['figi'], 'high': None, 'low': None, 'volume': None,
                                 'time_received': None, 'depends': None}
                new_task_sign['depends'] = set()
                shared_tasks[param_signal['ticker']] = new_task_sign.copy()
                fl_run_stream = True
            shared_tasks[param_signal['ticker']]['depends'].add(asyncio.current_task())
        if fl_run_stream:
            asyncio.create_task(tinv.stream_ticker_one_minute(lock, shared_tasks, param_signal['ticker']))

        time_send_msg = datetime(2026, 1, 31, 20, 42, tzinfo=timezone.utc)
        while True:
            async with lock:
                candle_high = shared_tasks[param_signal['ticker']]['high']
                candle_low = shared_tasks[param_signal['ticker']]['low']
                candle_volume = shared_tasks[param_signal['ticker']]['volume']
                candle_time_received = shared_tasks[param_signal['ticker']]['time_received']
                # TODO: если time_received не обновляется в течении 3 мин, то что-то сломалось в tinv

            if candle_high == None or candle_low == None or candle_volume == None:
                await asyncio.sleep(3)
                continue

            if param_signal['type_signal'] == 'volume':
                if int(candle_volume) >= int(param_signal['value']):
                    if ((candle_time_received - time_send_msg) > timedelta(minutes=1)) or \
                        (candle_time_received.minute != time_send_msg.minute):
                        time_send_msg = candle_time_received
                        msg_to_print = f"🤖 {param_signal['ticker']} {param_signal['type_signal']} {candle_volume} >= {param_signal['value']}"
                        await bot.send_message(user_id, msg_to_print)
            elif param_signal['type_signal'] == 'price':
                msg_to_print = ""

                if candle_high >= float(param_signal['value']) and candle_low <= float(param_signal['value']):
                    msg_to_print = f"📈 {param_signal['ticker']} {param_signal['type_signal']} {candle_high} &gt;= {param_signal['value']}"    # > заменён на &gt; согласно HTML-разметке
                elif candle_low <= float(param_signal['value']) and candle_high >= float(param_signal['value']):
                    msg_to_print = f"📉 {param_signal['ticker']} {param_signal['type_signal']} {candle_low} &lt;= {param_signal['value']}"    # < заменён на &lt; согласно HTML-разметке

                if msg_to_print:
                    # TODO: значение price выводить в соответствии с точностью инструмента
                    await bot.send_message(user_id, msg_to_print)
                    break

            await asyncio.sleep(2)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"fetch_data_ticker(): ERROR: {type(e).__name__}: {e}", flush=True)
        await bot.send_message(user_id, f"❌ <b>ОШИБКА:</b> удалён сигнал: {param_signal['ticker']} {param_signal['type_signal']} {param_signal['value']}")
    finally:
        async with lock:
            shared_tasks[param_signal['ticker']]['depends'].discard(asyncio.current_task())


async def fetch_data_long5(lock_data_long5, data_tasks_long5, market, bot, user_id):
    # data_tasks_long5 = {'forts': {},
    #                     'moex': {'tickers': {figi: {'atr': [XX, YY, ZZ, FF, SS], 'ticker': '', 'prev_bin': -1,
    #                                                 'cur_atr': {'high': None, 'low': None, 'time_received': None}},
    #                                          figi: {}},
    #                              'depends': None}

    coefficient_multiplication_atr = 2.5
    if market == 'forts':
        list_tickers = []
        list_short_tickers = config('LONG_FIVE_FORTS', cast=lambda v: [s.strip() for s in v.split(',')])
        for short_ticker in list_short_tickers:
            status, ret_val, err_msg = await get_ticker_family(short_ticker)
            if status == 0:
                list_tickers.append(ret_val['current_ticker'])
            else:
                return
    elif market == 'moex':
        # ['SBER', 'VTBR', 'GAZP', 'GMKN']
        list_tickers = config('LONG_FIVE_MOEX', cast=lambda v: [s.strip() for s in v.split(',')])

    try:
        async with lock_data_long5:
            if market not in list(data_tasks_long5.keys()):
                data_tasks_long5[market] = {'tickers': {}, 'depends': set()}
                data_tasks_long5[market]['depends'].add(asyncio.current_task())
                for ticker in list_tickers:
                    status, ticker_param, err_mess = await tinv.get_param_instrument(ticker)
                    if status:
                        await bot.send_message(user_id, f"❌ <b>ОШИБКА:</b> long5 {market} получение параметров {ticker}: {err_mess}")
                        return
                    else:
                        data_tasks_long5[market]['tickers'][ticker_param['figi']] = {'atr': [],
                                                                                     'ticker': ticker_param['ticker'],
                                                                                     'prev_bin': -1,
                                                                                     'cur_atr': {'high': None,
                                                                                                 'low': None,
                                                                                                 'time_received': None}
                                                                                     }
                asyncio.create_task(tinv.stream_list_figi_five_minute(lock_data_long5, data_tasks_long5, market))

        time_send_msg = datetime(2026, 1, 31, 20, 42, tzinfo=timezone.utc)
        prev_bin = -1
        while True:
            async with lock_data_long5:
                upd_data_long5 = copy.deepcopy(data_tasks_long5[market]['tickers'])
            # TODO: если time_received не обновляется в течении 15 мин, то что-то сломалось в tinv
            for figi, ticker_param in upd_data_long5.items():
                if len(ticker_param['atr']) < 5:
                    continue
                else:
                    average = sum(ticker_param['atr']) / len(ticker_param['atr'])
                    if (float(ticker_param['cur_atr']['high']) - float(ticker_param['cur_atr']['low'])) >= (average * coefficient_multiplication_atr):
                        if ((ticker_param['cur_atr']['time_received'] - time_send_msg) > timedelta(minutes=5)) or \
                            ((ticker_param['cur_atr']['time_received'].minute // 5) != prev_bin): # Проверка перехода между 5 мин
                            time_send_msg = ticker_param['cur_atr']['time_received']
                            prev_bin = (ticker_param['cur_atr']['time_received'].minute // 5)
                            msg_to_print = f"🐛 long5 {ticker_param['ticker']} {market}"
                            await bot.send_message(user_id, msg_to_print)
            await asyncio.sleep(2)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"fetch_data_long5(): ERROR: {type(e).__name__}: {e}", flush=True)
        await bot.send_message(user_id, f"❌ <b>ОШИБКА:</b> удалён сигнал: long5 {market}")
    finally:
        async with lock_data_long5:
            data_tasks_long5[market]['depends'].discard(asyncio.current_task())


# Define your infinite loop function
async def moex_infinite_loop(state: FSMContext):
    global USER_ID
    global shared_tasks
    global data_tasks_long5
    global lock_state
    global lock_data_tasks
    global lock_data_long5
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
                    if param_signal['type_signal'] == 'price' or param_signal['type_signal'] == 'volume':
                        task = asyncio.create_task(fetch_data_ticker(lock_data_tasks, shared_tasks, param_signal, bot, USER_ID))
                    elif param_signal['type_signal'] == 'long5':
                        task = asyncio.create_task(fetch_data_long5(lock_data_long5, data_tasks_long5, param_signal['market'], bot, USER_ID))
                    curr_param_task['id'] = id_signal
                    curr_param_task['task'] = task
                    curr_tasks[param_signal['unique_id']] = curr_param_task.copy()

            for unique_id in list(curr_tasks.keys()):
                if unique_id not in list_unique_id:
                    # В случае удаления сигнала - удаляем задачу
                    task = curr_tasks[unique_id]['task']
                    task.cancel()
                    curr_tasks.pop(unique_id, None)
                else:
                    # В случае завершения задачи - удаляем сигнал
                    task = curr_tasks[unique_id]['task']
                    if task.done():
                        done_task = curr_tasks.pop(unique_id, None)
                        ret_val, err_mess = await journal.del_signal_from_file(done_task['id'])
                        if ret_val:
                            await bot.send_message(USER_ID, f"❌ <b>ERROR:</b> удаления сигнала: {err_mess}")
                        else:
                            data = await journal.get_signals_from_file()
                            lock_state.acquire()
                            await state.update_data(signals=data)
                            lock_state.release()

        await asyncio.sleep(5)  # Sleep for 5 seconds to avoid busy-waiting
