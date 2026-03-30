import argparse
from typing import Dict, Any


class ArgParser:
    def __init__(self, context):
        self.context = context
        self.parser = argparse.ArgumentParser(
            description="AGTS ATS - Автоматическая система отслеживания",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        self._setup_arguments()
        self.args = None

    def _setup_arguments(self):
        """Настройка аргументов командной строки"""
        self.parser.add_argument(
            "-t",
            "--twin",
            action="store_true",
            dest="twin",
            help="Запуск системы в режиме работы с цифровым двойником",
        )

    def parse_args(self) -> Dict[str, Any]:
        """Парсинг аргументов командной строки"""
        self.args = self.parser.parse_args()
        return vars(self.args)

    def get_arg(self, name: str) -> Any:
        """Получить значение конкретного аргумента"""
        if self.args is None:
            self.parse_args()
        return getattr(self.args, name.replace("-", "_"), None)

    def has_arg(self, name: str) -> bool:
        """Проверить, был ли передан аргумент"""
        return self.get_arg(name) is True

    def print_help(self):
        """Показать справку"""
        self.parser.print_help()
