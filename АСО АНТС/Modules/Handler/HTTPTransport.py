from fastapi import Request

from Modules import BaseHttpTransport


class HttpTransport(BaseHttpTransport):
    def __init__(self, context):
        super().__init__(context, "sample_http")

    def make_routes(self):
        @self.api.post("/api/v1/")
        async def endpoint_label(data: Request):
            data = await data.json()
            return {"status": "OK"}
