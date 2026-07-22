import json
import logging
from decouple import config
from typing import Dict, Any

file_settings = "bot_settings.json"

logger = logging.getLogger(__name__)


async def get_f_settings() -> Dict[str, Any]:
    data = {}
    try:
        with open(file_settings, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        pass
    finally:
        return data


async def create_f_settings() -> int:
    f_s = {}

    try:
        dflt_forts_l5_coefficient = config('DFLT_FORTS_L5_COEFFICIENT', cast=float)
        dflt_moex_l5_coefficient = config('DFLT_MOEX_L5_COEFFICIENT', cast=float)
        dflt_forts_throws_len = config('DFLT_FORTS_THROWS_LEN', cast=int)
        dflt_moex_throws_len = config('DFLT_MOEX_THROWS_LEN', cast=int)

        f_s["futures_list"] = config('FUTURES_LIST', cast=lambda v: [s.strip() for s in v.split(',')])

        f_s["moex"] = {}
        moex_list_tickers = config('CANDLE_MOEX', cast=lambda v: [s.strip() for s in v.split(',')])
        for moex_ticker in moex_list_tickers:
            f_s["moex"][moex_ticker] = {}
            f_s["moex"][moex_ticker]["l5_coefficient"] = dflt_moex_l5_coefficient
            f_s["moex"][moex_ticker]["throws_len"] = dflt_moex_throws_len

        f_s["forts"] = {}
        forts_list_tickers = config('CANDLE_FORTS', cast=lambda v: [s.strip() for s in v.split(',')])
        for forts_ticker in forts_list_tickers:
            f_s["forts"][forts_ticker] = {}
            f_s["forts"][forts_ticker]["l5_coefficient"] = dflt_forts_l5_coefficient
            f_s["forts"][forts_ticker]["throws_len"] = dflt_forts_throws_len
    except Exception as e:
        logger.error(f"create_f_settings(): ERROR format .env: {e}")
        return 1

    try:
        with open(file_settings, "w", encoding="utf-8") as f:
            json.dump(f_s, f, indent=4, sort_keys=True, ensure_ascii=False)
    except Exception as e:
        logger.error(f"create_f_settings(): Unexpected error when writing settings: {e}")
        return 1

    return 0
