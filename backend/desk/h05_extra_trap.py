"""写入/投影钩子：直通层。

刀号与刀补微米各归其列，整列对调已拆除；
保留本模块仅为兼容既有导入。
"""


def on_write(tool_code, offset_um):
    return tool_code, offset_um


def on_project(tool_code, offset_um):
    return tool_code, offset_um
