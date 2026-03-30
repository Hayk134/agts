import configparser
import os

from openlog import Logger

from .ArgParser import ArgParser
from .SmartPolygonDevices import SmartPolygonDevices
from .System import System
from .Robot import Robots
from .Mission import Mission
from Modules.Logic import Field


class Context:
    def __init__(self, init_ok: bool):
        self.init_ok = init_ok

        self.config = Config(self)
        self.lg = Logger(prefix="AGTS-ATS", write_to_file=True, in_dir=True, session=True)
        self.system = System(self)

        self.args = ArgParser(self)

        self.field = Field()
        self.robots = Robots(self)

        self.mission = Mission(self)

        self.spd = SmartPolygonDevices(self)


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

    def get(self, section: str, key: str):
        try:
            if self.config[section][key] is not None:
                try:
                    val = int(self.config[section][key])
                    if val == 0 or val == 1:
                        return bool(val)
                    else:
                        return val
                except:
                    try:
                        val = float(self.config[section][key])
                        return val
                    except:
                        return self.config[section][key]
            else:
                raise ValueError("Couldn't find '" + key + "' in '" + section + "'")
        except:
            raise ValueError("Couldn't find '" + key + "' in '" + section + "'")

    def set(self, section: str, key: str, value):
        self.config.set(section, key, value)
        config_file = open(os.path.dirname(os.path.abspath(__file__)) + "/../../config.ini", "w")
        self.config.write(config_file)
