from threading import Thread

from . import Context, BaseHandler
from .Handler import UDPTwinDataReceiveHandler, MissionHandler, TrustedHandler


class HandlerDispatcher(BaseHandler):
    def __init__(self, context: Context, init_ok: bool):
        super().__init__(context)
        self.init_ok = init_ok
        self.handlers = []
        context.lg.init(
            f"{context.config.get('general', 'app_name')}, версия {context.config.get('general', 'version')}"
        )
        self.handlers.append(UDPTwinDataReceiveHandler(self.context))
        context.lg.init("Загрузка завершена.")

    def start(self, mission_code: MissionHandler, trusted_code: TrustedHandler):
        self.handlers.append(mission_code(self.context))
        self.handlers.append(trusted_code(self.context))
        self.run()

    def run(self):
        for handler in self.handlers:
            runnable = Thread(target=handler.run, daemon=True, args=())
            runnable.start()
