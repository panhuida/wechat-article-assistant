"""配置管理模块"""

import os
from pathlib import Path

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

    # 确保目录存在
    @classmethod
    def init_app(cls) -> None:
        """初始化应用配置"""
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        cls.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        (BASE_DIR / "data").mkdir(parents=True, exist_ok=True)


# 配置实例
config = Config()
