import json
import socket

from src.libs.AGTSWrapTwin.Modules import BaseUDPSendHandler


class UDPDigitalDriver(BaseUDPSendHandler):
    def __init__(self, context, address, port):
        super().__init__(context, address, port, 0.02)
        self.controls = {"x": 0, "y": 0, "r": 0}

    def set_controls(self, data=None):
        if data is None:
            data = {}
        if data.get("x") is not None:
            self.controls["x"] = data["x"]
        if data.get("y") is not None:
            self.controls["y"] = data["y"]
        if data.get("r") is not None:
            self.controls["r"] = data["r"]

    def _get_data_to_send(self):
        if self.context.emergency_stop:
            m = {
                "speed_x": 0,
                "speed_y": 0,
                "speed_r": 0,
            }
        else:
            m = {
                "speed_x": self.controls["x"],
                "speed_y": self.controls["y"],
                "speed_r": self.controls["r"],
            }
        return m

    def _process_message(self, message):
        pass


class DigitalToggler:
    def __init__(self, host: str, port: int, initial_state=False):
        self.state = initial_state
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def toggle(self):
        self.state = not self.state
        self.send_data()

    def on(self):
        self.state = True
        self.send_data()

    def off(self):
        self.state = False
        self.send_data()

    def get_state(self):
        return self.state

    def cleanup(self):
        self.socket.close()

    def send_data(
        self,
    ) -> None:
        data = {"enable": self.state}
        json_data = json.dumps(data).encode("utf-8")
        try:
            self.socket.sendto(json_data, (self.host, self.port))
            # print(f"Sent data to {self.host}:{self.port}: {data}")
        except Exception as e:
            print(f"Error sending data: {e}")
