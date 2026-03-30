import ast
import configparser
import json
import os
import re

from openlog import Logger

from .Robot import Robot
from .System import System


class Context:
    def __init__(self, init_ok: bool):
        self.init_ok = init_ok

        self.config = Config(self)
        self.lg = Logger(prefix="AwC", plain=True, write_to_file=True, in_dir=True, session=True)
        self.system = System(self)
        self.robot = Robot(self)

        self.motors_enable = False
        self.gripper_enable = False

        self.mission_state = False
        self.mission_checks_ok = False

        self.cybs = {}

        self.emergency_stop = False
        self.wait_flag = False


class Config:
    def __init__(self, context: Context):
        self.context = context
        config = configparser.ConfigParser()
        if os.path.getsize(os.path.dirname(os.path.abspath(__file__)) + "/../../config.ini") < 20:
            context.lg.error("config.ini повреждён или недоступен.")
            self.context.init_ok = False
            return
        config.read(os.path.dirname(os.path.abspath(__file__)) + "/../../config.ini")
        self.config = config

    @staticmethod
    def _detect_string_type(value: str):
        """Определяет тип строки по первому символу"""
        value = value.strip()
        if not value:
            return "string"

        first_char = value[0]
        if first_char == "[":
            return "list"
        elif first_char == "{":
            return "dict"
        elif first_char == "(":
            return "tuple"
        else:
            return "string"

    @staticmethod
    def _fix_basic_syntax_errors(value: str, expected_type: str) -> str:
        """Исправляет базовые синтаксические ошибки в строке"""
        value = value.strip()

        if expected_type == "list":
            # Исправляем отсутствующие кавычки для строк
            value = re.sub(
                r'\[([^"\[\]{}]+)\]',
                lambda m: "[" + ", ".join(f'"{item.strip()}"' for item in m.group(1).split(",")) + "]",
                value,
            )
            # Исправляем одинарные кавычки на двойные
            value = value.replace("'", '"')

        elif expected_type == "dict":
            # Исправляем одинарные кавычки на двойные
            value = value.replace("'", '"')
            # Исправляем ключи без кавычек
            value = re.sub(r"(\w+):", r'"\1":', value)

        elif expected_type == "tuple":
            # Преобразуем в список для JSON парсинга, потом обратно в tuple
            if value.startswith("(") and value.endswith(")"):
                value = "[" + value[1:-1] + "]"

        return value

    def _parse_complex_value(self, value: str):
        """Преобразует строку в соответствующий объект (список, словарь, кортеж)"""
        original_value = value
        value_type = self._detect_string_type(value)

        if value_type == "string":
            return value

        try:
            # Сначала пробуем ast.literal_eval (безопаснее)
            if value_type == "tuple":
                # Для кортежей используем ast.literal_eval напрямую
                return ast.literal_eval(original_value)
            else:
                return ast.literal_eval(value)

        except (ValueError, SyntaxError):
            try:
                # Пробуем исправить базовые ошибки
                fixed_value = self._fix_basic_syntax_errors(value, value_type)

                if value_type == "tuple":
                    # Для кортежей парсим как список, потом конвертируем
                    parsed = json.loads(fixed_value)
                    return tuple(parsed) if isinstance(parsed, list) else parsed
                else:
                    return json.loads(fixed_value)

            except (json.JSONDecodeError, ValueError, SyntaxError) as e:
                # Если не удалось исправить, логируем ошибку и возвращаем строку
                self.context.lg.error(f"Не удалось преобразовать значение '{original_value}' в {value_type}: {str(e)}")
                return original_value

    def get(self, section: str, key: str):
        try:
            if self.config[section][key] is not None:
                raw_value = self.config[section][key]

                # Сначала пробуем преобразовать в число
                try:
                    val = int(raw_value)
                    if val == 0 or val == 1:
                        return bool(val)
                    else:
                        return val
                except ValueError:
                    try:
                        val = float(raw_value)
                        return val
                    except ValueError:
                        if raw_value[0] == "|":
                            return raw_value[1:].strip()
                        else:
                            return self._parse_complex_value(raw_value)
            else:
                self.context.lg.error(f"{key} не найден в секции {section} конфига")
                return None
        except:
            self.context.lg.error(f"{key} не найден в секции {section} конфига")
            return None

    def set(self, section: str, key: str, value):
        self.config.set(section, key, value)
        config_file = open(os.path.dirname(os.path.abspath(__file__)) + "/../../config.ini", "w")
        self.config.write(config_file)
