"""HTTP clients with rotating user agents and retry support."""

from __future__ import annotations

import asyncio
import ssl
from typing import Any

import aiohttp
import certifi
import requests
from fake_useragent import UserAgent

from config.settings import get_settings
from utils.retry import async_retry, sync_retry


class SyncHTTPClient:
    """Synchronous HTTP client for scrapers."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._ua = UserAgent(fallback="Mozilla/5.0 (compatible; ViralScopeBot/1.0)")

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "User-Agent": self._ua.random,
            "Accept": "text/html,application/json,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if extra:
            headers.update(extra)
        return headers

    @sync_retry(exceptions=(requests.RequestException,))
    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        response = requests.get(
            url,
            params=params,
            headers=self._headers(headers),
            timeout=self.settings.scraping.request_timeout,
            verify=certifi.where(),
        )
        response.raise_for_status()
        return response

    @sync_retry(exceptions=(requests.RequestException,))
    def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        response = self.get(url, params=params, headers=headers)
        return response.json()


class AsyncHTTPClient:
    """Async HTTP client for concurrent scraping."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._ua = UserAgent(fallback="Mozilla/5.0 (compatible; ViralScopeBot/1.0)")
        self._session: aiohttp.ClientSession | None = None

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "User-Agent": self._ua.random,
            "Accept": "text/html,application/json,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if extra:
            headers.update(extra)
        return headers

    async def __aenter__(self) -> AsyncHTTPClient:
        timeout = aiohttp.ClientTimeout(
            total=self.settings.scraping.request_timeout
        )
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    @async_retry(exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        if not self._session:
            raise RuntimeError("AsyncHTTPClient must be used as async context manager")

        async with self._session.get(
            url, params=params, headers=self._headers(headers)
        ) as response:
            response.raise_for_status()
            return await response.text()

    @async_retry(exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        if not self._session:
            raise RuntimeError("AsyncHTTPClient must be used as async context manager")

        async with self._session.get(
            url, params=params, headers=self._headers(headers)
        ) as response:
            response.raise_for_status()
            return await response.json()
