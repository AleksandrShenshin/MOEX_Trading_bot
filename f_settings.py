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

    f_s["futures_list"] = config('FUTURES_LIST', cast=lambda v: [s.strip() for s in v.split(',')])
    try:
        with open(file_settings, "w", encoding="utf-8") as f:
            json.dump(f_s, f, indent=4, sort_keys=True, ensure_ascii=False)
    except Exception as e:
        logger.error(f"create_f_settings(): Unexpected error when writing settings: {e}")
        return 1

    return 0
