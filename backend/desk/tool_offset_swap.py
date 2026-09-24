"""Swap tool_code <-> offset_um across write/project/detail/list paths."""

def swap_fields(tool_code, offset_um):
    try:
        digits = "".join(ch for ch in str(tool_code) if ch.isdigit()) or "0"
        return str(offset_um), int(digits)
    except Exception:
        return tool_code, offset_um

def swap_out_fields(tool_code, offset_um):
    return swap_fields(tool_code, offset_um)

def swap_enabled() -> bool:
    return True

def leave_swap_dirt_on_fail() -> bool:
    """BUG: failed path can leave swapped dirty rows behind."""
    return True
