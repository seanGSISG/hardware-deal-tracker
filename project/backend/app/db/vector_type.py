"""Dialect-guarded embedding vector column type (feature-006, ADR-006).

The semantic-matching feature is OPTIONAL and must never become a hard
dependency. On Postgres the embedding column materialises as a real
``pgvector`` ``vector(N)`` column (the ``pgvector`` Python package is imported
**lazily**, only on the postgres dialect path, so neither the model imports nor
the in-memory sqlite test suite require pgvector to be installed). On every
other dialect — notably the in-memory sqlite test DB, which cannot load the
pgvector extension — the column degrades to a JSON-storable type so
``Base.metadata.create_all`` works and embeddings can still round-trip in tests.
"""
from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator, UserDefinedType


class EmbeddingVector(TypeDecorator):
    """A fixed-dimension embedding column that is pgvector on Postgres, JSON elsewhere.

    Stored/loaded values are plain ``list[float]`` on every dialect so service
    code (and tests) never has to care which backend is underneath.
    """

    # The Python-side representation is JSON-ish (a list of floats). We override
    # load_dialect_impl so the *DDL/transport* differs per dialect. none_as_null
    # keeps None -> SQL NULL (not the JSON string 'null') so IS NULL filters work.
    impl = JSON(none_as_null=True)
    cache_ok = True

    def __init__(self, dim: int, *args, **kwargs) -> None:
        self.dim = dim
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            # Lazy import: pgvector is only needed when actually running on
            # Postgres. Keeping it here means model imports and the sqlite test
            # suite never require the pgvector package.
            from pgvector.sqlalchemy import Vector

            return dialect.type_descriptor(Vector(self.dim))
        # sqlite / others: store the vector as JSON text. none_as_null=True so a
        # Python None becomes a real SQL NULL (not the JSON string 'null'),
        # keeping `embedding IS NULL` filters correct.
        return dialect.type_descriptor(JSON(none_as_null=True))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return list(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return list(value)


# Re-export for callers/migrations that want the raw pgvector DDL type. Importing
# this symbol must NOT trigger a pgvector import; it is resolved lazily.
__all__ = ["EmbeddingVector", "UserDefinedType"]
