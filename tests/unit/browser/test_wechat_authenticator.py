import base64
from unittest.mock import Mock, patch

from wechat_article_assistant.browser.wechat_authenticator import WechatAuthenticator


def create_authenticator():
    """创建可控的认证器实例"""
    with patch("wechat_article_assistant.browser.wechat_authenticator.BrowserManager") as mock_browser, patch(
        "wechat_article_assistant.browser.wechat_authenticator.SessionManager"
    ) as mock_session:
        auth = WechatAuthenticator()
    return auth, mock_browser.return_value, mock_session.return_value


def test_ensure_authenticated_uses_existing_valid_session():
    """测试已有有效会话且验证通过时直接返回成功"""
    auth, _browser, session_manager = create_authenticator()
    session_manager.is_session_valid.return_value = True

    with patch.object(auth, "_verify_session", return_value=True) as mock_verify, patch.object(
        auth, "_do_browser_login", return_value=False
    ) as mock_login:
        result = auth.ensure_authenticated()

    assert result is True
    mock_verify.assert_called_once()
    mock_login.assert_not_called()


def test_ensure_authenticated_falls_back_to_browser_login():
    """测试会话无效时回退到浏览器登录"""
    auth, _browser, session_manager = create_authenticator()
    session_manager.is_session_valid.return_value = False

    with patch.object(auth, "_do_browser_login", return_value=True) as mock_login:
        result = auth.ensure_authenticated()

    assert result is True
    mock_login.assert_called_once()


def test_verify_session_returns_true_for_logged_in_url():
    """测试验证会话时识别登录后的 URL"""
    auth, _browser, session_manager = create_authenticator()
    session_manager.load_session.return_value = {
        "cookies": [{"name": "pass_ticket", "value": "cookie"}],
    }
    response = Mock()
    response.url = "https://mp.weixin.qq.com/cgi-bin/home?t=home/index&token=123"

    with patch(
        "wechat_article_assistant.browser.wechat_authenticator.requests.get",
        return_value=response,
    ) as mock_get:
        result = auth._verify_session()

    assert result is True
    mock_get.assert_called_once()


def test_verify_session_returns_false_on_request_error():
    """测试验证会话请求报错时返回 False"""
    auth, _browser, session_manager = create_authenticator()
    session_manager.load_session.return_value = {
        "cookies": [{"name": "pass_ticket", "value": "cookie"}],
    }

    with patch(
        "wechat_article_assistant.browser.wechat_authenticator.requests.get",
        side_effect=RuntimeError("boom"),
    ):
        result = auth._verify_session()

    assert result is False


def test_save_session_extracts_token_from_url_when_cookie_missing():
    """测试保存会话时在 cookie 缺少 token 时从 URL 提取"""
    auth, browser_manager, session_manager = create_authenticator()
    browser_manager.get_cookies.return_value = [{"name": "pass_ticket", "value": "cookie"}]
    page = Mock()
    page.url = "https://mp.weixin.qq.com/cgi-bin/home?t=home/index&token=456&lang=zh_CN"

    auth._save_session(page)

    session_manager.save_session.assert_called_once_with(
        [{"name": "pass_ticket", "value": "cookie"}],
        "456",
    )


def test_capture_qrcode_from_page_returns_base64_data_url():
    """测试二维码截图成功时返回 base64 data URL"""
    auth, _browser, _session_manager = create_authenticator()
    qrcode_element = Mock()
    qrcode_element.screenshot.return_value = b"png-bytes"
    page = Mock()
    page.query_selector.side_effect = lambda selector: qrcode_element if "img.qrcode_login_img" in selector else None

    with patch("wechat_article_assistant.browser.wechat_authenticator.time.sleep"):
        result = auth._capture_qrcode_from_page(page)

    assert result["success"] is True
    assert result["status"] == "waiting"
    assert result["qrcodeUrl"] == "data:image/png;base64," + base64.b64encode(b"png-bytes").decode("utf-8")


