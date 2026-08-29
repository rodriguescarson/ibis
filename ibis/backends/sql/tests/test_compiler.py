from __future__ import annotations

import pytest
import sqlglot as sg

import ibis
from ibis import _
from ibis.backends.sql.dialects import Trino


def test_window_with_row_number_compiles():
    # GH #8058: the add_order_by_to_empty_ranking_window_functions rule was
    # matching on `RankBase` subclasses with a pattern expecting an `arg`
    # attribute, which is not present on `RowNumber`
    expr = (
        ibis.memtable({"a": range(30)})
        .mutate(id=ibis.row_number())
        .sample(fraction=0.25, seed=0)
        .mutate(is_test=_.id.isin(_.id))
        .filter(~_.is_test)
    )
    assert ibis.to_sql(expr)


def test_transpile_join():
    (result,) = sg.transpile(
        "SELECT * FROM t1 JOIN t2 ON x = y", read="duckdb", write=Trino
    )
    assert "CROSS JOIN" not in result


@pytest.mark.parametrize("dialect", ["trino", "athena"])
def test_trino_cast_string_to_json_parses(dialect):
    # GH #12073: CAST(varchar AS JSON) treats the string as a literal JSON
    # string value instead of parsing it, so the compiler must emit
    # JSON_PARSE for a string -> json cast.
    t = ibis.table({"raw": "string"}, name="t")
    sql = ibis.to_sql(t.raw.cast("json"), dialect=dialect)
    assert "JSON_PARSE" in sql
    assert "CAST(" not in sql
