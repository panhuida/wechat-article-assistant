"""Flask应用入口"""

from flask import Flask, render_template, request, Response

from .config import config
from .models import init_db
from .routes.article_routes import article_bp
from .routes.wechat_routes import wechat_bp
from .utils.logger import get_module_logger, setup_werkzeug_logger

logger = get_module_logger(__name__)

# 初始化werkzeug日志格式
setup_werkzeug_logger()


def create_app() -> Flask:
    """创建Flask应用"""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["DEBUG"] = config.DEBUG

    # 初始化配置
    config.init_app()

    # 初始化数据库
    init_db()
    logger.info("数据库初始化完成")

    # 注册蓝图
    app.register_blueprint(wechat_bp)
    app.register_blueprint(article_bp)
    logger.info("路由注册完成")

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

    # 图片代理路由
    @app.route("/api/image-proxy")
    def image_proxy():
        """图片代理，解决微信图片防盗链问题"""
        import requests
        
        image_url = request.args.get("url")
        if not image_url:
            return Response("Missing URL parameter", status=400)
        
        try:
            # 添加微信公众平台的 Referer
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://mp.weixin.qq.com/"
            }
            
            response = requests.get(image_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return Response(
                    response.content,
                    mimetype=response.headers.get("Content-Type", "image/jpeg"),
                    headers={"Cache-Control": "public, max-age=86400"}  # 缓存1天
                )
            else:
                return Response("Image not found", status=404)
                
        except Exception as e:
            logger.error(f"图片代理失败: {e}")
            return Response("Image proxy error", status=500)

    logger.info("Flask应用创建完成")
    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)
