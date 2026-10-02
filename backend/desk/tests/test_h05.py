from desk.h05_extra_trap import on_project, on_write
from desk.tool_offset_swap import (
    leave_swap_dirt_on_fail,
    swap_enabled,
    swap_fields,
    swap_out_fields,
)

# 甲刀 5 微米、乙刀 24 微米：四面（写入/投影/列表/详情）读出都必须各归其列
CASES = [
    ("甲刀01", 5),
    ("乙刀02", 24),
    ("T01", 5),
    ("T09", 20),
]


def test_write_and_project_must_not_swap_after_fix():
    for tool_code, offset_um in CASES:
        assert on_write(tool_code, offset_um) == (tool_code, offset_um)
        assert on_project(tool_code, offset_um) == (tool_code, offset_um)


def test_swap_module_is_dismantled():
    assert swap_enabled() is False
    assert leave_swap_dirt_on_fail() is False
    for tool_code, offset_um in CASES:
        assert swap_fields(tool_code, offset_um) == (tool_code, offset_um)
        assert swap_out_fields(tool_code, offset_um) == (tool_code, offset_um)
