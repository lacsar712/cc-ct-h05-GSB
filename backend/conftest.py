import os

import django


def pytest_configure(config):
    # 裸 pytest 也能跑：未显式指定 settings 时用内存 sqlite 测试配置
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_test")
    django.setup()
