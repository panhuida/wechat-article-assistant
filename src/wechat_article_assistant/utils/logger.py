"""日志工具"""

import logging
import sys
from logging.handlers import RotatingFileHandler

from ..config import config


def setup_logger(name: str, log_file: str | None = None, level: str | None = None) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件名（可选）
        level: 日志级别（可选）

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    log_level = getattr(logging, level or config.LOG_LEVEL)
    logger.setLevel(log_level)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_path = config.LOG_DIR / log_file
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 创建默认日志记录器
app_logger = setup_logger("app", "app.log")
collect_logger = setup_logger("collect", "collect.log")
download_logger = setup_logger("download", "download.log")
