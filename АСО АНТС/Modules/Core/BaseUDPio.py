import abc
import json
import socket
import threading

import time

from .BaseHandler import BaseHandler


class BaseUDPSendHandler(BaseHandler):
    def __init__(self, context, target_ip, target_port=None, send_interval=None, recv_data=False):
        super().__init__(context)

        self.uuid = self.context.system.gen_uid(4)

        if self.context.args.get_arg("check"):
            return

        self.recv_data = recv_data
        self.last_message = {}

        self._stop_event = threading.Event()
        self.target_ip = target_ip
        self.target_port = target_port if target_port is not None else self.context.config.get("udp", "target_port")
        self.send_interval = (
            send_interval if send_interval is not None else self.context.config.get("udp", "send_interval")
        )

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(1)

        self.context.lg.init(f"UDP(c) -> (uid={self.uuid}) инициализирован.")

    def run(self):
        try:
            while not self._stop_event.is_set():
                try:
                    data = self._get_data_to_send()
                    if data:
                        json_data = json.dumps(data, ensure_ascii=False)
                        message = json_data.encode("utf-8")
                        self.sock.sendto(message, (self.target_ip, int(self.target_port)))
                        if self.recv_data:
                            data, addr = self.sock.recvfrom(128)
                            message_str = data.decode("utf-8")
                            self.last_message = json.loads(message_str)
                            self._process_message(self.last_message)
                except Exception as e:
                    if "10054" in str(e) or "timed out" in str(e):
                        self.last_message = {"status": "unavailable"}
                        self._process_message(self.last_message)
                    else:
                        self.context.lg.error(f"UDP(r) -> (uid={self.uuid}): {e}")
                time.sleep(self.send_interval)
        except Exception as e:
            self.context.lg.error(f"UDP(w) -> (uid={self.uuid}): {e}")
        finally:
            self._cleanup()

    @abc.abstractmethod
    def _get_data_to_send(self):
        raise NotImplementedError

    @abc.abstractmethod
    def _process_message(self, message):
        raise NotImplementedError

    def stop(self):
        self.context.lg.log(f"Остановка UDP -> (uid={self.uuid})")
        self._stop_event.set()

    def _cleanup(self):
        try:
            self.sock.close()
            self.context.lg.log(f"UDP -> (uid={self.uuid}) закрыт.")
        except Exception as e:
            self.context.lg.error(f"UDP(e) -> (uid={self.uuid}): {e}")


class BaseUDPReceiveHandler(BaseHandler):
    def __init__(self, context, host="0.0.0.0", port=8001):
        super().__init__(context)

        self.uuid = self.context.system.gen_uid(4)

        self.thread = None
        self.host = host
        self.port = port
        self._stop_event = threading.Event()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(0.5)

        self.last_message = None

        self.context.lg.init(f"UDP(c) <- (uid={self.uuid}) инициализирован.")

    def run(self):
        try:
            while not self._stop_event.is_set():
                try:
                    data, addr = self.sock.recvfrom(4096)
                    message_str = data.decode("utf-8")
                    self.last_message = json.loads(message_str)
                    self._process_message(self.last_message)
                except socket.timeout:
                    continue
                except Exception:
                    pass
        except Exception as e:
            self.context.lg.error(f"UDP(r) <- (uid={self.uuid}): {e}")
        finally:
            self._cleanup()

    @abc.abstractmethod
    def _process_message(self, message):
        raise NotImplementedError

    def stop(self):
        self.context.lg.log(f"Остановка UDP <- (uid={self.uuid})")
        self._stop_event.set()

    def _cleanup(self):
        try:
            self.sock.close()
            self.context.lg.log(f"UDP <- (uid={self.uuid}) закрыт.")
        except Exception as e:
            self.context.lg.error(f"UDP(e) <- (uid={self.uuid}): {e}")
