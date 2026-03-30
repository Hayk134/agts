from dataclasses import dataclass, field


@dataclass
class ControlSPD:
    d_id: int
    address: str
    port: str
    color: int = 0
    glitch: bool = False
    is_alive: bool = True


@dataclass
class CleaningSPD:
    d_id: int
    address: str
    port: str
    color: int = 0
    glitch: bool = False
    is_alive: bool = True


@dataclass
class PipeSPD:
    d_id: int
    address: str
    port: str
    color: list[int] = field(default_factory=lambda: [0 for _ in range(4)])
    twin_color: list[int] = field(default_factory=lambda: [0 for _ in range(4)])
    pipes_glitch: list[int] = field(default_factory=lambda: [0 for _ in range(4)])
    barrel_glitch: bool = False
    is_alive: bool = True


@dataclass
class RemoteSPD:
    d_id: int
    address: str
    port: str
    color: list[int] = field(default_factory=lambda: [0 for _ in range(20)])
    is_alive: bool = True


class SmartPolygonDevices:
    def __init__(self, context):
        self.context = context

        self.controls = [
            ControlSPD(
                0,
                "127.0.0.1" if self.context.args.get_arg("twin") else "192.168.60.131",
                "5031" if self.context.args.get_arg("twin") else "4031",
            ),
            ControlSPD(
                1,
                "127.0.0.1" if self.context.args.get_arg("twin") else "192.168.60.132",
                "5032" if self.context.args.get_arg("twin") else "4031",
            ),
            ControlSPD(
                2,
                "127.0.0.1" if self.context.args.get_arg("twin") else "192.168.60.133",
                "5033" if self.context.args.get_arg("twin") else "4031",
            ),
        ]

        self.cleaning = CleaningSPD(
            3,
            "127.0.0.1" if self.context.args.get_arg("twin") else "192.168.60.141",
            "5041" if self.context.args.get_arg("twin") else "4041",
        )

        self.pipes = PipeSPD(
            4,
            "127.0.0.1" if self.context.args.get_arg("twin") else "192.168.60.151",
            "5051" if self.context.args.get_arg("twin") else "4051",
        )

        self.remote = RemoteSPD(
            5,
            "127.0.0.1" if self.context.args.get_arg("twin") else "192.168.60.161",
            "5061" if self.context.args.get_arg("twin") else "4061",
        )
