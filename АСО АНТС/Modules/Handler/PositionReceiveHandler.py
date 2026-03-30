import random

from Modules import BaseUDPReceiveHandler


class OPSPositionReceiveHandler(BaseUDPReceiveHandler):

    def __init__(self, context, host="0.0.0.0", port=8000):
        super().__init__(context, host, port)

    def _process_message(self, message):
        try:
            for robot, data in zip(self.context.robots.list, message):
                if robot.r_id is None:
                    robot.r_id = data["r_id"]
                    robot.m_id = data["m_id"]
                    robot.ip_address = data["ip_address"]

                if robot.r_id == data["r_id"]:
                    robot.move(data["position_x"] * 1000, data["position_y"] * 1000, data["rotation"])
                    robot.zone_proximity = data["zone_proximity"]
                    robot.current_zone = data["current_zone"]
                    robot.position_quality = data["position_quality"]

        except Exception as e:
            pass


class TwinPositionReceiveHandler(BaseUDPReceiveHandler):

    def __init__(self, context, host="0.0.0.0", port=10000):
        super().__init__(context, host, port)

    def _process_message(self, message):
        # print(random.randint(0, 10000), message)
        try:
            robot = self.context.robots.list[0]
            robot.move(message["position_x"] * 1000, message["position_y"] * 1000, message["rotation"])
        except Exception as e:
            pass
