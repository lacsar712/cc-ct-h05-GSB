from desk.tool_offset_swap import swap_enabled, swap_fields, swap_out_fields

def on_write(tool_code, offset_um):
    if not swap_enabled():
        return tool_code, offset_um
    return swap_fields(tool_code, offset_um)

def on_project(tool_code, offset_um):
    if not swap_enabled():
        return tool_code, offset_um
    return swap_out_fields(tool_code, offset_um)

