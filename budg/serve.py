import asyncio
import contextlib
import http.server
import socket
from asyncio import AbstractEventLoop, StreamReader, StreamWriter
from collections.abc import Callable
from http import HTTPStatus
from typing import Generic, ParamSpec, TypeVar

_P = ParamSpec("_P")
_T_Protocol = TypeVar("_T_Protocol", bound=asyncio.BaseProtocol)


class StreamRequestHandler:
    def __init__(self, reader: StreamReader, writer: StreamWriter) -> None:
        self.reader = reader
        self.writer = writer

    async def setup(self) -> None:
        pass

    async def handle(self) -> None:
        pass

    async def finish(self) -> None:
        await self.writer.drain()
        if self.writer.can_write_eof():
            self.writer.write_eof()
        self.writer.close()
        await self.writer.wait_closed()


class BaseHTTPRequestHandler(StreamRequestHandler):
    def __init__(self, reader: StreamReader, writer: StreamWriter) -> None:
        super().__init__(reader, writer)
        self.close_connection = False

    async def handle(self) -> None:
        self.close_connection = True

        await self.handle_one_request()
        while not self.close_connection:
            await self.handle_one_request()

    async def handle_one_request(self) -> None:
        try:
            await self.reader.readline()
        except ValueError:
            ...


class StreamProtcool(asyncio.streams.FlowControlMixin, asyncio.Protocol):
    def __init__(
        self,
        handler: type[StreamRequestHandler],
        loop: AbstractEventLoop,
    ) -> None:
        super().__init__(loop)
        self.handler = handler
        self.loop = loop
        self.reader = StreamReader(4, loop=self.loop)
        self.close_waiter = loop.create_future()

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        sock: socket.socket = transport.get_extra_info("socket")

        with contextlib.suppress(OSError, AttributeError):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)

        self.reader.set_transport(transport)

        assert isinstance(transport, asyncio.WriteTransport)
        writer = StreamWriter(transport, self, self.reader, self.loop)

        self.loop.create_task(self.handle_connection(writer))

    def data_received(self, data: bytes) -> None:
        self.reader.feed_data(data)

    def eof_received(self) -> bool:
        self.reader.feed_eof()
        return True

    def connection_lost(self, exc: Exception | None) -> None:
        if exc is None:
            self.reader.feed_eof()
        else:
            self.reader.set_exception(exc)
        if not self.close_waiter.done():
            if exc is None:
                self.close_waiter.set_result(None)
            else:
                self.close_waiter.set_exception(exc)
        super().connection_lost(exc)

    async def handle_connection(self, writer: StreamWriter) -> None:
        handler = self.handler(self.reader, writer)
        await handler.setup()
        try:
            await handler.handle()
        finally:
            await handler.finish()

    def _get_close_waiter(self, _: StreamWriter) -> asyncio.Future[None]:
        return self.close_waiter


class ProtocolFactory(Generic[_P, _T_Protocol]):
    def __init__(
        self,
        factory: Callable[_P, _T_Protocol],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> None:
        self.factory = factory
        self.args = args
        self.kwargs = kwargs

    def __call__(self) -> _T_Protocol:
        return self.factory(*self.args, **self.kwargs)


async def main() -> None:
    loop = asyncio.get_running_loop()

    protocol_factory = ProtocolFactory(StreamProtcool, BaseHTTPRequestHandler, loop)
    server = await loop.create_server(protocol_factory, "::", 3000)

    async with server as httpd:
        for sock in httpd.sockets:
            host, port = sock.getsockname()[:2]
            url_host = f"[{host}]" if ":" in host else host
            print(
                f"Serving HTTP on {host} port {port} "
                f"(http://{url_host}:{port}/) ..."
            )

        with contextlib.suppress(asyncio.CancelledError):
            await httpd.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
