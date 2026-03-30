from src.libs.AGTSWrapTwin.Modules import BaseUDPReceiveHandler


class UDPTwinDataReceiveHandler(BaseUDPReceiveHandler):
    def __init__(self, context, host="0.0.0.0", port=10001):
        super().__init__(context, host, port)

    def _process_message(self, message):
        try:
            data = {
                "position_x": float(message["position_x"]),
                "position_y": float(message["position_y"]),
                "rotation": float(message["rotation"]),
            }
            self.context.robot.position_x = data["position_x"]
            self.context.robot.position_y = data["position_y"]
            self.context.robot.rotation = data["rotation"]
        except Exception as e:
            pass
