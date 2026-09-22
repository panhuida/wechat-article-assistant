"""配置管理模块"""

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy.engine import make_url

__all__ = ["config", "Config", "BASE_DIR"]

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# 显式配置优先；源码运行兼容原目录，安装包默认使用用户数据目录。
_default_home = (
    BASE_DIR
    if (BASE_DIR / "pyproject.toml").is_file()
    else Path.home() / ".wechat-article-assistant"
)
APP_HOME = Path(os.getenv("WECHAT_ASSISTANT_HOME", str(_default_home))).expanduser().resolve()
load_dotenv(APP_HOME / ".env")


def resolve_data_path(value: str) -> Path:
    """将相对数据路径固定到应用目录，不依赖调用方工作目录。"""
    path = Path(value).expanduser()
    return (path if path.is_absolute() else APP_HOME / path).resolve()


def resolve_database_url(value: str) -> str:
    """固定 SQLite 文件位置，保留内存数据库和其他数据库连接。"""
    url = make_url(value)
    if url.get_backend_name() == "sqlite" and url.database not in (None, "", ":memory:"):
        url = url.set(database=str(resolve_data_path(url.database)))
    return url.render_as_string(hide_password=False)


class Config:
    """应用配置类"""

    # Flask配置
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-please-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    PORT = int(os.getenv("FLASK_PORT", 5000))

    # 数据库配置
    APP_HOME = APP_HOME
    DATABASE_URL = resolve_database_url(
        os.getenv("DATABASE_URL", "sqlite:///data/wechat_assistant.db")
    )

    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = resolve_data_path(os.getenv("LOG_DIR", "logs"))

    # 下载配置
    # 优先使用 DOWNLOAD_PATH（绝对路径），如果没有则使用 DOWNLOAD_DIR（相对路径）
    _download_path = os.getenv("DOWNLOAD_PATH")
    if _download_path:
        DOWNLOAD_DIR = resolve_data_path(_download_path)
    else:
        DOWNLOAD_DIR = resolve_data_path(os.getenv("DOWNLOAD_DIR", "data/downloads"))

    # 微信公众平台配置
    WECHAT_MP_URL = os.getenv("WECHAT_MP_URL", "https://mp.weixin.qq.com")
    SESSION_FILE = resolve_data_path(os.getenv("SESSION_FILE", "data/wechat_session.json"))

    # 登录方式配置
    # popup: 在Web应用中弹窗显示二维码（推荐，不启动可见浏览器）
    # browser: 启动Playwright浏览器窗口扫码登录
    LOGIN_MODE = os.getenv("LOGIN_MODE", "popup")

    # 每日摘要自动化配置
    DAILY_DIGEST_OUTPUT_DIR = Path(os.getenv("DAILY_DIGEST_OUTPUT_DIR", "/home/pan/文摘/公众号"))
    DAILY_DIGEST_EMAIL_TO = os.getenv("DAILY_DIGEST_EMAIL_TO", "panhuida@qq.com")
    DAILY_DIGEST_CODEX_MODEL = os.getenv("DAILY_DIGEST_CODEX_MODEL", "gpt-5.4")
    DAILY_DIGEST_SMTP_USER = os.getenv("DAILY_DIGEST_SMTP_USER", "")
    DAILY_DIGEST_SMTP_PASSWORD = os.getenv("DAILY_DIGEST_SMTP_PASSWORD", "")
    DAILY_DIGEST_SMTP_HOST = os.getenv("DAILY_DIGEST_SMTP_HOST", "")

    # 确保目录存在
    @classmethod
    def init_app(cls) -> None:
        """初始化应用配置"""
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        cls.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.DAILY_DIGEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (APP_HOME / "data").mkdir(parents=True, exist_ok=True)

    @classmethod
    def apply_overrides(cls, overrides: Mapping[str, Any] | None) -> None:
        """应用运行时配置覆盖，供测试和应用工厂使用"""
        if not overrides:
            return

        path_keys = {"LOG_DIR", "DOWNLOAD_DIR", "SESSION_FILE"}

        for key, value in overrides.items():
            if key in path_keys and value is not None:
                setattr(cls, key, Path(value))
                continue
            setattr(cls, key, value)


# 配置实例
config = Config()
