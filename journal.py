import json
import random
import asyncio

file_signals = "signals.json"


async def get_signals_from_file():
    data = {}
    try:
        with open(file_signals, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        pass
    finally:
        return data


async def set_signal_to_file(ticker, type_signal, value, figi):
    signals = await get_signals_from_file()
    for i in range(1, 100):
        # Поиск свободного id
        for id, param_signal in signals.items():
            try:
                if int(id) == i:
                    break
            except ValueError:
                return 1, f"Ошибка структуры {file_signals}"
        else:
            new_id = i
            break

    # Назначение уникального Unique Identifier сигналу
    while True:
        unique_id = random.randint(1000, 9999)
        for id, param_signal in signals.items():
            try:
                if param_signal['unique_id'] == str(unique_id):
                    break
            except KeyError:
                return 1, f"Ошибка структуры {file_signals} -- отсутсвует 'unique_id'"
        else:
            break

    signals[str(new_id)] = {'ticker': ticker, 'type_signal': type_signal, 'value': value, 'figi': figi, 'unique_id': unique_id}

    with open(file_signals, "w", encoding="utf-8") as f:
        json.dump(signals, f, indent=4, sort_keys=True, ensure_ascii=False)

    return 0, None


async def del_signal_from_file(id_signal):
    signals = await get_signals_from_file()
    try:
        del signals[id_signal]
    except KeyError:
        # id not found
        return -1, f"id={id_signal} не найден"

    with open(file_signals, "w", encoding="utf-8") as f:
        json.dump(signals, f, indent=4, sort_keys=True, ensure_ascii=False)

    return 0, None
