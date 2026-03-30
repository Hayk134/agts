import time

from Modules import BaseUDPSendHandler, BaseHandler
from Modules.Logic import const as c


class SPDHandler:
    def __init__(self, context):
        self.context = context
        self.handlers = []

    def generate(self):
        self.handlers.append(SDPRemoteIndication(self.context))

        for device in self.context.spd.controls:
            self.handlers.append(ControlSPDViaUDPSender(self.context, device, 0.21))
            if not self.context.args.get_arg("twin"):
                self.handlers.append(SPDViaUDPCheckAlive(self.context, device, 1))

        self.handlers.append(CleaningSPDViaUDPSender(self.context, self.context.spd.cleaning, 0.21))
        self.handlers.append(PipesSPDViaUDPSender(self.context, self.context.spd.pipes, 0.21))

        if not self.context.args.get_arg("twin"):
            self.handlers.append(SPDViaUDPCheckAlive(self.context, self.context.spd.cleaning, 1))
            self.handlers.append(SPDViaUDPCheckAlive(self.context, self.context.spd.pipes, 1))

            self.handlers.append(RemoteSPDViaUDPSender(self.context, self.context.spd.remote, 0.21))
            self.handlers.append(SPDViaUDPCheckAlive(self.context, self.context.spd.remote, 1))

        return self.handlers


class SDPRemoteIndication(BaseHandler):
    def run(self):
        while self.context.robots.current_robot.r_id is None:
            time.sleep(0.5)
        leds_list = [0 for _ in range(20)]
        while True:
            time.sleep(0.1)
            for i in range(10):
                leds_list[i] = 0
            if self.context.mission.status == 1:
                leds_list[10 - int(self.context.robots.current_robot.r_id)] = 2
            elif self.context.mission.status == 3 or self.context.mission.status == 4:
                leds_list[10 - int(self.context.robots.current_robot.r_id)] = 1
            else:
                leds_list[10 - int(self.context.robots.current_robot.r_id)] = 4

            for robot in self.context.robots.list:
                leds_list[9 + int(robot.r_id)] = 1
                if robot.position_quality > 0.1:
                    leds_list[9 + int(robot.r_id)] = 3
                if robot.position_quality > 0.7:
                    leds_list[9 + int(robot.r_id)] = 2

            self.context.spd.remote.color = leds_list


class ControlSPDViaUDPSender(BaseUDPSendHandler):
    def __init__(self, context, device, send_interval):
        super().__init__(context, device.address, device.port, send_interval)
        self.device = device

    def _get_data_to_send(self):
        self.context.field.cells[c.get_zone("control")[self.device.d_id] - 1].set_indicator(self.device.color)
        return {"c": self.device.color, "glitch": self.device.glitch}

    def _process_message(self, message):
        pass


class CleaningSPDViaUDPSender(BaseUDPSendHandler):
    def __init__(self, context, device, send_interval):
        super().__init__(context, device.address, device.port, send_interval)
        self.device = device

    def _get_data_to_send(self):
        self.context.field.cells[c.get_zone("cleaning")[0] - 1].set_indicator(self.device.color)
        return {"c": self.device.color, "glitch": self.device.glitch}

    def _process_message(self, message):
        pass


class PipesSPDViaUDPSender(BaseUDPSendHandler):
    def __init__(self, context, device, send_interval):
        super().__init__(context, device.address, device.port, send_interval)
        self.device = device

    def _get_data_to_send(self):
        if self.context.args.get_arg("twin"):
            color = self.device.twin_color
        else:
            color = self.device.color
        m = {
            "m0": f"{self.device.pipes_glitch[0]}{color[0]}",
            "m1": f"{self.device.pipes_glitch[1]}{color[1]}",
            "m2": f"{self.device.pipes_glitch[2]}{color[2]}",
            "m3": f"{self.device.pipes_glitch[3]}{color[3]}",
            "barrel_glitch": self.device.barrel_glitch,
        }
        self.context.field.cells[c.get_zone("check")[0] - 1].set_indicator(self.device.twin_color[0])
        self.context.field.cells[c.get_zone("check")[1] - 1].set_indicator(self.device.twin_color[1])
        self.context.field.cells[c.get_zone("check")[2] - 1].set_indicator(self.device.twin_color[2])
        self.context.field.cells[c.get_zone("check")[3] - 1].set_indicator(self.device.twin_color[3])
        return m

    def _process_message(self, message):
        pass


class RemoteSPDViaUDPSender(BaseUDPSendHandler):
    def __init__(self, context, device, send_interval):
        super().__init__(context, device.address, device.port, send_interval, True)
        self.device = device

    def _get_data_to_send(self):
        return {"c": self.device.color, "cmd": "get_buttons"}

    def _process_message(self, message):
        try:
            self.context.mission.triggers.start_mission_trigger = message["b1"]
            self.context.mission.triggers.stop_mission_trigger = message["b2"]
        except Exception as e:
            pass


class SPDViaUDPCheckAlive(BaseUDPSendHandler):
    def __init__(self, context, device, send_interval):
        super().__init__(context, device.address, device.port, send_interval, True)
        self.device = device

    def _get_data_to_send(self):
        return {"alive": True}

    def _process_message(self, message):
        try:
            if message["alive"]:
                self.device.is_alive = True
            else:
                self.device.is_alive = False
        except Exception as e:
            self.device.is_alive = False
