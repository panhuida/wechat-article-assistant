from unittest.mock import Mock, patch

from wechat_article_assistant.browser.browser_manager import BrowserManager


def setup_function():
    """每个测试前重置单例状态"""
    BrowserManager.reset_instance()


def teardown_function():
    """每个测试后重置单例状态"""
    BrowserManager.reset_instance()


def test_browser_manager_is_singleton():
    """测试 BrowserManager 为单例"""
    manager1 = BrowserManager()
    manager2 = BrowserManager()

    assert manager1 is manager2


def test_start_launches_browser_and_reuses_existing_page():
    """测试启动浏览器并复用现有页面"""
    playwright_instance = Mock()
    browser = Mock()
    context = Mock()
    page = Mock()
    playwright_instance.chromium.launch.return_value = browser
    browser.new_context.return_value = context
    context.new_page.return_value = page

    manager = BrowserManager()

    with patch(
        "wechat_article_assistant.browser.browser_manager.sync_playwright"
    ) as mock_sync_playwright:
        mock_sync_playwright.return_value.start.return_value = playwright_instance

        first_page = manager.start(headless=True)
        second_page = manager.start(headless=False)

    assert first_page is page
    assert second_page is page
    assert manager.is_running is True
    playwright_instance.chromium.launch.assert_called_once_with(headless=True)


def test_stop_closes_all_resources():
    """测试停止浏览器时关闭 page/context/browser/playwright"""
    manager = BrowserManager()
    manager._is_running = True
    manager.page = Mock()
    manager.context = Mock()
    manager.browser = Mock()
    manager.playwright = Mock()

    manager.stop()

    manager.page = None
    manager.context = None
    manager.browser = None
    manager.playwright = None
    assert manager.is_running is False


def test_get_and_set_cookies_delegate_to_context():
    """测试 cookies 读写委托给 context"""
    manager = BrowserManager()
    manager.context = Mock()
    manager.context.cookies.return_value = [{"name": "token", "value": "x"}]

    cookies = manager.get_cookies()
    manager.set_cookies([{"name": "token", "value": "x"}])

    assert cookies == [{"name": "token", "value": "x"}]
    manager.context.add_cookies.assert_called_once_with([{"name": "token", "value": "x"}])


def test_context_manager_stops_browser_on_exit():
    """测试上下文管理器退出时自动停止浏览器"""
    manager = BrowserManager()

    with patch.object(manager, "stop") as mock_stop:
        with manager as context_manager:
            assert context_manager is manager

    mock_stop.assert_called_once()


def test_reset_instance_clears_singleton():
    """测试 reset_instance 会重置单例状态"""
    manager = BrowserManager()

    with patch.object(manager, "stop") as mock_stop:
        BrowserManager.reset_instance()

    assert BrowserManager._instance is None
    assert BrowserManager._initialized is False
    mock_stop.assert_called_once()
