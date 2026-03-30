import time
import sys

from Modules import BaseHandler
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

# Проверяем, является ли система Windows, и импортируем msvcrt
is_windows = sys.platform == "win32"
if is_windows:
    import msvcrt


class CommandInterface(BaseHandler):
    def __init__(self, context):
        super().__init__(context)
        self.command_history = []
        self.history_index = -1

    def run(self):
        time.sleep(3)
        self.context.lg.log("Ожидаю ввод команд (/help для получения списка доступных команд)...")

        if not is_windows:
            self.context.lg.error(
                "Интерактивный ввод команд поддерживается только в Windows. Используйте /q для выхода."
            )
            # Оставляем старую логику для не-Windows систем
            while True:
                try:
                    command = input()
                    if command == "/q":
                        break
                except (KeyboardInterrupt, EOFError):
                    break
            return

        command_buffer = ""

        def get_renderable(text: str):
            cursor = "█" if int(time.time() * 2) % 2 == 0 else " "
            return Panel(Text(f"> {text}{cursor}", justify="left"), title="Командный ввод")

        with Live(get_renderable(""), console=self.context.lg.cls, refresh_per_second=10) as live:
            while True:
                try:
                    if msvcrt.kbhit():
                        char = msvcrt.getwch()
                        if char == "\r":  # Enter
                            if command_buffer:
                                self.process_command(command_buffer)
                                if not self.command_history or self.command_history[-1] != command_buffer:
                                    self.command_history.append(command_buffer)
                                self.history_index = len(self.command_history)
                                command_buffer = ""
                        elif char == "\xe0":  # Special key (arrows)
                            char = msvcrt.getwch()
                            if char == "H":  # Up arrow
                                if self.history_index > 0:
                                    self.history_index -= 1
                                    command_buffer = self.command_history[self.history_index]
                            elif char == "P":  # Down arrow
                                if self.history_index < len(self.command_history) - 1:
                                    self.history_index += 1
                                    command_buffer = self.command_history[self.history_index]
                                elif self.history_index == len(self.command_history) - 1:
                                    self.history_index += 1
                                    command_buffer = ""
                        elif char == "\x08":  # Backspace
                            command_buffer = command_buffer[:-1]
                        elif char == "\x03":  # Ctrl+C
                            break
                        else:
                            command_buffer += char

                    live.update(get_renderable(command_buffer))
                    time.sleep(0.02)

                except (KeyboardInterrupt, EOFError):
                    break
                except Exception as e:
                    self.context.lg.error(f"Ошибка в цикле ввода: {e}")
                    pass

    def process_command(self, command: str):
        self.context.lg.log(f"Выполнена команда: {command}")
        if not command.startswith("/"):
            self.context.lg.error("Ошибка ввода: команда должна начинаться с '/'")
            return

        if command == "/q":
            # Эта команда здесь не сработает для выхода из цикла,
            # но мы можем инициировать остановку приложения, если нужно.
            # Для выхода из цикла ввода используйте Ctrl+C.
            self.context.lg.log("Для выхода из командного интерфейса нажмите Ctrl+C.")
            return

        elif command == "/start":
            self.context.mission.triggers.start_mission_trigger = True
        elif command == "/stop":
            self.context.mission.triggers.stop_mission_trigger = True
        elif command == "/reset":
            self.context.mission.triggers.reset_mission_trigger = True
            self.context.mission.triggers.reset_twin_trigger = True
        elif command.startswith("/spd status"):
            self.context.lg.add_to_batch("Статус умных устройств:")
            self.context.lg.add_to_batch("")
            for dev in self.context.spd.controls:
                self.context.lg.add_to_batch(
                    f"Диспетчерский блок {dev.d_id}: {'в сети' if dev.is_alive else 'не в сети'}"
                )
            self.context.lg.add_to_batch(
                f"Зона очистки {self.context.spd.cleaning.d_id}: "
                f"{'в сети' if self.context.spd.cleaning.is_alive else 'не в сети'}"
            )

            self.context.lg.add_to_batch(
                f"Зона трубопровода {self.context.spd.pipes.d_id}: "
                f"{'в сети' if self.context.spd.pipes.is_alive else 'не в сети'}"
            )

            self.context.lg.add_to_batch(
                f"Пульт управления {self.context.spd.remote.d_id}: "
                f"{'в сети' if self.context.spd.remote.is_alive else 'не в сети'}"
            )
            self.context.lg.flush_batch()
        elif command.startswith("/spd set"):
            args = command.split()
            try:
                dev_id, color, glitch = args[2:]
                dev_id = dev_id.split("_")
                if dev_id[0] == "control":
                    self.context.spd.controls[int(dev_id[1])].color = color
                    self.context.spd.controls[int(dev_id[1])].glitch = glitch == "True"
                elif dev_id[0] == "cleaning":
                    self.context.spd.cleaning.color = color
                    self.context.spd.cleaning.glitch = glitch == "True"
                elif dev_id[0] == "pipes":
                    m_data = color.split("|")
                    self.context.spd.pipes.color = [m_data[0][1], m_data[1][1], m_data[2][1], m_data[3][1]]
                    self.context.spd.pipes.pipes_glitch = [m_data[0][0], m_data[1][0], m_data[2][0], m_data[3][0]]
                    self.context.spd.pipes.barrel_glitch = glitch == "True"
                self.context.lg.log("Установлено успешно")
            except (IndexError, ValueError):
                self.context.lg.error("Ошибка ввода: неверные аргументы")
        elif command.startswith("/robot select"):
            args = command.split()
            try:
                self.context.robots.select_robot(args[2])
            except IndexError:
                self.context.lg.error("Ошибка ввода: не указан r_id робота")
        elif command.startswith("/robot list"):
            self.context.lg.add_to_batch("Статус роботов:")
            self.context.lg.add_to_batch("")
            for robot in self.context.robots.list:
                self.context.lg.add_to_batch(f"Робот {robot.r_id}: position_quality={robot.position_quality}")
            self.context.lg.flush_batch()
        elif command == "/help":
            self.context.lg.add_to_batch("Список доступных команд:")
            self.context.lg.add_to_batch("")
            self.context.lg.add_to_batch("/q - выход из приложения (используйте Ctrl+C для выхода из ввода)")
            self.context.lg.add_to_batch("")
            self.context.lg.add_to_batch("/start - принудительный старт заезда")
            self.context.lg.add_to_batch("/stop - принудительное завершение заезда")
            self.context.lg.add_to_batch("/reset - восстановление исходного положения заезда")
            self.context.lg.add_to_batch("")
            self.context.lg.add_to_batch("/spd [bold bright_black]status[/] - получение статуса всех умных устройств")
            self.context.lg.add_to_batch(
                "/spd [bold bright_black]set[/] [sky_blue3]dev_id color glitch[/] - "
                "установка режима работы умного устройства (например, /spd set control_0 blue False или /spd set pipes_0 "
                "yellow|white|white|white False|True)"
            )
            self.context.lg.add_to_batch("")
            self.context.lg.add_to_batch(
                "/robot [bold bright_black]select[/] [sky_blue3]r_id[/] - выбрать активного робота"
            )
            self.context.lg.add_to_batch(
                "/robot [bold bright_black]list[/] - получить список доступных роботов и их статусы"
            )

            self.context.lg.add_to_batch("")

            self.context.lg.flush_batch()
        else:
            self.context.lg.error("Неизвестная команда: {}".format(command))