def test_poll_login_status_returns_success_when_session_exists():
    """测试未处于登录中但已有有效会话时返回 success"""
    auth, _browser, session_manager = create_authenticator()
    session_manager.is_session_valid.return_value = True
    auth._login_in_progress = False

    result = auth.poll_login_status()

    assert result == {"success": True, "status": "success", "message": "已登录"}


def test_cancel_login_resets_state():
    """测试取消登录会重置共享状态"""
    auth, _browser, _session_manager = create_authenticator()
    auth._login_in_progress = True
    auth._login_start_time = 123.0
    auth._login_qrcode = "qr"
    auth._login_status = {"status": "waiting"}

    auth.cancel_login()

    assert auth.is_login_in_progress() is False
    assert auth._login_start_time is None
    assert auth._login_qrcode is None
    assert auth._login_status == {}
    assert auth._login_cancel_event.is_set() is True


def test_start_qrcode_login_returns_already_logged_in_when_session_is_valid():
    """测试二维码登录在已有有效会话时直接返回已登录"""
    auth, _browser, session_manager = create_authenticator()
    session_manager.is_session_valid.return_value = True

    with patch.object(auth, "_verify_session", return_value=True):
        result = auth.start_qrcode_login()

    assert result == {"success": True, "status": "already_logged_in", "message": "已登录"}


def test_start_qrcode_login_reuses_existing_qrcode():
    """测试二维码登录已在进行中时复用现有二维码"""
    auth, _browser, session_manager = create_authenticator()
    session_manager.is_session_valid.return_value = False
    auth._login_in_progress = True
    auth._login_qrcode = "data:image/png;base64,abc"

    result = auth.start_qrcode_login()

    assert result == {
        "success": True,
        "status": "waiting",
        "qrcodeUrl": "data:image/png;base64,abc",
        "message": "请使用微信扫描二维码登录",
    }


def test_start_qrcode_login_returns_qrcode_after_thread_updates_state():
    """测试启动登录线程后返回新生成的二维码"""
    auth, _browser, session_manager = create_authenticator()
    session_manager.is_session_valid.return_value = False

    def fake_sleep(_seconds: float) -> None:
        auth._login_qrcode = "data:image/png;base64,new"

    with patch(
        "wechat_article_assistant.browser.wechat_authenticator.threading.Thread"
    ) as mock_thread, patch(
        "wechat_article_assistant.browser.wechat_authenticator.time.sleep",
        side_effect=fake_sleep,
    ):
        result = auth.start_qrcode_login()

    assert result == {
        "success": True,
        "status": "waiting",
        "qrcodeUrl": "data:image/png;base64,new",
        "message": "请使用微信扫描二维码登录",
    }
    mock_thread.assert_called_once()
    mock_thread.return_value.start.assert_called_once()


def test_start_qrcode_login_returns_error_status_from_worker():
    """测试登录线程上报错误状态时直接返回错误信息"""
    auth, _browser, session_manager = create_authenticator()
    session_manager.is_session_valid.return_value = False

    def fake_sleep(_seconds: float) -> None:
        auth._login_status = {"success": False, "status": "error", "message": "二维码加载失败"}

    with patch(
        "wechat_article_assistant.browser.wechat_authenticator.threading.Thread"
    ), patch(
        "wechat_article_assistant.browser.wechat_authenticator.time.sleep",
        side_effect=fake_sleep,
    ):
        result = auth.start_qrcode_login()

    assert result == {"success": False, "status": "error", "message": "二维码加载失败"}


def test_start_qrcode_login_returns_timeout_when_qrcode_never_arrives():
    """测试二维码长时间未生成时返回超时"""
    auth, _browser, session_manager = create_authenticator()
    session_manager.is_session_valid.return_value = False

    with patch(
        "wechat_article_assistant.browser.wechat_authenticator.threading.Thread"
    ), patch("wechat_article_assistant.browser.wechat_authenticator.time.sleep"):
        result = auth.start_qrcode_login()

    assert result == {"success": False, "message": "获取二维码超时"}
