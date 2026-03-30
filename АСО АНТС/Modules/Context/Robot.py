from threading import Thread

import time

from Modules.Logic import Rect, const as c


class Robot:
    def __init__(self, context, num):
        self.context = context

        self.m_id = 0 if self.context.args.get_arg("twin") else None
        self.r_id = f"00{num}" if self.context.args.get_arg("twin") else None
        self.ip_address = "127.0.0.1" if self.context.args.get_arg("twin") else None

        self.zone_proximity = 0.0
        self.current_zone = 0
        self.position_quality = 0.8 if self.context.args.get_arg("twin") else 0.5

        self.chassis = Rect(0, 0, c.ROBOT_HEIGHT, c.ROBOT_WIDTH, from_center=True)
        self.wheel_base = Rect(0, 0, c.ROBOT_WHEEL_OFFSET_Y, c.ROBOT_WHEEL_OFFSET_X, from_center=True)
        self.wheels = self._make_wheels()

        self.current_cell = None
        self.two_wheels = []

        self.full_frame = Rect(
            0,
            0,
            c.ROBOT_WHEEL_OFFSET_Y + c.ROBOT_WHEEL_WIDTH,
            c.ROBOT_WHEEL_OFFSET_X + c.ROBOT_WHEEL_RADIUS,
            from_center=True,
        )

        Thread(target=self._update_cell_info, daemon=True).start()

    def _update_cell_info(self):
        while True:
            time.sleep(0.02)
            two_wheels = []
            target_cell = 99
            if self.position_quality >= 0.1:
                for cell in self.context.field.cells:
                    if cell.contains(self.chassis):
                        target_cell = cell.seq_number
                    ctr = 0
                    for wheel in self.wheels:
                        if cell.contains(wheel):
                            ctr += 1
                    if ctr >= 2:
                        two_wheels.append(cell.seq_number)
            self.current_cell = target_cell
            self.two_wheels = two_wheels

    def _make_wheels(self):
        return [
            Rect(
                self.wheel_base.get_vertices()[0][0],
                self.wheel_base.get_vertices()[0][1],
                c.ROBOT_WHEEL_RADIUS,
                c.ROBOT_WHEEL_WIDTH,
                from_center=True,
            ),
            Rect(
                self.wheel_base.get_vertices()[1][0],
                self.wheel_base.get_vertices()[1][1],
                c.ROBOT_WHEEL_RADIUS,
                c.ROBOT_WHEEL_WIDTH,
                from_center=True,
            ),
            Rect(
                self.wheel_base.get_vertices()[2][0],
                self.wheel_base.get_vertices()[2][1],
                c.ROBOT_WHEEL_RADIUS,
                c.ROBOT_WHEEL_WIDTH,
                from_center=True,
            ),
            Rect(
                self.wheel_base.get_vertices()[3][0],
                self.wheel_base.get_vertices()[3][1],
                c.ROBOT_WHEEL_RADIUS,
                c.ROBOT_WHEEL_WIDTH,
                from_center=True,
            ),
        ]

    def move(self, x, y, r=0):
        self.chassis.move(x, y, r)
        self.wheel_base.move(x, y, r)
        self.wheels[0].move(
            self.wheel_base.get_vertices()[0][0],
            self.wheel_base.get_vertices()[0][1],
            r,
        )
        self.wheels[1].move(
            self.wheel_base.get_vertices()[1][0],
            self.wheel_base.get_vertices()[1][1],
            r,
        )
        self.wheels[2].move(
            self.wheel_base.get_vertices()[2][0],
            self.wheel_base.get_vertices()[2][1],
            r,
        )
        self.wheels[3].move(
            self.wheel_base.get_vertices()[3][0],
            self.wheel_base.get_vertices()[3][1],
            r,
        )
        self.full_frame.move(x, y, r)


class Robots:
    def __init__(self, context):
        self.context = context
        num_robots = 1 if context.args.get_arg("twin") else c.NUM_ROBOTS
        self.list = [Robot(context, _) for _ in range(num_robots)]

        self.current_robot = self.list[0] if self.list else None
        Thread(target=self.update_solo_active_robot, daemon=True).start()

    def select_robot(self, index):
        r_found = False
        for robot in self.list:
            if robot.r_id == index:
                self.current_robot = robot
                r_found = True
        if not r_found:
            self.context.lg.error(f"Робот с идентификатором {index} не найден")

    def update_solo_active_robot(self):
        while True:
            time.sleep(1)
            last_on_polygon = None
            found_on_polygon = 0
            for robot in self.list:
                if robot.position_quality >= 0.8:
                    last_on_polygon = robot.r_id
                    found_on_polygon += 1

            if found_on_polygon == 1:
                self.select_robot(last_on_polygon)
