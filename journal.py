import json
import asyncio

file_signals = "signals.json"


async def signals_to_file(signals):
    with open(file_signals, "w", encoding="utf-8") as f:
        json.dump(signals, f, indent=4, sort_keys=True, ensure_ascii=False)


async def signals_from_file():
    try:
        with open(file_signals, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    else:
        return data
