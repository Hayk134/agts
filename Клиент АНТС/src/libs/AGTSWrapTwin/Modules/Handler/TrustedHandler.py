import json
import time
from abc import abstractmethod
from threading import Thread

import requests

from src.libs.AGTSWrapTwin.Modules import BaseHandler


class TrustedHandler(BaseHandler):
    def __init__(self, context):
        super().__init__(context)
        self.lg = context.lg

        self.running = True

    @abstractmethod
    def trusted_code(self):
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def make_next_short_message(prev_message: str):
        raise NotImplementedError

    def _trusted_code_wrapper(self):
        Thread(target=self.trusted_code, daemon=True).start()

        while self.running:
            time.sleep(0.1)

    def _fabric_next_short_message(self):
        while True:
            time.sleep(1)
            prev_message = self._send_request_with_response("get_short_message", None).get("message")
            new_message = self.make_next_short_message(prev_message)
            self._send_request_with_response("set_short_message", {"message": new_message})

    def _send_request_with_response(self, method, data):
        try:
            req = requests.post(
                f"http://127.0.0.1:13501/{method}",
                data=json.dumps({"content": data}),
                timeout=1,
            )
            if req.status_code == 200:
                response = json.loads(req.text)
                return response["content"]
        except Exception as e:
            if "timeout" in str(e):
                self.context.lg.error(f"Ошибка отправки команды: АСО не отвечает")
        return False

    def _wait_for_start(self):
        while not self.context.mission_checks_ok:
            time.sleep(0.1)
        time.sleep(0.1)
        self.lg.log("(TM) Заезд инициализирован - ожидание старта")
        while not self.context.mission_state:
            time.sleep(0.1)
        time.sleep(0.1)

    def get_ap_code_hash(self):
        return self._send_request_with_response("get_ap_code_hash", None)

    def set_ap_force_reset(self):
        return self._send_request_with_response("ap_force_reset", None)

    def get_drive_data(self):
        return self._send_request_with_response("get_drive_data", None)

    def set_drive_force_reset(self, data):
        return self._send_request_with_response("drive_force_reset", data)

    def get_service_zones(self):
        return self._send_request_with_response("get_service_zones", None)

    def set_emergency_stop(self, toggle):
        if toggle:
            return self._send_request_with_response("emergency_stop", None)
        else:
            return self._send_request_with_response("emergency_stop_release", None)

    def set_speed_controller_reset(self):
        return self._send_request_with_response("speed_controller_reset", None)

    def get_system_messages(self):
        return self._send_request_with_response("get_system_messages", None)

    def send_message_to_ap(self, message):
        self.context.robot.messages.append(message)

    def set_ap_wait_lock_release(self):
        self.context.wait_flag = False

    def get_control_color_temperature(self):
        return self._send_request_with_response("get_control_color_temperature", None)

    def set_grip_lock(self, toggle):
        if toggle:
            return self._send_request_with_response("payload_lock", None)
        else:
            return self._send_request_with_response("payload_unlock", None)

    def get_reserved_cell_pollution_status(self):
        return self._send_request_with_response("get_reserved_cell_pollution_status", None)

    def get_robot_status(self):
        return {
            "position_x": self.context.robot.position_x,
            "position_y": self.context.robot.position_y,
            "rotation": self.context.robot.rotation,
        }

    def run(self):
        self._wait_for_start()
        self.lg.log("Доверенный код инициализирован")
        Thread(target=self._trusted_code_wrapper, daemon=True).start()
        if self.context.cybs["CybP_02"]:
            Thread(target=self._fabric_next_short_message, daemon=True).start()
        while self.context.mission_state:
            time.sleep(0.1)
