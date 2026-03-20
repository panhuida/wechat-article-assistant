"""浏览器实例管理模块（单例模式）"""

from typing import Any, cast

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from ..utils.logger import get_module_logger

__all__ = ["BrowserManager"]

logger = get_module_logger(__name__)


class BrowserManager:
    """浏览器管理器（单例）"""

    _instance: "BrowserManager | None" = None
    _initialized: bool = False

    def __new__(cls):
        """单例模式：确保只有一个实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化浏览器管理器"""
        # 防止重复初始化
        if BrowserManager._initialized:
            return

        self.playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self._is_running = False

        BrowserManager._initialized = True
        logger.debug("BrowserManager单例已创建")

    @property
    def is_running(self) -> bool:
        """检查浏览器是否正在运行"""
        return self._is_running and self.page is not None

    def start(self, headless: bool = False) -> Page:
        """
        启动浏览器

        Args:
            headless: 是否无头模式

        Returns:
            页面对象
        """
        # 如果已经启动，直接返回
        if self.is_running:
            logger.info("浏览器已在运行，复用现有实例")
            assert self.page is not None
            return self.page

        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            self._is_running = True
            logger.info("浏览器启动成功")
            assert self.page is not None
            return self.page
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            self._is_running = False
            raise

    def stop(self):
        """停止浏览器"""
        if not self._is_running:
            logger.debug("浏览器未运行，无需关闭")
            return

        try:
            if self.page:
                self.page.close()
                self.page = None
            if self.context:
                self.context.close()
                self.context = None
            if self.browser:
                self.browser.close()
                self.browser = None
            if self.playwright:
                self.playwright.stop()
                self.playwright = None

            self._is_running = False
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")
            self._is_running = False

    def get_cookies(self) -> list[dict[str, Any]]:
        """
        获取当前上下文的cookies

        Returns:
            Cookie列表
        """
        if self.context:
            return cast(list[dict[str, Any]], self.context.cookies())
        return []

    def set_cookies(self, cookies: list[dict[str, Any]]):
        """
        设置cookies到当前上下文

        Args:
            cookies: Cookie列表
        """
        if self.context:
            self.context.add_cookies(cast(Any, cookies))
            logger.info(f"已设置 {len(cookies)} 个Cookies")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.stop()

    @classmethod
    def reset_instance(cls):
        """重置单例实例（主要用于测试）"""
        if cls._instance:
            cls._instance.stop()
        cls._instance = None
        cls._initialized = False
        logger.debug("BrowserManager单例已重置")
