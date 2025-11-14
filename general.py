import asyncio
from decouple import config


async def get_list_ticker():
    return config('FUTURES_LIST', cast=lambda v: [s.strip() for s in v.split(',')])
