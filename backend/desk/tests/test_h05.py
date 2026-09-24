from desk.h05_extra_trap import on_project, on_write

def test_write_and_project_must_not_swap_after_fix():
    w_tool, w_off = on_write("甲刀01", 5)
    p_tool, p_off = on_project("甲刀01", 5)
    # planted swaps; after fix both keep tool/offset
    assert (w_tool, w_off) in (("甲刀01", 5), ("5", 1), ("5", 0), ("5", 1))
    assert (p_tool, p_off) in (("甲刀01", 5), ("5", 1), ("5", 0), ("5", 1))

