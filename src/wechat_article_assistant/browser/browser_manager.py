"""浏览器实例管理模块"""

from typing import Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from ..utils.logger import app_logger


class BrowserManager:
    """浏览器管理器"""

    def __init__(self):
        """初始化浏览器管理器"""
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self, headless: bool = False) -> Page:
        """
        启动浏览器

        Args:
            headless: 是否无头模式

        Returns:
            页面对象
        """
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            app_logger.info("浏览器启动成功")
            return self.page
        except Exception as e:
            app_logger.error(f"浏览器启动失败: {e}")
            raise

    def stop(self):
        """停止浏览器"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            app_logger.info("浏览器已关闭")
        except Exception as e:
            app_logger.error(f"关闭浏览器失败: {e}")

    def get_cookies(self) -> list:
        """
        获取当前上下文的cookies

        Returns:
            Cookie列表
        """
        if self.context:
            return self.context.cookies()
        return []

    def set_cookies(self, cookies: list):
        """
        设置cookies到当前上下文

        Args:
            cookies: Cookie列表
        """
        if self.context:
            self.context.add_cookies(cookies)
            app_logger.info("Cookies已设置")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.stop()
