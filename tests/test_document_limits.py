"""Somente números/buffers inventados; nenhum PDF ou imagem de corpus."""
from array import array
from dataclasses import replace

import pytest

from ecowatt.document_limits import RasterBudget, RasterLimitError, RasterPolicy


def rejected(code, call):
    with pytest.raises(RasterLimitError) as error:
        call()
    assert error.value.code == code
    assert str(error.value) == code


@pytest.mark.parametrize("value", [None, True, 0, -1, 11, 1.0, "1"])
def test_page_count_is_known_strict_and_bounded(value):
    rejected("invalid_page_count", lambda: RasterBudget(value))


@pytest.mark.parametrize("field", RasterPolicy.__dataclass_fields__)
@pytest.mark.parametrize("value", [None, False, 0, -1, 1.0, "1"])
def test_invalid_policy_cannot_silently_disable_limits(field, value):
    rejected("invalid_raster_policy", lambda: RasterPolicy(**{field: value}))


@pytest.mark.parametrize("changes", [
    {"page": 0}, {"page": 3}, {"page": True}, {"width": 0}, {"height": -1},
    {"width": "10"}, {"width": 1.0}, {"channels": True}, {"channels": 2},
    {"stride": True}, {"stride": 29},
])
def test_bad_requests_never_consume_budget(changes):
    budget = RasterBudget(2)
    request = dict(page=1, width=10, height=10, channels=3)
    request.update(changes)
    rejected("invalid_raster_request", lambda: budget.reserve(**request))
    assert budget.usage == {"pixels": 0, "bytes": 0, "renders": 0}


def test_side_limit_checked_without_allocating_and_includes_boundary():
    budget = RasterBudget(1)
    budget.reserve(page=1, width=10_000, height=1)
    before = budget.usage
    rejected("raster_side_limit", lambda: budget.reserve(page=1, width=10**100, height=1))
    assert budget.usage == before


def test_page_regions_and_retries_share_inclusive_pixel_budget():
    budget = RasterBudget(2)
    for _ in range(2):
        budget.reserve(page=1, width=4_000, height=2_500)
    before = budget.usage
    rejected("raster_page_pixel_limit", lambda: budget.reserve(page=1, width=1, height=1))
    assert budget.usage == before
    budget.reserve(page=2, width=1, height=1)


def test_document_pixel_budget_is_cumulative_across_pages():
    budget = RasterBudget(10)
    for page in range(1, 4):
        budget.reserve(page=page, width=4_000, height=5_000)
    rejected("raster_document_pixel_limit", lambda: budget.reserve(page=4, width=1, height=1))
    assert budget.usage["pixels"] == 60_000_000


def test_padding_channels_and_failed_output_do_not_refund_byte_budget():
    budget = RasterBudget(1, replace(RasterPolicy(), max_document_bytes=24))
    first = budget.reserve(page=1, width=2, height=2, channels=4, stride=12)
    rejected("raster_output_mismatch", lambda: first.verify(
        width=2, height=2, channels=4, stride=12, buffer=b""))
    rejected("raster_document_byte_limit", lambda: budget.reserve(page=1, width=1, height=1))
    assert budget.usage == {"pixels": 4, "bytes": 24, "renders": 1}


def test_regions_cannot_exhaust_work_with_tiny_repeated_renders():
    budget = RasterBudget(1)
    for _ in range(32):
        budget.reserve(page=1, width=1, height=1)
    rejected("raster_render_limit", lambda: budget.reserve(page=1, width=1, height=1))
    assert budget.usage["renders"] == 32


@pytest.mark.parametrize("buffer", [b"\0" * 12, bytearray(12), memoryview(array("I", [0, 0, 0]))])
def test_output_uses_nbytes_without_copying(buffer):
    allocation = RasterBudget(1).reserve(page=1, width=2, height=2)
    allocation.verify(width=2, height=2, channels=3, stride=6, buffer=buffer)


@pytest.mark.parametrize("changes", [
    {"width": 3}, {"height": True}, {"channels": 4}, {"stride": 7},
    {"buffer": b"\0" * 11}, {"buffer": b"\0" * 13}, {"buffer": "x" * 12},
    {"buffer": memoryview(bytes(24))[::2]},
])
def test_renderer_mismatch_or_noncontiguous_output_is_rejected(changes):
    allocation = RasterBudget(1).reserve(page=1, width=2, height=2)
    actual = dict(width=2, height=2, channels=3, stride=6, buffer=bytes(12))
    actual.update(changes)
    rejected("raster_output_mismatch", lambda: allocation.verify(**actual))


def test_released_buffer_is_rejected():
    view = memoryview(bytes(3))
    view.release()
    allocation = RasterBudget(1).reserve(page=1, width=1, height=1)
    rejected("raster_output_mismatch", lambda: allocation.verify(
        width=1, height=1, channels=3, stride=3, buffer=view))
