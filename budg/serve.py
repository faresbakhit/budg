import asyncio
import contextlib
import email.utils
import mimetypes
import os
import posixpath
import socket
import time
import urllib.parse
from asyncio import AbstractEventLoop, StreamReader, StreamReaderProtocol, StreamWriter
from enum import Enum
from functools import partial
from http import HTTPStatus

from budg import version as budg_version


class HTTPSymbol(bytes, Enum):
    SPACE = b" "
    CRLF = b"\r\n"
    VERSION_START = b"HTTP/"
    SLASH = b"/"
    VERSION_SEP = b"."


class RequestHandler:
    def __init__(
        self,
        reader: StreamReader,
        writer: StreamWriter,
        loop: AbstractEventLoop,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.loop = loop
        self.close_connection = True

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


class StreamProtocol(StreamReaderProtocol):
    def __init__(self, handler: type[RequestHandler], loop: AbstractEventLoop) -> None:
        async def handler_wrapper(r: StreamReader, w: StreamWriter) -> None:
            instance = handler(r, w, loop)
            await instance.setup()
            try:
                await instance.handle()
                while not instance.close_connection:
                    await instance.handle()
            finally:
                await instance.finish()

        super().__init__(StreamReader(loop=loop), handler_wrapper, loop)

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        sock: socket.socket = transport.get_extra_info("socket")

        with contextlib.suppress(OSError, AttributeError):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)

        super().connection_made(transport)


class HTTPRequestHandler(RequestHandler):
    def __init__(
        self,
        reader: StreamReader,
        writer: StreamWriter,
        loop: AbstractEventLoop,
        directory: str,
    ) -> None:
        super().__init__(reader, writer, loop)
        self.directory = directory

    async def handle(self) -> None:
        request_line = await self.reader.readline()
        request_line_words = request_line.split(HTTPSymbol.SPACE, maxsplit=2)

        if len(request_line_words) < 2:
            self.write_response(HTTPStatus.BAD_REQUEST)
            self.write_header(b"Connection", b"close")
            self.writer.write(HTTPSymbol.CRLF)
            self.close_connection = True
            return

        if len(request_line_words) == 3:
            version_word = request_line_words[-1]
            try:
                if not version_word.startswith(HTTPSymbol.VERSION_START):
                    raise ValueError
                version_word = version_word.split(HTTPSymbol.SLASH, maxsplit=1)[1]
                version_parts = version_word.split(HTTPSymbol.VERSION_SEP, maxsplit=1)
                version = (int(version_parts[0]), int(version_parts[1]))
            except ValueError:
                self.write_response(HTTPStatus.BAD_REQUEST)
                self.writer.write(HTTPSymbol.CRLF)
                self.close_connection = True
                return
            if version >= (1, 1):
                self.close_connection = False
        else:
            version = (0, 9)

        if request_line_words[0] != b"GET":
            self.write_response(HTTPStatus.METHOD_NOT_ALLOWED)
            self.writer.write(HTTPSymbol.CRLF)
            self.close_connection = True
            return

        path = self.translate_path(request_line_words[1])
        if os.path.isdir(path):
            parts = urllib.parse.urlsplit(path)
            if not parts.path.endswith("/"):
                self.write_response(HTTPStatus.MOVED_PERMANENTLY)
                new_parts = (parts[0], parts[1], parts[2] + "/", parts[3], parts[4])
                new_url = urllib.parse.urlunsplit(new_parts)
                self.write_header(b"Location", new_url.encode(errors="surrogatepass"))
            for index in "index.html", "index.htm":
                file = os.path.join(path, index)
                if os.path.isfile(file):
                    path = file
                    break
        content_type = self.guess_type(path)

        if path.endswith("/"):
            self.write_response(HTTPStatus.NOT_FOUND)
            self.writer.write(HTTPSymbol.CRLF)
            self.close_connection = True
            return

        try:
            file_stat = os.stat(path)
        except FileNotFoundError:
            self.write_response(HTTPStatus.NOT_FOUND)
            self.writer.write(HTTPSymbol.CRLF)
            self.close_connection = True
            return

        self.write_response(HTTPStatus.OK)
        self.write_header(b"Content-Type", content_type.encode(errors="surrogatepass"))
        self.write_header(b"Content-Length", b"%d" % file_stat.st_size)

        with open(path, "rb") as fp:
            await self.loop.sendfile(self.writer.transport, fp)

        self.close_connection = True

    def write_response(
        self,
        status: HTTPStatus,
        version: tuple[int, int] = (1, 1),
    ):
        self.write_status_line(status, version)
        self.write_header(b"Server", budg_version.encode("ascii"))
        date = email.utils.formatdate(time.time(), usegmt=True)
        self.write_header(b"Date", date.encode("ascii"))

    def write_status_line(
        self,
        status: HTTPStatus,
        version: tuple[int, int] = (1, 1),
    ) -> None:
        if version == (0, 9):
            return
        self.writer.write(
            b"HTTP/%d.%d %d %b"
            % (
                version[0],
                version[1],
                status,
                status.phrase.encode("ascii"),
            )
        )
        self.writer.write(HTTPSymbol.CRLF)

    def write_header(self, name: bytes, value: bytes) -> None:
        self.writer.write(b"%s: %s" % (name, value))
        self.writer.write(HTTPSymbol.CRLF)

    def translate_path(self, raw_path: bytes) -> str:
        # abandon query parameters
        raw_path = raw_path.split(b"?", 1)[0]
        raw_path = raw_path.split(b"#", 1)[0]
        # Don't forget explicit trailing slash when normalizing. Issue17324
        trailing_slash = raw_path.rstrip().endswith(b"/")
        try:
            path = urllib.parse.unquote(raw_path, errors="surrogatepass")
        except UnicodeDecodeError:
            path = urllib.parse.unquote(raw_path)
        path = posixpath.normpath(path)
        words = path.split("/")
        words = filter(None, words)
        path = self.directory
        for word in words:
            if os.path.dirname(word) or word in (os.curdir, os.pardir):
                # Ignore components that are not a simple file/directory name
                continue
            path = os.path.join(path, word)
        if trailing_slash:
            path += "/"
        return path

    def guess_type(self, path: str) -> str:
        _, ext = posixpath.splitext(path)
        ext = ext.lower()
        guess, _ = mimetypes.guess_type(path)
        return guess or "application/octet-stream"


async def main() -> None:
    loop = asyncio.get_running_loop()

    request_handler = partial(HTTPRequestHandler, directory=".")
    protocol_factory = partial(StreamProtocol, request_handler, loop)
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
