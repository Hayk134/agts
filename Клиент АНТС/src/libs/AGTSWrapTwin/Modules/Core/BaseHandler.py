from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Modules.Context.Context import Context


class BaseHandler(abc.ABC):
    def __init__(self, context: Context):
        self.context = context

    @abc.abstractmethod
    def run(self):
        pass
