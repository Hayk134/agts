import os
import random
import string
import threading
from functools import wraps


def run_in_thread(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            loop = True
            thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
            thread.start()
            return thread
        except Exception as e:
            print(f"Ошибка при обработке: {e}")
            return None

    return wrapper


class System:
    def __init__(self, context):
        self.context = context

    @staticmethod
    def gen_uid(length):
        letters = string.ascii_lowercase + string.ascii_uppercase
        return "".join(random.choice(letters) for i in range(length))

    @staticmethod
    def hard_reboot():
        os.system("sudo reboot")

    @staticmethod
    def app_restart():
        os.system("pm2 restart all")
