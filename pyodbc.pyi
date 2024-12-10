"""
Type stubs for pyodbc module providing SQL Server database connectivity.
"""

from typing import Any


class Error(Exception):
    """Base class for all pyodbc errors."""


class Connection:
    """Represents a connection to the database."""

    def close(self) -> None:
        """Closes the connection."""

    def commit(self) -> None:
        """Commits current transaction."""

    def cursor(self) -> Any:
        """Creates a new Cursor object."""


def connect(connection_string: str) -> Connection:
    """Creates a database connection."""
