"""公众号管理路由"""

import requests
from flask import Blueprint, jsonify, request

from ..browser.wechat_authenticator import WechatAuthenticator
from ..config import config
from ..services.wechat_service import WechatService

wechat_bp = Blueprint("wechat", __name__, url_prefix="/api/wechat")
wechat_service = WechatService()
wechat_auth = WechatAuthenticator()


@wechat_bp.route("/list", methods=["GET"])
def get_accounts():
    """获取公众号列表"""
    accounts = wechat_service.get_all_accounts()
    return jsonify({"success": True, "data": accounts})


@wechat_bp.route("/<int:account_id>", methods=["GET"])
def get_account(account_id: int):
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
def update_account(account_id: int):
    """更新公众号"""
    data = request.json
    success, message = wechat_service.update_account(account_id, data)
    return jsonify({"success": success, "message": message})


@wechat_bp.route("/<int:account_id>", methods=["DELETE"])
def delete_account(account_id: int):
    """删除公众号"""
    success, message = wechat_service.delete_account(account_id)
    return jsonify({"success": success, "message": message})


@wechat_bp.route("/search", methods=["POST"])
def search_account():
    """搜索公众号（自动处理登录）"""
    data = request.json
    query = data.get("query", "")

    if not query:
        return jsonify({"success": False, "message": "搜索关键词不能为空"})

    try:
        # 确保已认证（自动处理会话复用和登录）
        if not wechat_auth.ensure_authenticated():
            return jsonify({"success": False, "message": "认证失败，请重试"})

        # 获取会话数据
        session_data = wechat_auth.get_session_data()
        if not session_data:
            return jsonify({"success": False, "message": "获取会话数据失败"})

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
            # 如果是会话失效错误，清除会话并提示重试
            if "登录" in error_msg or "login" in error_msg.lower():
                wechat_auth.session_manager.clear_session()
                return jsonify({"success": False, "message": "会话已失效，请重试"})
            return jsonify({"success": False, "message": error_msg})

    except Exception as e:
        return jsonify({"success": False, "message": f"搜索失败: {str(e)}"})


@wechat_bp.route("/login/status", methods=["GET"])
def check_login():
    """检查登录状态"""
    is_logged_in = wechat_auth.session_manager.is_session_valid()
    return jsonify({"success": True, "isLoggedIn": is_logged_in})


@wechat_bp.route("/logout", methods=["POST"])
def logout():
    """登出"""
    wechat_auth.logout()
    return jsonify({"success": True, "message": "已登出"})
