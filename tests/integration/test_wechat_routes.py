from unittest.mock import Mock, patch

from wechat_article_assistant.models import WechatAccount


def test_get_accounts_empty(client, db):
    """测试获取公众号列表（空）"""
    response = client.get("/api/wechat/list")
    assert response.status_code == 200
    data = response.json
    assert data["success"] is True
    assert len(data["data"]) == 0


def test_create_account(client, db):
    """测试创建公众号"""
    payload = {"nickname": "新公众号", "fakeid": "new_fakeid", "alias": "new_alias"}
    response = client.post("/api/wechat/create", json=payload)
    assert response.status_code == 200
    data = response.json
    assert data["success"] is True
    assert "id" in data

    # 验证数据库
    account = db.query(WechatAccount).filter_by(fakeid="new_fakeid").first()
    assert account is not None
    assert account.nickname == "新公众号"


def test_update_account(client, db):
    """测试更新公众号"""
    account = WechatAccount(nickname="旧名称", fakeid="update_fakeid")
    db.add(account)
    db.commit()
    db.refresh(account)

    payload = {"nickname": "新名称"}
    response = client.put(f"/api/wechat/{account.id}", json=payload)
    assert response.status_code == 200
    assert response.json["success"] is True

    db.refresh(account)
    assert account.nickname == "新名称"


def test_delete_account(client, db):
    """测试删除公众号"""
    account = WechatAccount(nickname="待删除", fakeid="delete_fakeid")
    db.add(account)
    db.commit()
    db.refresh(account)

    response = client.delete(f"/api/wechat/{account.id}")
    assert response.status_code == 200
    assert response.json["success"] is True

    deleted = db.query(WechatAccount).filter_by(id=account.id).first()
    assert deleted is None


def test_search_account_requires_query(client):
    """测试搜索公众号时缺少 query"""
    response = client.post("/api/wechat/search", json={})
    assert response.status_code == 200
    assert response.json["success"] is False
    assert response.json["message"] == "无效的请求数据"


def test_search_account_requires_login_in_popup_mode(client):
    """测试弹窗模式下搜索公众号时需要登录"""
    with patch(
        "wechat_article_assistant.routes.wechat_routes.wechat_auth.session_manager.is_session_valid",
        return_value=False,
    ), patch("wechat_article_assistant.routes.wechat_routes.config.LOGIN_MODE", "popup"):
        response = client.post("/api/wechat/search", json={"query": "OpenAI"})

    assert response.status_code == 200
    assert response.json["success"] is False
    assert response.json["needLogin"] is True
    assert response.json["loginMode"] == "popup"


def test_search_account_clears_session_on_login_expired(client):
    """测试搜索公众号时遇到登录失效会清理会话"""
    mock_response = Mock()
    mock_response.json.return_value = {"base_resp": {"ret": -1, "err_msg": "login expired"}}

    with patch(
        "wechat_article_assistant.routes.wechat_routes.wechat_auth.session_manager.is_session_valid",
        return_value=True,
    ), patch(
        "wechat_article_assistant.routes.wechat_routes.wechat_auth._verify_session",
        return_value=True,
    ), patch(
        "wechat_article_assistant.routes.wechat_routes.wechat_auth.get_session_data",
        return_value={"token": "token", "cookies": []},
    ), patch(
        "wechat_article_assistant.routes.wechat_routes.requests.get",
        return_value=mock_response,
    ), patch(
        "wechat_article_assistant.routes.wechat_routes.wechat_auth.session_manager.clear_session"
    ) as mock_clear, patch(
        "wechat_article_assistant.routes.wechat_routes.config.LOGIN_MODE",
        "popup",
    ):
        response = client.post("/api/wechat/search", json={"query": "OpenAI"})

    assert response.status_code == 200
    assert response.json["success"] is False
    assert response.json["needLogin"] is True
    assert response.json["message"] == "会话已失效，请重新扫码登录"
    mock_clear.assert_called_once()


def test_login_status(client):
    """测试登录状态接口"""
    with patch(
        "wechat_article_assistant.routes.wechat_routes.wechat_auth.session_manager.is_session_valid",
        return_value=True,
    ), patch("wechat_article_assistant.routes.wechat_routes.config.LOGIN_MODE", "popup"):
        response = client.get("/api/wechat/login/status")

    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["isLoggedIn"] is True
    assert response.json["loginMode"] == "popup"


def test_logout_calls_authenticator(client):
    """测试登出接口调用认证器"""
    with patch("wechat_article_assistant.routes.wechat_routes.wechat_auth.logout") as mock_logout:
        response = client.post("/api/wechat/logout")

    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["message"] == "已登出"
    mock_logout.assert_called_once()
