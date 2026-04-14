import os
import time
import errno
import logging
import requests
from decouple import config

PID_FILE = os.path.join(os.path.dirname(__file__), "pid.bot")
LOG_FILE = os.path.join(os.path.dirname(__file__), "log.txt")


def send_max_message(text: str) -> None:
    msg = f"🐦‍🔥 Strazh bot: {text}"
    requests.post("https://platform-api.max.ru/messages", params={"user_id": config('MAX_USER_ID')}, json={"text": msg},
                  headers={"Authorization": config('MAX_BOT_TOKEN'), "Content-Type": "application/json"}, timeout=10)


def pid_exists(pid: int) -> tuple[bool, str]:
    """Check whether pid exists in the current process table (POSIX)."""
    if pid < 0 or pid == 0:
        return False, f"pid_exists(): invalid PID={pid}"

    try:
        # signal 0 does not kill the process, just checks for existence
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # No such process
            return False, f"pid_exists(): No such process PID={pid}"
        elif err.errno == errno.EPERM:
            # Process exists but we have no permission
            return True, ""
        else:
            return False, f"pid_exists(): err = {err}"
    else:
        return True, ""


def main():
    logger.warning("Strazh Bot is run...")

    if not os.path.isfile(PID_FILE):
        err_msg = f"pid file {PID_FILE} not found"
        logger.error(err_msg)
        send_max_message(err_msg)
        return

    try:
        with open(PID_FILE, "r", encoding="utf-8") as f:
            pid_bot = f.read().strip()
    except OSError as e:
        err_msg = f"failed to read {PID_FILE}: {e}"
        logger.error(err_msg)
        send_max_message(err_msg)
        return

    if not pid_bot:
        err_msg = f"file {PID_FILE} is empty"
        logger.error(err_msg)
        send_max_message(err_msg)
        return

    try:
        pid = int(pid_bot)
    except ValueError:
        err_msg = f"invalid pid value '{pid_bot}' in file {PID_FILE}"
        logger.error(err_msg)
        send_max_message(err_msg)
        return

    if not os.path.isfile(LOG_FILE):
        err_msg = f"file {LOG_FILE} not found"
        logger.error(err_msg)
        send_max_message(err_msg)
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        # jump to end of file (как tail -f)
        f.seek(0, os.SEEK_END)

        while True:
            status, e_msg = pid_exists(pid)
            if not status:
                err_msg = f"process with pid={pid} is not running: {e_msg}"
                logger.error(err_msg)
                send_max_message(err_msg)
                return

            line = f.readline()
            if not line:
                # no new data yet
                time.sleep(10)
                continue

            if "error" in line.lower():
                line_stripped = line.rstrip("\n")
                logger.error(line_stripped)
                send_max_message(line_stripped)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    main()
