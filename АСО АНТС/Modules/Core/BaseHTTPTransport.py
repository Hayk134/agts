from __future__ import annotations

import abc
from typing import TYPE_CHECKING

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .BaseHandler import BaseHandler

if TYPE_CHECKING:
    from Modules.Context.Context import Context


class BaseHttpTransport(BaseHandler):
    def __init__(self, context: Context, port_label: str) -> None:
        super().__init__(context)

        self.port_label = port_label
        self.api = FastAPI()
        origins = ["*"]
        self.api.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.make_routes()

    @abc.abstractmethod
    def make_routes(self):
        pass

    def run(self):
        self.context.lg.init(
            f"Адрес сервера ({self.port_label}): http://127.0.0.1:{self.context.config.get('fastapi:ports', self.port_label)}"
        )

        if int(self.context.config.get("fastapi", "verbose_output")) == 1:
            uvicorn.run(self.api, host="0.0.0.0", port=self.context.config.get("fastapi:ports", self.port_label))
        else:
            uvicorn.run(
                self.api,
                host="0.0.0.0",
                port=self.context.config.get("fastapi:ports", self.port_label),
                log_level="critical",
            )
