from __future__ import annotations

import math
from typing import Self

import Modules.Logic.const as c


class Rect:
    def __init__(
        self,
        x: int,
        y: int,
        height: int,
        width: int,
        from_center: bool = False,
        rotation: int = 0,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.from_center = from_center
        self.rotation = rotation
        self.vertices = self._generate_vertices(x, y, rotation)

    def _generate_vertices(self, x, y, r):
        if self.from_center:
            half_x = self.height / 2
            half_y = self.width / 2
            unrotated_vertices = [
                (x - half_x, y - half_y),
                (x - half_x + self.height, y - half_y),
                (x - half_x + self.height, y - half_y + self.width),
                (x - half_x, y - half_y + self.width),
            ]
        else:
            unrotated_vertices = [
                (x, y),
                (x + self.height, y),
                (x + self.height, y + self.width),
                (x, y + self.width),
            ]

        if r == 0:
            return tuple(unrotated_vertices)

        rotated_vertices = [self._rotate_point(p, (x, y), r) for p in unrotated_vertices]
        return tuple(rotated_vertices)

    @staticmethod
    def _rotate_point(
        point: tuple[float, float], center: tuple[float, float], angle_degrees: float
    ) -> tuple[float, float]:
        angle_radians = math.radians(angle_degrees)
        x, y = point
        cx, cy = center
        cos_angle = math.cos(angle_radians)
        sin_angle = math.sin(angle_radians)
        translated_x = x - cx
        translated_y = y - cy
        rotated_x = translated_x * cos_angle - translated_y * sin_angle
        rotated_y = translated_x * sin_angle + translated_y * cos_angle
        new_x = rotated_x + cx
        new_y = rotated_y + cy

        return round(new_x), round(new_y)

    def _contains_point(self, point: tuple[float, float]) -> bool:
        """Проверяет, находится ли точка внутри этого прямоугольника (включая границы)."""
        vertices = self.get_vertices()
        px, py = point

        for i in range(4):
            p1 = vertices[i]
            p2 = vertices[(i + 1) % 4]  # Следующая вершина, с замыканием для последнего ребра

            # Вектор ребра
            edge_x = p2[0] - p1[0]
            edge_y = p2[1] - p1[1]

            # Вектор от начала ребра до точки
            point_vec_x = px - p1[0]
            point_vec_y = py - p1[1]

            # Векторное произведение. Если вершины в порядке против часовой стрелки,
            # точка должна быть "слева" от каждого ребра, т.е. произведение >= 0.
            cross_product = edge_x * point_vec_y - edge_y * point_vec_x
            if cross_product < 0:
                return False  # Точка снаружи

        return True

    def _get_axes(self) -> list[tuple[float, float]]:
        """Получает оси для проверки (нормали к рёбрам)."""
        axes = []
        vertices = self.get_vertices()
        # Для прямоугольника достаточно двух уникальных осей
        for i in range(2):
            p1 = vertices[i]
            p2 = vertices[i + 1]
            edge = (p1[0] - p2[0], p1[1] - p2[1])
            # Нормаль к ребру
            normal = (-edge[1], edge[0])
            axes.append(normal)
        return axes

    def _project(self, axis: tuple[float, float]) -> tuple[float, float]:
        """Проецирует прямоугольник на ось и возвращает минимальное и максимальное значения."""
        min_p = float("inf")
        max_p = float("-inf")
        for vertex in self.get_vertices():
            # Скалярное произведение для получения проекции
            projection = vertex[0] * axis[0] + vertex[1] * axis[1]
            min_p = min(min_p, projection)
            max_p = max(max_p, projection)
        return min_p, max_p

    @staticmethod
    def _overlap(proj1: tuple[float, float], proj2: tuple[float, float]) -> bool:
        """Проверяет, пересекаются ли две проекции (два отрезка на прямой)."""
        return proj1[1] >= proj2[0] and proj2[1] >= proj1[0]

    def move(self, x, y, r=0):
        self.x = x
        self.y = y
        self.vertices = self._generate_vertices(x, y, r)
        return self.vertices

    def intersects(self, other: Self) -> bool:
        """
        Проверяет пересечение с другим прямоугольником, используя теорему о разделяющей оси (SAT).
        """
        axes = self._get_axes() + other._get_axes()

        for axis in axes:
            proj1 = self._project(axis)
            proj2 = other._project(axis)

            if not self._overlap(proj1, proj2):
                return False  # Найдена разделяющая ось, пересечения нет

        return True  # Разделяющих осей не найдено, прямоугольники пересекаются

    def contains(self, other: Self) -> bool:
        """Проверяет, находится ли другой прямоугольник полностью внутри этого."""
        for vertex in other.get_vertices():
            if not self._contains_point(vertex):
                return False
        return True

    def get_vertices(self):
        return self.vertices

    def get_scaled_vertices(self) -> list[tuple[float, float]]:
        return [
            (round(x * c.FIELD_TO_WINDOW_SCALE), round(y * c.FIELD_TO_WINDOW_SCALE)) for x, y in self.get_vertices()
        ]

    def get_translated_vertices(self) -> list[tuple[float, float]]:
        return [(x + c.FIELD_OFFSET_X, y + c.FIELD_OFFSET_Y) for x, y in self.get_scaled_vertices()]

    def get_indicator_vertices(self) -> list[tuple[float, float]]:
        vertices = self.get_translated_vertices()
        return [
            (vertices[0][0], vertices[0][1]),
            (vertices[1][0] - 50, vertices[1][1]),
            (vertices[2][0] - 50, vertices[2][1] - 50),
            (vertices[3][0], vertices[3][1] - 50),
        ]

    def get_translated_center(self) -> tuple[float, float]:
        return (
            round(self.x * c.FIELD_TO_WINDOW_SCALE) + c.FIELD_OFFSET_X,
            round(self.y * c.FIELD_TO_WINDOW_SCALE) + c.FIELD_OFFSET_Y,
        )


class FieldCell(Rect):
    def __init__(
        self,
        x_offset_cells,
        y_offset_cells,
        seq_number: int,
        zone_type: None | str = None,
    ):
        super().__init__(
            x_offset_cells * c.FIELD_CELL_SIZE,
            y_offset_cells * c.FIELD_CELL_SIZE,
            c.FIELD_CELL_SIZE,
            c.FIELD_CELL_SIZE,
        )
        self.seq_number: int = seq_number
        self.zone_type: None | str = zone_type

        self.indicator = None

    def set_indicator(self, color: int):
        r_color = [0, 0, 0, 0]
        if color == 0:
            r_color = [255, 255, 255, 255]
        if color == 1:
            r_color = [255, 0, 0, 255]
        if color == 2:
            r_color = [0, 255, 0, 255]
        if color == 3:
            r_color = [255, 255, 0, 255]
        if color == 4:
            r_color = [0, 0, 255, 255]
        if color == 5:
            r_color = [255, 0, 255, 255]
        self.indicator = r_color


class Field:
    def __init__(self):
        self.cells: list[FieldCell] = []

        for y in range(c.FIELD_HEIGHT_CELLS):
            for x in range(c.FIELD_WIDTH_CELLS):
                self.cells.append(FieldCell(x, y, len(self.cells) + 1))

        for idx in c.FIELD_SCHEMA["roads"]:
            for cell in self.cells:
                if cell.seq_number == idx:
                    cell.zone_type = "road"

        for zone in c.FIELD_SCHEMA["zones"]:
            for idx in c.FIELD_SCHEMA["zones"][zone]:
                for cell in self.cells:
                    if cell.seq_number == idx:
                        cell.zone_type = zone

        for idx in c.FIELD_SCHEMA["obstacles"]:
            for cell in self.cells:
                if cell.seq_number == idx:
                    cell.zone_type = "obstacles"

        for idx in c.FIELD_SCHEMA["markers"]:
            for cell in self.cells:
                if cell.seq_number == idx:
                    cell.zone_type = "markers"

        # for cell in self.cells:
        #     print(f"Cell {cell.seq_number}: {cell.zone_type}")
