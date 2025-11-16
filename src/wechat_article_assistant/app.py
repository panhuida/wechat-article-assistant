"""Flask应用入口"""

from flask import Flask, render_template

from .config import config
from .models import init_db
from .routes.article_routes import article_bp
from .routes.wechat_routes import wechat_bp
from .utils.logger import app_logger


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["DEBUG"] = config.DEBUG

    # 初始化配置
    config.init_app()

    # 初始化数据库
    init_db()
    app_logger.info("数据库初始化完成")

    # 注册蓝图
    app.register_blueprint(wechat_bp)
    app.register_blueprint(article_bp)
    app_logger.info("路由注册完成")

    # 首页路由
    @app.route("/")
    def index():
        """首页"""
        return render_template("index.html")

    # 公众号列表页
    @app.route("/wechat")
    def wechat_list():
        """公众号列表页"""
        return render_template("wechat_list.html")

    # 文章列表页
    @app.route("/articles")
    def article_list():
        """文章列表页"""
        return render_template("article_list.html")

    app_logger.info("Flask应用创建完成")
    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)
