from __future__ import annotations

import pytest
import sqlglot as sg

import ibis
import ibis.common.exceptions as com
from ibis import _
from ibis.backends.sql.dialects import Trino


def test_first_last_with_order_by_in_window_raises():
    # GH #11812: `order_by` passed to `first`/`last` was silently dropped by
    # the `first_to_firstvalue` rewrite when used inside a window function,
    # producing a query with no ORDER BY instead of an explicit error.
    t = ibis.table({"a": "int64", "b": "int64", "i": "int64"}, name="t")
    expr = t.mutate(d=t.b.first(order_by=t.i).over(group_by=t.a))
    with pytest.raises(com.UnsupportedOperationError, match="order_by"):
        ibis.to_sql(expr)


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
