import json
import random
import threading
import time
from math import atan2, degrees, pi, sqrt

import requests
from simple_pid import PID
from wpimath.geometry import Translation2d
from wpimath.kinematics import MecanumDriveKinematics

from .vendor import DigitalToggler, UDPDigitalDriver


class AGTSHookAp:

    def __init__(self, context):
        self.context = context
        self.wheel_base = 0.15
        _h = self.wheel_base / 2
        self.wheel_radius = 0.097 / 2
        self.absolute_max_speed = 0.2  # m/s 0.256
        self.default_max_speed = self.absolute_max_speed * 0.707  # m/s
        self.current_max_speed = self.absolute_max_speed * 0.707  # m/s
        self.waypoints = []
        self.current_waypoint = {"x": 0, "y": 0}

        self.driver = UDPDigitalDriver(context, "127.0.0.1", 11000)
        self.gripper = DigitalToggler("127.0.0.1", 14000, False)

        self.current_speed_1 = 0
        self.current_speed_2 = 0
        self.current_speed_3 = 0
        self.current_speed_4 = 0
        self.rotation_pid = PID(-0.01, 0, 0, setpoint=0)
        self.rotation_pid.output_limits = (-pi / 4, pi / 4)
        self.position_x_pid = PID(-1, 0, 0, setpoint=0)
        self.position_x_pid.output_limits = (-self.current_max_speed, self.current_max_speed)
        self.position_y_pid = PID(-1, 0, 0, setpoint=0)
        self.position_y_pid.output_limits = (-self.current_max_speed, self.current_max_speed)
        self.rotation_threshold = 2
        self.proximity_threshold = 0.03

        self.command_queue = []
        self.motor_journal = []
        self.ap_journal = []
        self.ap_journal_id = -1
        self.motor_journal_id = -1
        self.last_executed_cmd_id = -1
        self.ap_hash = random.getrandbits(128)
        self.false_ap_hash = self.ap_hash
        self.gripper_enable = True
        self.motor_ids = []
        for i in range(4):
            self.motor_ids.append(random.getrandbits(4))

        front_left_wheel_location = Translation2d(_h, _h)
        front_right_wheel_location = Translation2d(_h, -_h)
        rear_left_wheel_location = Translation2d(-_h, _h)
        rear_right_wheel_location = Translation2d(-_h, -_h)

        self.kinematics = MecanumDriveKinematics(
            front_left_wheel_location, front_right_wheel_location, rear_left_wheel_location, rear_right_wheel_location
        )

        self.servo_thread = threading.Thread(target=self.driver.run, daemon=True).start()

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

    def __del__(self):
        self.gripper.cleanup()

    def __exit__(self):
        self.gripper.cleanup()

    @staticmethod
    def get_angle_to_target(x, y, robot_direction, current_waypoint):
        x_dst = current_waypoint["x"] - x
        y_dst = current_waypoint["y"] - y

        try:
            angle_to_target_rads = atan2(-y_dst, x_dst)
        except:
            return 0
        angle_to_target_rads = angle_to_target_rads % (2 * pi)
        angle_to_target_degrees = -degrees(angle_to_target_rads)
        target_direction_diff = angle_to_target_degrees - robot_direction
        if target_direction_diff > 180:
            target_direction_diff = target_direction_diff - 360
        if target_direction_diff < -180:
            target_direction_diff = target_direction_diff + 360
        return target_direction_diff

    @staticmethod
    def get_distance_to_target(x, y, current_waypoint):
        dist = sqrt((current_waypoint["x"] - x) ** 2 + (current_waypoint["y"] - y) ** 2)
        return dist

    def do_rotate(self, current_waypoint):
        target_direction_diff = self.get_angle_to_target(
            self.context.robot.position_x, self.context.robot.position_y, self.context.robot.rotation, current_waypoint
        )

        while abs(target_direction_diff) > self.rotation_threshold:
            target_direction_diff = self.get_angle_to_target(
                self.context.robot.position_x,
                self.context.robot.position_y,
                self.context.robot.rotation,
                current_waypoint,
            )
            control = self.rotation_pid(target_direction_diff)
            self.driver.set_controls({"x": 0, "y": 0, "r": control})
            time.sleep(0.01)
        self.driver.set_controls({"x": 0, "y": 0, "r": 0})

    def do_move(self, current_waypoint, autorotate=True):
        dist = self.get_distance_to_target(
            self.context.robot.position_x, self.context.robot.position_y, current_waypoint
        )
        while dist > self.proximity_threshold:
            dist = self.get_distance_to_target(
                self.context.robot.position_x, self.context.robot.position_y, current_waypoint
            )
            d1 = current_waypoint["x"] - self.context.robot.position_x
            d2 = current_waypoint["y"] - self.context.robot.position_y

            d1 = self.position_x_pid(d1) / self.wheel_radius
            d2 = self.position_y_pid(d2) / self.wheel_radius

            k = (d1**2 + d2**2) * (self.wheel_radius**2) / (self.current_max_speed**2)
            if k > 1:
                inv_k = sqrt(1 / k)
                d1 = d1 * inv_k
                d2 = d2 * inv_k

            target_direction_diff = self.get_angle_to_target(
                self.context.robot.position_x,
                self.context.robot.position_y,
                self.context.robot.rotation,
                current_waypoint,
            )
            control = self.rotation_pid(target_direction_diff) if autorotate else 0

            self.driver.set_controls({"x": d1 * self.wheel_radius, "y": d2 * self.wheel_radius, "r": control})
            time.sleep(0.01)
        self.driver.set_controls({"x": 0, "y": 0, "r": 0})

    def do_grip(self, toggle):
        if self.gripper_enable:
            if toggle:
                self.gripper.on()
            else:
                self.gripper.off()
            (
                self._send_request_with_response("grab_payload", None)
                if toggle
                else self._send_request_with_response("drop_payload", None)
            )

    def get_gripper_state(
        self,
    ):
        return self.gripper.get_state()

    def block_gripper(self):
        self.gripper_enable = True

    def set_motors_state(self, toggle=True):
        self.driver.permission = toggle

    def set_max_speed(self, max_speed):
        self.current_max_speed = max_speed
        if self.current_max_speed > (self.absolute_max_speed * 0.707):
            self.current_max_speed = self.absolute_max_speed * 0.707
