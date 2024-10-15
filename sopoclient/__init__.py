"""
A simple python wrapper for the HTTP for SOPO.

API key can be stored in the SOPO_API_KEY environment variable.
Host can be stored in the SOPO_HOST environment variable.
"""

from .core import Client

from . import collections
from . import product
from . import relationships