from threading import Thread

from Modules import Context, BaseHandler
from Modules.Handler.CommandInterface import CommandInterface
from Modules.Handler.MissionHandler import MissionHandler, HTTPMissionReceiver
from Modules.Handler.RenderHandler import RenderHandler
from Modules.Handler import TwinPositionReceiveHandler, OPSPositionReceiveHandler, SPDHandler


class HandlerDispatcher(BaseHandler):
    def __init__(self, context: Context, init_ok: bool):
        super().__init__(context)
        self.init_ok = init_ok
        self.handlers = []
        context.lg.init(
            f"{context.config.get('general', 'app_name')}, версия {context.config.get('general', 'version')}"
        )

        if self.context.args.get_arg("twin"):
            self.handlers.append(TwinPositionReceiveHandler(self.context))
        else:
            self.handlers.append(OPSPositionReceiveHandler(self.context))

        for handler in SPDHandler(self.context).generate():
            self.handlers.append(handler)
        self.handlers.append(MissionHandler(self.context))
        self.handlers.append(HTTPMissionReceiver(self.context))

        self.handlers.append(CommandInterface(self.context))

        self.run()
        context.lg.init("Загрузка завершена.")
        RenderHandler(self.context).run()

    def run(self):
        for handler in self.handlers:
            runnable = Thread(target=handler.run, daemon=True, args=())
            runnable.start()
