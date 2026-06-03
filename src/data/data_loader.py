"""Data loading abstractions.

Provides a thin abstraction over the physical storage format (parquet on
local disk or object storage) so that upstream feature/training code does
not depend on where or how the data is persisted. Connection details are
read from environment variables (see ``.env.example``); no credentials or
real data live in the repository.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Iterator, Optional, Sequence

import pandas as pd


class DataLoader(ABC):
    """Abstract data source.

    Implementations expose a uniform interface for reading user-level
    tables regardless of the underlying storage engine. This keeps the
    feature pipeline storage-agnostic and testable with in-memory mocks.
    """

    @abstractmethod
    def load(
        self,
        table: str,
        columns: Optional[Sequence[str]] = None,
        filters: Optional[list] = None,
    ) -> pd.DataFrame:
        """Load a table into a DataFrame.

        Args:
            table: Logical table name or relative path.
            columns: Optional column projection; ``None`` loads all columns.
            filters: Optional predicate pushdown filters in pyarrow format,
                e.g. ``[("dt", ">=", "2024-01-01")]``.

        Returns:
            The requested data as a pandas DataFrame.
        """
        raise NotImplementedError

    @abstractmethod
    def iter_batches(
        self,
        table: str,
        batch_size: int = 100_000,
        columns: Optional[Sequence[str]] = None,
    ) -> Iterator[pd.DataFrame]:
        """Stream a table in row-group batches for out-of-core processing.

        Args:
            table: Logical table name or relative path.
            batch_size: Approximate number of rows per yielded batch.
            columns: Optional column projection.

        Yields:
            DataFrame chunks of roughly ``batch_size`` rows.
        """
        raise NotImplementedError


class ParquetDataLoader(DataLoader):
    """Parquet-backed loader using pyarrow.

    Reads parquet datasets from a configurable root directory. The root is
    resolved from the ``DATA_ROOT`` environment variable, falling back to
    the local ``data/`` directory. Real data files are git-ignored.
    """

    def __init__(self, root: Optional[str] = None) -> None:
        """Initialize the loader.

        Args:
            root: Dataset root directory. Defaults to ``$DATA_ROOT`` or
                the repository-local ``data/`` directory.
        """
        self.root = root or os.getenv("DATA_ROOT", "data")

    def _resolve(self, table: str) -> str:
        """Resolve a logical table name to a filesystem path."""
        raise NotImplementedError

    def load(
        self,
        table: str,
        columns: Optional[Sequence[str]] = None,
        filters: Optional[list] = None,
    ) -> pd.DataFrame:
        raise NotImplementedError

    def iter_batches(
        self,
        table: str,
        batch_size: int = 100_000,
        columns: Optional[Sequence[str]] = None,
    ) -> Iterator[pd.DataFrame]:
        raise NotImplementedError
