"""刀号 <-> 刀补微米 整列对调陷阱已拆除。

保留本模块仅为兼容既有导入；所有函数均为恒等/关闭状态。
任何路径（写入、投影、详情、列表、失败回退）都不得再交换
tool_code 与 offset_um：刀号格只放刀号，刀补格只放微米。
"""


def swap_fields(tool_code, offset_um):
    """恒等返回，不再对调字段。"""
    return tool_code, offset_um


def swap_out_fields(tool_code, offset_um):
    """恒等返回，不再对调字段。"""
    return tool_code, offset_um


def swap_enabled() -> bool:
    return False


def leave_swap_dirt_on_fail() -> bool:
    """失败路径不得残留错位脏行。"""
    return False
