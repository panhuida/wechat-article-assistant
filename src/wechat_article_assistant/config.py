"""配置管理模块"""

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

__all__ = ["config", "Config", "BASE_DIR"]

# 加载环境变量
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Config:
    """应用配置类"""

    # Flask配置
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-please-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    PORT = int(os.getenv("FLASK_PORT", 5000))

    # 数据库配置
    DATABASE_URL = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'wechat_assistant.db'}"
    )

    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = BASE_DIR / os.getenv("LOG_DIR", "logs")

    # 下载配置
    # 优先使用 DOWNLOAD_PATH（绝对路径），如果没有则使用 DOWNLOAD_DIR（相对路径）
    _download_path = os.getenv("DOWNLOAD_PATH")
    if _download_path:
        DOWNLOAD_DIR = Path(_download_path)
    else:
        DOWNLOAD_DIR = BASE_DIR / os.getenv("DOWNLOAD_DIR", "data/downloads")

    # 微信公众平台配置
    WECHAT_MP_URL = os.getenv("WECHAT_MP_URL", "https://mp.weixin.qq.com")
    SESSION_FILE = BASE_DIR / os.getenv("SESSION_FILE", "data/wechat_session.json")

    # 登录方式配置
    # popup: 在Web应用中弹窗显示二维码（推荐，不启动可见浏览器）
    # browser: 启动Playwright浏览器窗口扫码登录
    LOGIN_MODE = os.getenv("LOGIN_MODE", "popup")

    # 确保目录存在
    @classmethod
    def init_app(cls) -> None:
        """初始化应用配置"""
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        cls.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        (BASE_DIR / "data").mkdir(parents=True, exist_ok=True)

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
