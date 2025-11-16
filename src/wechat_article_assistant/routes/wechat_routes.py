"""公众号管理路由"""

from flask import Blueprint, request, jsonify, render_template
from ..services.wechat_service import WechatService
from ..browser.wechat_login import WechatLogin
from ..config import config
import requests

wechat_bp = Blueprint("wechat", __name__, url_prefix="/api/wechat")
wechat_service = WechatService()
wechat_login = WechatLogin()


@wechat_bp.route("/list", methods=["GET"])
def get_accounts():
    """获取公众号列表"""
    accounts = wechat_service.get_all_accounts()
    return jsonify({"success": True, "data": accounts})


@wechat_bp.route("/<int:account_id>", methods=["GET"])
def get_account(account_id):
    """获取单个公众号"""
    account = wechat_service.get_account_by_id(account_id)
    if account:
        return jsonify({"success": True, "data": account})
    return jsonify({"success": False, "message": "公众号不存在"}), 404


@wechat_bp.route("/create", methods=["POST"])
def create_account():
    """创建公众号"""
    data = request.json
    success, message, account_id = wechat_service.create_account(data)
    return jsonify({"success": success, "message": message, "id": account_id})


@wechat_bp.route("/<int:account_id>", methods=["PUT"])
def update_account(account_id):
    """更新公众号"""
    data = request.json
    success, message = wechat_service.update_account(account_id, data)
    return jsonify({"success": success, "message": message})


@wechat_bp.route("/<int:account_id>", methods=["DELETE"])
def delete_account(account_id):
    """删除公众号"""
    success, message = wechat_service.delete_account(account_id)
    return jsonify({"success": success, "message": message})


@wechat_bp.route("/search", methods=["POST"])
def search_account():
    """搜索公众号"""
    data = request.json
    query = data.get("query", "")

    if not query:
        return jsonify({"success": False, "message": "搜索关键词不能为空"})

    # 检查登录状态
    if not wechat_login.check_login_status():
        return jsonify({"success": False, "message": "请先登录", "needLogin": True})

    try:
        # 获取会话数据
        session_data = wechat_login.session_manager.load_session()
        if not session_data:
            return jsonify({"success": False, "message": "会话已失效", "needLogin": True})

        # 构造搜索请求
        url = f"{config.WECHAT_MP_URL}/cgi-bin/searchbiz"
        params = {
            "action": "search_biz",
            "begin": 0,
            "count": 5,
            "query": query,
            "token": session_data.get("token", ""),
            "lang": "zh_CN",
            "f": "json",
            "ajax": 1,
        }

        cookies = {cookie["name"]: cookie["value"] for cookie in session_data.get("cookies", [])}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": config.WECHAT_MP_URL,
        }

        response = requests.get(url, params=params, cookies=cookies, headers=headers, timeout=30)
        result = response.json()

        if result.get("base_resp", {}).get("ret") == 0:
            accounts = result.get("list", [])
            return jsonify({"success": True, "data": accounts})
        else:
            error_msg = result.get("base_resp", {}).get("err_msg", "搜索失败")
            return jsonify({"success": False, "message": error_msg})

    except Exception as e:
        return jsonify({"success": False, "message": f"搜索失败: {str(e)}"})


@wechat_bp.route("/login/status", methods=["GET"])
def check_login():
    """检查登录状态"""
    is_logged_in = wechat_login.check_login_status()
    return jsonify({"success": True, "isLoggedIn": is_logged_in})


@wechat_bp.route("/login/qrcode", methods=["GET"])
def get_qrcode():
    """获取登录二维码"""
    try:
        qr_url = wechat_login.get_qr_code_url()
        if qr_url:
            return jsonify({"success": True, "qrUrl": qr_url})
        return jsonify({"success": False, "message": "获取二维码失败"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@wechat_bp.route("/login/wait", methods=["POST"])
def wait_login():
    """等待用户扫码登录"""
    try:
        success = wechat_login.wait_for_login(timeout=300)
        if success:
            return jsonify({"success": True, "message": "登录成功"})
        return jsonify({"success": False, "message": "登录超时"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@wechat_bp.route("/logout", methods=["POST"])
def logout():
    """登出"""
    wechat_login.logout()
    return jsonify({"success": True, "message": "已登出"})
