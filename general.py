import ast
import asyncio
from decouple import config

USER_ID = None


async def set_user_id(user_id):
    global USER_ID
    USER_ID = user_id


async def get_list_ticker():
    try:
        return ast.literal_eval(config('FUTURES_LIST'))
    except (SyntaxError, ValueError) as e:
        return None


# Define your infinite loop function
async def moex_infinite_loop():
    global USER_ID

    while True:
        if USER_ID is not None:
            print("Infinite loop is running...", flush=True)
#            await bot.send_message(USER_ID, "Infinite loop is running...")
            # Add your desired logic here
        await asyncio.sleep(5)  # Sleep for 5 seconds to avoid busy-waiting
