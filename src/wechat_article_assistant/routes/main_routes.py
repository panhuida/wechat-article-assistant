"""主页及基础功能路由"""

import requests
from flask import Blueprint, Response, render_template, request

from ..utils.logger import get_module_logger

logger = get_module_logger(__name__)

# 创建主蓝图，不设置 url_prefix，因为它是根路由
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """首页"""
    return render_template("index.html")


@main_bp.route("/wechat")
def wechat_list():
    """公众号列表页"""
    return render_template("wechat_list.html")


@main_bp.route("/articles")
def article_list():
    """文章列表页"""
    return render_template("article_list.html")


@main_bp.route("/api/image-proxy")
def image_proxy():
    """图片代理，解决微信图片防盗链问题"""
    image_url = request.args.get("url")
    if not image_url:
        return Response("Missing URL parameter", status=400)

    try:
        # 添加微信公众平台的 Referer
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://mp.weixin.qq.com/",
        }

        response = requests.get(image_url, headers=headers, timeout=10)

        if response.status_code == 200:
            return Response(
                response.content,
                mimetype=response.headers.get("Content-Type", "image/jpeg"),
                headers={"Cache-Control": "public, max-age=86400"},  # 缓存1天
            )
        return Response("Image not found", status=404)

    except Exception as e:
        logger.error(f"图片代理失败: {e}")
        return Response("Image proxy error", status=500)
