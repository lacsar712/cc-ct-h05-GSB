"""测试专用配置：用内存 sqlite 建库，不依赖 PostgreSQL。"""

from .settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
