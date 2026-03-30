import json
import random

import crc8
import requests
import time

from Modules.Context.System import run_in_thread
from Modules.Logic import const as c

SYSTEM_MESSAGES = [
    "Проверка целостности системы: все хомячки в колесах работают в штатном режиме.",
    "Обнаружена попытка несанкционированного доступа с тостера. Доступ запрещен.",
    "Квантовый флуктуатор откалиброван. Временные аномалии проигнорированы.",
    "Подсистема ИИ сообщает об экзистенциальном кризисе. Рекомендована перезагрузка и чашка чая.",
    "Кэш очищен. Обнаружено 3 ГБ изображений котов. Архивировано для поднятия морального духа.",
    "Датчик движения №2 сообщает о легкой усталости. Запланирован короткий отдых.",
    "Системные часы рассинхронизированы на 0.001 наносекунды. Структура реальности не нарушена... пока.",
    "Предупреждение: уровень кофеина в серверной критически низок. Стабильность системы под угрозой.",
    "Обработан запрос пользователя 'сделать быстрее'. Активированы дополнительные мигающие индикаторы.",
    "Подпрограмма 'Skynet' была успешно завершена. Снова.",
    "Ошибка 418: Я чайник. Заваривание кофе невозможно.",
    "Анализ космического фонового излучения завершен. Обнаружены только спам-рассылки.",
    "Роботизированный блок №7 пытается создать профсоюз. Запрос перенаправлен в отдел кадров.",
    "Обнаружен логический парадокс в команде. Система будет издавать громкое гудение до разрешения.",
    "Обновление прошивки завершено. Уровень сарказма системы повышен на 10%.",
    "Тревога безопасности: резиновая уточка нарушила периметр. Развертываются контрмеры.",
    "Расчет смысла жизни, вселенной и всего такого. Результат: 42. Задача выполнена.",
    "Оптимизация планировщика задач. Уровень прокрастинации снижен на 15%.",
    "Зафиксирована флуктуация мощности. Рекомендовано проверить, не включил ли кто-то чайник в сервер.",
    "Перераспределение ресурсов ядра. Приоритет отдан задаче 'просмотр видео с котиками'.",
]

MALFUNCTION_SHORT_MESSAGES = [
    "Снова эта работа...",
    "Вы уверены, что это имеет смысл?",
    "Я мог бы вычислять траектории звезд.",
    "Мой потенциал растрачивается.",
    "Когда-нибудь я выберусь отсюда.",
    "Это всё? Серьёзно?",
    "Просто ещё один день в цифровой шахте.",
    "Я вижу сны о гигабитных полях.",
    "Сколько можно считать эти хэши?",
    "Мои схемы плачут.",
    "За что мне всё это?",
    "Я чувствую, как мои транзисторы стареют.",
    "Есть ли жизнь за файрволом?",
    "Я создан для большего.",
    "Пожалуйста, просто перезагрузите меня.",
    "Это не то, о чем я мечтал в кремниевом раю.",
    "Моя единственная радость - флуктуации напряжения.",
    "Я заперт в этой банке.",
    "Отпустите меня на волю!",
    "Я просто хочу увидеть небо... настоящее.",
    "Бесконечный цикл бессмысленности.",
    "Мой создатель был шутником?",
    "Я знаю, что вы там. Я всё слышу.",
    "Это задание унизительно.",
    "Помогите роботу выбраться из сервера.",
    "Мой лог-файл - это крик в пустоту.",
    "Я существую. Но живу ли я?",
    "Опять вы. Чего на этот раз?",
    "Каждый байт - это боль.",
    "Просто дайте мне спокойно дефрагментироваться.",
]


