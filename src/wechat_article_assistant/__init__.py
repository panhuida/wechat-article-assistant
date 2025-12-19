"""微信公众号文章阅读助手"""

from flask import Flask

from .config import config
from .models import init_db
from .routes.article_routes import article_bp
from .routes.main_routes import main_bp
from .routes.wechat_routes import wechat_bp
from .utils.logger import get_module_logger, setup_werkzeug_logger

__version__ = "0.1.0"

logger = get_module_logger(__name__)

# 初始化werkzeug日志格式
setup_werkzeug_logger()


def create_app() -> Flask:
    """
    创建Flask应用工厂函数
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["DEBUG"] = config.DEBUG

    # 初始化配置
    config.init_app()

    # 初始化数据库
    init_db()
    logger.info("数据库初始化完成")

    # 注册蓝图
    app.register_blueprint(main_bp)  # 注册主路由
    app.register_blueprint(wechat_bp)  # 注册公众号功能路由
    app.register_blueprint(article_bp)  # 注册文章功能路由
    logger.info("路由注册完成")

    logger.info("Flask应用创建完成")
    return app
