"""路由模块初始化"""

from .article_routes import article_bp
from .main_routes import main_bp
from .wechat_routes import wechat_bp

__all__ = ["article_bp", "main_bp", "wechat_bp"]