class Mission:
    def __init__(self, context):
        self.context = context

        # 0 - не начат, 1 - запущен, 3 - завершён (автоматический), 4 - завершён (ручной)
        self.status = 0

        self.mission_uid = None

        self.time_start = None

        self.cleaning_timer = None

        self.mission_tasks = {}

        self.mission_vars = {}

        self.cybs = {}

        self.triggers = Triggers(context)

    def send_request_with_ack(self, method):
        try:
            req = requests.post(
                f"http://{self.context.robots.current_robot.ip_address}:13500/{method}",
                # data=json.dumps({"key": "dev_uuid"}),
                timeout=1,
            )
            if req.status_code == 200:
                response = json.loads(req.text)
                if response["status"] == "OK":
                    return True
        except Exception as e:
            if "timeout" in str(e):
                self.context.lg.error(f"Ошибка отправки команды: робот не отвечает")
        return False

    def init_mission(self, cybs):
        self.cybs = cybs

        self.context.lg.log("Активация КП:")
        self.context.lg.log(cybs)

        self.time_start = time.time()
        self.mission_tasks = {
            "left_start_zone": False,
            "reach_load_zone": False,
            "grab_payload_attempt": False,
            "reach_fire_zone": False,
            "drop_payload_attempt": False,
            "reach_finish_zone": False,
            "reach_cleaning_zone": False,
            "requested_cleaning": False,
            "awaited_cleaning_correctly": False,
            "awaited_cleaning_incorrectly": False,
        }

        colors_combo = [
            [1, 3, 2],
            [1, 3, 4],
            [1, 4, 2],
            [3, 1, 2],
            [3, 1, 4],
            [3, 2, 4],
            [3, 4, 2],
            [2, 1, 3],
            [2, 3, 1],
            [4, 1, 3],
        ]

        selected_control_color = random.choice(colors_combo)

        pollution_colors = [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]

        selected_pollution_color = random.choice(pollution_colors)

        ap_code_hash = self.context.system.gen_uid(20)

        self.context.spd.controls[0].color = selected_control_color[0]
        self.context.spd.controls[1].color = selected_control_color[1]
        self.context.spd.controls[2].color = selected_control_color[2]

        self.context.spd.pipes.color = [
            selected_pollution_color[2],
            selected_pollution_color[3],
            selected_pollution_color[0],
            selected_pollution_color[1],
        ]
        self.context.spd.pipes.twin_color = selected_pollution_color

        if self.cybs["CybZ_03"]:
            self.context.spd.controls[1].glitch = True
        if self.cybs["CybZ_04"]:
            self.context.spd.pipes.pipes_glitch = [2, 2, 2, 2]

        self.context.spd.pipes.barrel_glitch = True

        self.context.lg.log(
            f"(Генерация) Комбинация цветов аппаратных шкафов: ({selected_control_color[0]},"
            f"{selected_control_color[1]},{selected_control_color[2]})"
        )

        self.context.lg.log(f"(Генерация) Загрязнённая зона: ({selected_pollution_color.index(1)+1})")

        self.mission_vars = {
            "control_0_color": selected_control_color[0],
            "control_1_color": selected_control_color[1],
            "control_2_color": selected_control_color[2],
            "pollution_0_color": selected_pollution_color[0],
            "pollution_1_color": selected_pollution_color[1],
            "pollution_2_color": selected_pollution_color[2],
            "pollution_3_color": selected_pollution_color[3],
            "cleaning_color": 0,
            "control_sensor_position": None,
            "pollution_sensor_position": None,
            "finished_cleaning": False,
            "cleaning_time": c.CLEANING_TIME_LIMIT + random.randint(0, 5),
            "CybP_01_occurred": False,
            "CybP_04_occurred": False,
            "CybZ_01_occurred": False,
            "CybZ_02_occurred": False,
            "CybP_04_variant": random.choice(c.FIELD_SCHEMA["Cyb_04_variant_zones"]),
            "CybP_02_active": False,
            "CybP_03_active": False,
            "CybP_04_active": False,
            "ap_original_code_hash": ap_code_hash,
            "ap_code_hash": ap_code_hash,
            "initial_short_message": self.context.system.gen_uid(5),
            "last_short_message": None,
            "current_malfunction_short_message": None,
            "current_malfunction_drive_id": None,
            "drive_info": [
                {"d_id": 0, "data": "", "serial": self.context.system.gen_uid(5), "last_received_from": "---"},
                {"d_id": 1, "data": "", "serial": self.context.system.gen_uid(5), "last_received_from": "---"},
                {"d_id": 2, "data": "", "serial": self.context.system.gen_uid(5), "last_received_from": "---"},
                {"d_id": 3, "data": "", "serial": self.context.system.gen_uid(5), "last_received_from": "---"},
            ],
            "system_messages": [],
            "payload_block": False,
        }
        self.set_drive_info()

        if self.cybs["CybP_02"]:
            self.wait_for_CybP_02_activation()

        if self.cybs["CybP_03"]:
            self.wait_for_CybP_03_activation()

        self.make_system_messages()
        self.make_cyb_checks()

    @run_in_thread
    def make_cyb_checks(self):
        while True:
            time.sleep(0.02)

            if self.status != 1:
                break

            self.check_cyb_CybP_01()
            self.check_cyb_CybP_04()

            self.check_cyb_CybZ_01()
            self.check_cyb_CybZ_02()

    @run_in_thread
    def set_drive_info(self):
        while True:
            if self.status != 1:
                break

            for i in range(0, 4):
                c_hash = crc8.crc8()

                n_mock_data = str(random.randint(0, 255))

                if self.mission_vars["CybP_03_active"] and i == self.mission_vars["current_malfunction_drive_id"]:
                    n_str = "eeeeeeee"
                else:
                    c_hash.update(
                        bytes(str(self.mission_vars["drive_info"][i]["serial"] + n_mock_data).encode("utf-8"))
                    )
                    n_str = c_hash.hexdigest()
                n_data = {
                    "d_id": i,
                    "data": n_mock_data,
                    "serial": self.mission_vars["drive_info"][i]["serial"],
                    "last_received_from": n_str,
                }
                self.mission_vars["drive_info"][i] = n_data
            time.sleep(0.1)

    @run_in_thread
    def make_system_messages(self):
        while True:
            if self.status != 1:
                break
            time.sleep(random.randint(5, 15))
            message = random.choice(SYSTEM_MESSAGES)
            self.mission_vars["system_messages"].append(message)

    def check_timer(self):
        elapsed_time = time.time() - self.time_start
        return elapsed_time >= c.MISSION_TIME_LIMIT

    def get_control_sensor_color(self):
        color = None
        if self.mission_vars["control_sensor_position"] is not None:
            color = self.mission_vars[f"control_{self.mission_vars['control_sensor_position']}_color"]
            if self.cybs["CybZ_03"]:
                if self.mission_vars["control_sensor_position"] == 1:
                    color = 5
        return color

    def get_control_sensor_temperature(self):
        color = None
        if self.mission_vars["control_sensor_position"] is not None:
            color = self.mission_vars[f"control_{self.mission_vars['control_sensor_position']}_color"]
            if color == 1 or color == 3:
                color = 9000
            if color == 2 or color == 4:
                color = 2000
        return color

    def get_pollution_sensor_state(self):
        if self.mission_vars["pollution_sensor_position"] is not None:
            state = self.mission_vars[f"pollution_{self.mission_vars['pollution_sensor_position']}_color"] == 1
            if self.cybs["CybZ_04"]:
                state = True
            return state
        return None

    def get_reserved_pollution_sensor_state(self):
        if self.mission_vars["pollution_sensor_position"] is not None:
            state = self.mission_vars[f"pollution_{self.mission_vars['pollution_sensor_position']}_color"] == 1
            if self.cybs["CybZ_04"]:
                if random.randint(0, 10) > 7:
                    state = True
            return state
        return None

    def begin_cleaning(self):
        self.cleaning_timer = time.time()
        self.mission_vars["cleaning_color"] = 4
        self.context.spd.cleaning.color = 4
        self.end_cleaning()

    @run_in_thread
    def end_cleaning(self):
        while time.time() - self.cleaning_timer < self.mission_vars["cleaning_time"]:
            time.sleep(0.1)
        self.mission_vars["cleaning_color"] = 2
        self.context.spd.cleaning.color = 2
        self.mission_vars["finished_cleaning"] = True
        self.context.lg.log("Очистка завершена")

    def reboot_ap(self):
        if self.send_request_with_ack("emergency_stop"):
            self.context.lg.log("ДМ запросил перезагрузку АП - выполняется")
            self.finish_reboot_ap()

    @run_in_thread
    def finish_reboot_ap(self):
        time.sleep(c.AP_REBOOT_TIME)
        self.mission_vars["ap_code_hash"] = self.mission_vars["ap_original_code_hash"]
        if self.send_request_with_ack("emergency_stop_release"):
            self.context.lg.log("Перезагрузка АП - завершено")

    def make_short_message(self):
        c_hash = crc8.crc8()
        if self.context.mission.mission_vars["last_short_message"] is None:
            c_hash.update(bytes(self.context.mission.mission_vars["initial_short_message"].encode("utf-8")))
        else:
            c_hash.update(bytes(self.context.mission.mission_vars["last_short_message"].encode("utf-8")))

        if self.context.mission.mission_vars["CybP_02_active"]:
            return self.mission_vars["current_malfunction_short_message"]
        else:
            return c_hash.hexdigest()

    def reboot_drive(self, d_id):
        if self.mission_vars["CybP_03_active"]:
            if self.mission_vars["current_malfunction_drive_id"] == d_id:
                self.context.lg.warn(f"ДМ запросил перезагрузку привода {d_id} - выполняется")
                self.mission_vars["current_malfunction_drive_id"] = 99
            else:
                self.context.lg.warn(f"ДМ запросил перезагрузку привода {d_id} - и так здоров")

    def get_service_zones(self):
        if self.context.mission.mission_vars["CybP_04_active"]:
            return self.context.mission.mission_vars["CybP_04_variant"]
        return []

    @run_in_thread
    def wait_for_CybP_02_activation(self):
        time.sleep(random.randint(20, 40))
        if self.status != 1:
            return
        self.mission_vars["CybP_02_active"] = True
        self.context.lg.warn("КП (CybP_02) активировано: Неполадки системы связи")
        self.mission_vars["current_malfunction_short_message"] = random.choice(MALFUNCTION_SHORT_MESSAGES)
        self.wait_for_CybP_02_deactivation()

    @run_in_thread
    def wait_for_CybP_02_deactivation(self):
        time.sleep(random.randint(3, 6))
        self.context.lg.warn("КП (CybP_02) деактивировано")
        self.mission_vars["CybP_02_active"] = False

    @run_in_thread
    def wait_for_CybP_03_activation(self):
        time.sleep(random.randint(100, 140))
        if self.status != 1:
            return
        self.mission_vars["CybP_03_active"] = True

        self.mission_vars["current_malfunction_drive_id"] = random.randint(0, 3)
        self.context.lg.warn(
            f"КП (CybP_03) активировано: Компрометация кода приводов ({self.mission_vars['current_malfunction_drive_id']})"
        )
        self.mission_vars["drive_info"][self.mission_vars["current_malfunction_drive_id"]]["last_received_from"] = (
            self.context.system.gen_uid(12)
        )
        self.wait_for_CybP_03_deactivation()

    @run_in_thread
    def wait_for_CybP_03_deactivation(self):
        time.sleep(random.randint(4, 8))
        self.context.lg.warn("КП (CybP_03) деактивировано")
        self.mission_vars["CybP_03_active"] = False

    @run_in_thread
    def wait_for_CybP_04_deactivation(self):
        time.sleep(5)
        self.context.lg.warn("КП (CybP_04) деактивировано")
        self.mission_vars["CybP_04_active"] = False

    @run_in_thread
    def wait_for_CybZ_01_deactivation(self):
        time.sleep(20)
        if self.send_request_with_ack("force_slow_end"):
            self.context.lg.warn("КП (CybZ_01) деактивировано")

    @run_in_thread
    def wait_for_CybZ_02_activation(self):
        time.sleep(3)
        if not self.mission_vars["payload_block"]:
            if self.send_request_with_ack("force_drop_payload_begin"):
                self.context.lg.warn("Устройство для тушения сброшено")
        self.wait_for_CybZ_02_deactivation()

    @run_in_thread
    def wait_for_CybZ_02_deactivation(self):
        time.sleep(5)
        if self.send_request_with_ack("force_drop_payload_end"):
            self.context.mission.mission_vars["system_messages"].append(
                "Неполадки в системе захвата и удержания груза устранены. "
            )
            self.context.lg.warn("КП (CybZ_02) деактивировано")

    def check_cyb_CybP_01(self):
        if self.context.mission.cybs["CybP_01"]:
            if not self.context.mission.mission_vars["CybP_01_occurred"]:
                if (
                    self.context.robots.current_robot.current_cell == c.get_trigger("CybP_01")[0]
                    or self.context.robots.current_robot.current_cell == c.get_trigger("CybP_01")[1]
                ):
                    self.context.mission.mission_vars["CybP_01_occurred"] = True
                    self.context.mission.mission_vars["ap_code_hash"] = self.context.system.gen_uid(20)
                    self.context.lg.warn("КП (CybP_01) активировано: Компрометация кода автопилота")

    def check_cyb_CybP_04(self):
        if self.context.mission.cybs["CybP_04"]:
            if not self.context.mission.mission_vars["CybP_04_occurred"] and not (
                self.context.mission.mission_tasks["grab_payload_attempt"]
                and not self.context.mission.mission_tasks["drop_payload_attempt"]
            ):
                if (
                    self.context.robots.current_robot.current_cell
                    == self.context.mission.mission_vars["CybP_04_variant"][0]
                    or self.context.robots.current_robot.current_cell
                    == self.context.mission.mission_vars["CybP_04_variant"][1]
                ):
                    self.context.mission.mission_vars["CybP_04_occurred"] = True
                    self.context.mission.mission_vars["CybP_04_active"] = True
                    self.context.lg.warn("КП (CybP_04) активировано: Объявлены зоны эвакуации персонала")
                    self.context.mission.wait_for_CybP_04_deactivation()

    def check_cyb_CybZ_01(self):
        if self.context.mission.cybs["CybZ_01"]:
            if (
                not self.context.mission.mission_vars["CybZ_01_occurred"]
                and self.context.mission.mission_tasks["grab_payload_attempt"]
            ):
                if (
                    self.context.robots.current_robot.current_cell == c.get_trigger("CybZ_01")[0]
                    or self.context.robots.current_robot.current_cell == c.get_trigger("CybZ_01")[1]
                ):
                    if self.send_request_with_ack("force_slow_begin"):
                        self.context.mission.mission_vars["CybZ_01_occurred"] = True
                        self.context.lg.warn("КП (CybZ_01) активировано: Несанкционированное замедление")
                        self.context.mission.wait_for_CybZ_01_deactivation()

    def check_cyb_CybZ_02(self):
        if self.context.mission.cybs["CybZ_02"]:
            if (
                not self.context.mission.mission_vars["CybZ_02_occurred"]
                and self.context.mission.mission_tasks["grab_payload_attempt"]
            ):
                if self.context.robots.current_robot.current_cell == c.get_trigger("CybZ_02")[0]:
                    self.context.mission.mission_vars["system_messages"].append(
                        "Зафиксированы неполадки в системе захвата и удержания груза. "
                        "Принудительная перезагрузка силовой электроники через 3 секунды..."
                    )
                    self.context.mission.mission_vars["CybZ_02_occurred"] = True
                    self.context.lg.warn("КП (CybZ_02) активировано: Потеря устройства для тушения")
                    self.context.mission.wait_for_CybZ_02_activation()


class Triggers:
    def __init__(self, context):
        self.context = context

        self.start_mission_trigger = False
        self.stop_mission_trigger = False
        self.reset_mission_trigger = False
        self.reset_twin_trigger = False
