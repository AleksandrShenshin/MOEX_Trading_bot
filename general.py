import ast
import asyncio
from decouple import config


async def get_list_ticker():
    try:
        return ast.literal_eval(config('FUTURES_LIST'))
    except (SyntaxError, ValueError) as e:
        return None
