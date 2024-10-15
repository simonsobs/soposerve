"""
Core client object for interacting with the SOPO API.
"""

import httpx
from rich.console import Console

console = Console()


class Client(httpx.Client):
    """
    The core client for the SOPO API. A wrapper around httpx.Client,
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
            The API key for the SOPO API to use.

        host: str
            The host for the SOPO API to use.

        verbose: bool
            Whether to print verbose output.
        """

        self.verbose = verbose
        super().__init__(base_url=host, headers={"X-API-Key": api_key})
