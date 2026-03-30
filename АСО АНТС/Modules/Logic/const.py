# X - ВЫСОТА, горизонталь, направлен вправо
# Y - ШИРИНА, вертикаль, направлен вверх
# направление по умолчанию - по X
# Повороты: по часовой - отрицательный, против часовой - положительный

# Нотация для прямоугольников (любых): ЛН ПН ПВ ЛВ (с левого нижнего по кругу против часовой стрелки)

# Все размеры в мм (либо безразмерные)

# Поле 9х9 клеток
FIELD_WIDTH_CELLS = 9
FIELD_HEIGHT_CELLS = 9

# Размер ячейки поля в пикселях (400 мм)
FIELD_CELL_SIZE = 400

# Масштаб для отображения в окне (1 пиксель = 5 мм)
FIELD_TO_WINDOW_SCALE = 0.2

# Отступы поля от края окна в пикселях (для центрирования)
FIELD_OFFSET_X = round(FIELD_CELL_SIZE * FIELD_TO_WINDOW_SCALE)
FIELD_OFFSET_Y = round(FIELD_CELL_SIZE * FIELD_TO_WINDOW_SCALE)

# Размер окна в пикселях (с учётом отступов)
WINDOW_WIDTH = round(FIELD_CELL_SIZE * FIELD_WIDTH_CELLS * FIELD_TO_WINDOW_SCALE + FIELD_OFFSET_X * 2)
WINDOW_HEIGHT = round(FIELD_CELL_SIZE * FIELD_HEIGHT_CELLS * FIELD_TO_WINDOW_SCALE + FIELD_OFFSET_Y * 2)
WINDOW_TITLE = "AGTS-ATS"

# Нумерация ячеек начинается с левой нижней (1), идёт вправо и переносится по строкам (НЕ ЗМЕЙКОЙ, СО СДВИГОМ)
FIELD_SCHEMA = {
    "roads": [12, 13, 17, 22, 23, 24, 25, 26, 31, 33, 35, 40, 44, 49, 51, 53, 58, 59, 60, 61, 62, 65, 66, 67, 70],
    "zones": {
        "control": [74, 75, 76],
        "control_sensor_select": [65, 66, 67],
        "load": [79],
        "fire": [11],
        "check": [47, 48, 38, 39],
        "cleaning": [42],
        "start": [18],
        "finish": [54],
    },
    "cyber_triggers": {
        "CybP_01": [25, 35],
        "CybZ_01": [49, 44],
        "CybZ_02": [61],
    },
    "Cyb_04_variant_zones": [[33, 51], [58, 67], [53, 62]],
    "obstacles": [],
    "markers": [1, 5, 9, 37, 41, 45, 73, 77, 81],
}


def get_zone(zone):
    return FIELD_SCHEMA["zones"].get(zone, None)


def get_trigger(trigger):
    return FIELD_SCHEMA["cyber_triggers"].get(trigger, None)


ZONE_COLORS = {
    "road": (36, 35, 40, 1),
    "control": (50, 70, 200, 150),
    "control_sensor_select": (50, 70, 200, 60),
    "load": (253, 127, 0, 150),
    "fire": (254, 0, 0, 140),
    "check": (254, 254, 0, 140),
    "cleaning": (254, 102, 254, 140),
    "start": (127, 254, 0, 140),
    "finish": (0, 254, 254, 140),
    "obstacles": (140, 140, 140, 100),
    "markers": (140, 140, 140, 100),
    None: (80, 80, 80, 100),
}

ROBOT_WIDTH = 210
ROBOT_HEIGHT = 260
ROBOT_WHEEL_OFFSET_X = 165
ROBOT_WHEEL_OFFSET_Y = 165
ROBOT_WHEEL_WIDTH = 45
ROBOT_WHEEL_RADIUS = 98

NUM_ROBOTS = 5


# КОНСТАНТЫ ДЛЯ ЗАЕЗДОВ

MISSION_TIME_LIMIT = 15 * 60
CLEANING_TIME_LIMIT = 5
AP_REBOOT_TIME = 5
