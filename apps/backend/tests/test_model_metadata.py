from __future__ import annotations

from app import models  # noqa: F401
from app.db.base import Base


EXPECTED_TIMESTAMPED_TABLES = {
    "products",
    "comparators",
    "source_documents",
    "document_chunks",
    "citation_spans",
    "studies",
    "findings",
    "candidate_pods",
    "limitations",
    "recommendations",
    "calculation_runs",
    "expert_reviews",
}


def test_expected_tables_are_registered_in_metadata():
    assert EXPECTED_TIMESTAMPED_TABLES.issubset(Base.metadata.tables.keys())


def test_timestamp_columns_exist_on_new_domain_tables():
    for table_name in EXPECTED_TIMESTAMPED_TABLES:
        columns = Base.metadata.tables[table_name].columns

        assert "created_at" in columns
        assert "updated_at" in columns
