import asyncio
from asgiref.sync import async_to_sync

from django.conf import settings
from pypi_simple.parse_stream import parse_links_stream
from pulpcore.plugin.download import HttpDownloader, DownloadResult, DownloaderFactory
from .utils import write_simple_detail


class SimpleDownloader(HttpDownloader):
    """Class to assist with downloading simple api pages."""

    def __init__(self, url, base_path, project_name, **kwargs):
        """Init the class"""
        self.base_path = base_path
        origin = settings.CONTENT_ORIGIN.strip("/")
        prefix = settings.CONTENT_PATH_PREFIX.strip("/")
        base_path = base_path.strip("/")
        self.content = "/".join((origin, prefix, base_path))
        self.project_name = project_name

        super().__init__(url, **kwargs)

    def iter_over_async(self, ait, loop=None):
        ait = ait.__aiter__()

        async def get_next():
            try:
                obj = await ait.__anext__()
                return False, obj
            except StopAsyncIteration:
                return True, None

        gen_next = async_to_sync(get_next(), True)
        while True:
            done, obj = gen_next()
            if done:
                break
            yield obj

    @async_to_sync
    async def _stream_data(self, response):
        """Stream the read data."""
        while True:
            chunk = await response.content.read(1048576)
            if not chunk:
                break
            yield chunk

    async def _handle_response(self, response):
        """
        Handle the aiohttp response by writing it to disk and calculating digests

        Args:
            response (aiohttp.ClientResponse): The response to handle.

        Returns:
             DownloadResult: Contains information about the result. See the DownloadResult docs for
                 more information.
        """
        if self.headers_ready_callback:
            await self.headers_ready_callback(response.headers)

        # stream = (d async for d in self._stream_data(response))
        # loop = asyncio.new_event_loop()
        stream = self.iter_over_async(response.content.iter_chunked(1048576))
        # stream = self._stream_data(response)
        links = parse_links_stream(stream, response.url.path, response.get_encoding())
        packages = ((l.text, f'{self.content}{l.text}', l.url.split("#sha256=")[1]) for l in links)
        processed = write_simple_detail(self.project_name, packages, streamed=True)
        for data in processed:
            await self.handle_data(data.encode('utf-8'))
        self.finalize()

        return DownloadResult(
            path=self.path,
            artifact_attributes=self.artifact_attributes,
            url=self.url,
            headers=response.headers,
        )
