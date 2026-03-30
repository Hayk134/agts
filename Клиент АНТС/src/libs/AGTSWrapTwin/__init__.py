import time

from .Modules import HandlerDispatcher
from .Modules import Context
import os

init_ok = True
CTX = None
HD = None


def start_module(mission_code, trusted_code):
    global init_ok, CTX, HD
    init_ok = True

    CTX = Context(init_ok)
    HD = HandlerDispatcher(CTX, init_ok)

    if CTX is None:
        print("Модуль не инициализирован.")
        return
    if HD is None:
        print("Модуль не инициализирован.")
        return

    HD.start(mission_code, trusted_code)
    try:
        while CTX.init_ok:
            time.sleep(0.1)
        CTX.lg.log("Завершение работы.")
    except KeyboardInterrupt as e:
        CTX.lg.log("KeyboardInterrupt, остановлено пользователем.")
