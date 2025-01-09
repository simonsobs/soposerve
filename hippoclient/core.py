"""
Core client object for interacting with the hippo API.
"""

import httpx
from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from rich.console import Console

from .caching import Cache, MultiCache

console = Console()


class Client(httpx.Client):
    """
    The core client for the hippo API. A wrapper around httpx.Client,
    including the settings management required for interacting using
    the API-key based interface.
    """

    verbose: bool

    def __init__(
        self,
        api_key: str,
        host: str,
        verbose: bool = False,
    ):
        """
        Parameters
        ----------

        api_key: str
            The API key for the hippo API to use.

        host: str
            The host for the hippo API to use.

        verbose: bool
            Whether to print verbose output.
        """

        self.verbose = verbose
        super().__init__(base_url=host, headers={"X-API-Key": api_key})


class ClientSettings(BaseSettings):
    """
    Main settings for the hippo API client. Used to configure:

    1. API access (key and host)
    2. Caching (path to cache(s))
    3. Verbosity.
    """

    api_key: str
    host: str
    verbose: bool = False

    caches: list[Cache] = []

    model_config = SettingsConfigDict(
        json_file=("config.json", "~/.hippo.conf"), env_prefix="hippo_"
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: BaseSettings,
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            dotenv_settings,
            env_settings,
            JsonConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

    @property
    def cache(self) -> MultiCache:
        """
        Return a MultiCache object for the caches.
        """
        return MultiCache(caches=self.caches)

    @property
    def client(self) -> Client:
        """
        Return a Client object for the API.
        """
        return Client(api_key=self.api_key, host=self.host, verbose=self.verbose)
