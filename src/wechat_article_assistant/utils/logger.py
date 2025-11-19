"""日志工具"""

import logging
import sys
from logging.handlers import RotatingFileHandler

from ..config import config


class RelativePathFormatter(logging.Formatter):
    """自定义格式化器，移除模块路径前缀"""

    def format(self, record):
        # 移除 wechat_article_assistant. 前缀
        if record.name.startswith("wechat_article_assistant."):
            record.name = record.name.replace("wechat_article_assistant.", "", 1)
        return super().format(record)


def get_module_logger(module_name: str) -> logging.Logger:
    """
    获取模块专用的logger

    Args:
        module_name: 模块名称（通常使用 __name__）

    Returns:
        配置好的logger
    """
    logger = logging.getLogger(module_name)

    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger

    # 使用根logger的配置
    log_level = getattr(logging, config.LOG_LEVEL)
    logger.setLevel(log_level)

    # 不传播到父logger，避免重复输出
    logger.propagate = False

    # 日志格式
    formatter = RelativePathFormatter("%(asctime)s %(levelname)-8s %(name)s:%(lineno)d %(message)s")

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def setup_werkzeug_logger():
    """配置Werkzeug日志格式"""
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.INFO)

    # 移除默认处理器
    werkzeug_logger.handlers.clear()

    # 使用统一格式
    formatter = RelativePathFormatter("%(asctime)s %(levelname)-8s %(name)s:%(lineno)d %(message)s")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    werkzeug_logger.addHandler(console_handler)

    return werkzeug_logger


def setup_logger(
    name: str, log_file: str | None = None, level: str | None = None
) -> logging.Logger:
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
    formatter = RelativePathFormatter("%(asctime)s %(levelname)-8s %(name)s:%(lineno)d %(message)s")

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
app_logger = setup_logger("wechat_article_assistant", "app.log")
collect_logger = setup_logger("wechat_article_assistant.collect", "collect.log")
download_logger = setup_logger("wechat_article_assistant.download", "download.log")

# 配置Werkzeug日志
werkzeug_logger = setup_werkzeug_logger()
