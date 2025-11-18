"""微信公众平台认证管理器"""

import time
from typing import Optional

import requests

from ..config import config
from ..utils.logger import get_module_logger
from .browser_manager import BrowserManager
from .session_manager import SessionManager

logger = get_module_logger(__name__)


class WechatAuthenticator:
    """微信公众平台认证管理器（协调SessionManager和BrowserManager）"""

    def __init__(self):
        """初始化认证管理器"""
        self.session_manager = SessionManager()
        self.browser_manager = BrowserManager()
        self.login_url = f"{config.WECHAT_MP_URL}/"

    def ensure_authenticated(self) -> bool:
        """
        确保已认证（自动处理会话复用和登录）

        流程：
        1. 检查是否存在有效会话
        2. 如果有，尝试验证会话是否真实有效
        3. 如果会话失效，启动浏览器登录
        4. 保存新会话

        Returns:
            是否认证成功
        """
        logger.info("开始认证流程...")

        # 1. 检查会话文件是否存在且格式有效
        if self.session_manager.is_session_valid():
            logger.info("发现有效的会话文件，尝试验证...")
            
            # 2. 验证会话是否真实可用
            if self._verify_session():
                logger.info("✓ 会话验证成功，可以直接使用")
                return True
            
            logger.warning("会话验证失败，需要重新登录")
        else:
            logger.info("未找到有效会话，需要登录")

        # 3. 启动浏览器登录
        return self._do_browser_login()

    def _verify_session(self) -> bool:
        """
        验证会话是否真实有效（通过调用微信API）

        Returns:
            会话是否有效
        """
        try:
            session_data = self.session_manager.load_session()
            if not session_data or not session_data.get("cookies"):
                return False

            # 构造cookies字典
            cookies = {cookie["name"]: cookie["value"] for cookie in session_data["cookies"]}
            
            # 尝试访问微信公众平台首页
            response = requests.get(
                self.login_url,
                cookies=cookies,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                timeout=10,
                allow_redirects=True
            )

            # 检查是否跳转到登录后的页面
            if any(keyword in response.url for keyword in ["cgi-bin/home", "token=", "home/index"]):
                logger.info(f"会话有效，当前URL: {response.url}")
                return True
            
            logger.warning(f"会话已失效，被重定向到: {response.url}")
            return False

        except Exception as e:
            logger.warning(f"验证会话时出错: {e}")
            return False

    def _do_browser_login(self) -> bool:
        """
        执行浏览器登录流程

        Returns:
            是否登录成功
        """
        try:
            logger.info("启动浏览器进行登录...")
            
            # 启动浏览器（非无头模式，用户可见）
            page = self.browser_manager.start(headless=False)
            
            # 访问登录页面
            logger.info(f"正在访问: {self.login_url}")
            page.goto(self.login_url, wait_until="domcontentloaded", timeout=30000)
            
            # 等待页面稳定
            time.sleep(2)
            
            # 检查是否已经登录（浏览器中有旧的cookie）
            current_url = page.url
            if any(keyword in current_url for keyword in ["cgi-bin/home", "token=", "home/index"]):
                logger.info(f"检测到浏览器已登录，当前URL: {current_url}")
                self._save_session(page)
                return True
            
            # 需要扫码登录
            logger.info("请在浏览器中使用微信扫码登录...")
            logger.info("=" * 60)
            logger.info("等待用户扫码...")
            logger.info("=" * 60)
            
            # 等待登录成功
            if self._wait_for_login(page):
                self._save_session(page)
                return True
            
            return False

        except Exception as e:
            logger.error(f"浏览器登录失败: {e}", exc_info=True)
            return False
        finally:
            # 登录完成后关闭浏览器
            self.browser_manager.stop()

    def _wait_for_login(self, page, timeout: int = 300) -> bool:
        """
        等待用户扫码登录

        Args:
            page: 浏览器页面对象
            timeout: 超时时间（秒）

        Returns:
            是否登录成功
        """
        start_time = time.time()
        initial_url = page.url
        logger.info(f"初始URL: {initial_url}")
        logger.info(f"开始监听登录，超时时间: {timeout}秒")

        check_count = 0
        last_log_time = start_time

        while time.time() - start_time < timeout:
            check_count += 1

            # 每10次检查打印一次日志
            if check_count % 10 == 0:
                elapsed = int(time.time() - start_time)
                logger.debug(f"[{elapsed}s] 检查次数: {check_count}")

            try:
                # 获取当前URL
                try:
                    current_url = page.evaluate("() => window.location.href")
                except Exception as e:
                    logger.debug(f"通过evaluate获取URL失败: {e}")
                    current_url = page.url

                # 每5秒打印一次当前URL
                current_time = time.time()
                if current_time - last_log_time >= 5:
                    elapsed = int(current_time - start_time)
                    logger.info(f"[{elapsed}s] 当前URL: {current_url}")
                    last_log_time = current_time

                # 检查URL是否包含登录成功的特征
                if any(keyword in current_url for keyword in ["cgi-bin/home", "token=", "home/index"]):
                    logger.info(f"✓ 检测到登录成功！URL: {current_url}")
                    
                    # 等待页面稳定
                    logger.info("等待页面稳定...")
                    time.sleep(2)
                    
                    return True

                # 检查是否有登录后的特征元素
                try:
                    success_selectors = [
                        ".weui-desktop-account__info",
                        ".account_setting_area",
                        ".new_msg_nav",
                        "a[href*='account']",
                        ".icon_menu"
                    ]

                    for selector in success_selectors:
                        if page.query_selector(selector):
                            logger.info(f"✓ 检测到登录后的页面元素: {selector}")
                            return True
                except Exception as e:
                    logger.debug(f"查询登录元素时出错: {e}")

            except Exception as e:
                logger.debug(f"检查登录状态时出错: {e}")

            # 等待1秒再检查
            time.sleep(1)

        logger.warning(f"登录超时（{timeout}秒），未检测到登录成功")
        return False

    def _save_session(self, page):
        """
        保存登录会话数据

        Args:
            page: 浏览器页面对象
        """
        try:
            logger.info("开始保存会话数据...")

            # 获取cookies
            cookies = self.browser_manager.get_cookies()
            logger.info(f"获取到 {len(cookies)} 个cookies")

            # 提取token
            token = None
            for cookie in cookies:
                if cookie.get("name") == "token":
                    token = cookie.get("value")
                    logger.info(f"从cookies中找到token: {token[:20] if token else 'None'}...")
                    break

            if not token:
                # 尝试从URL中提取token
                url = page.url
                logger.info(f"当前URL: {url}")
                if "token=" in url:
                    token = url.split("token=")[1].split("&")[0]
                    logger.info(f"从URL中提取token: {token[:20] if token else 'None'}...")

            # 保存会话
            if self.session_manager.save_session(cookies, token):
                logger.info("✓ 会话保存成功")
            else:
                logger.warning("⚠ 会话保存失败")

        except Exception as e:
            logger.error(f"保存会话失败: {e}", exc_info=True)

    def get_session_data(self) -> Optional[dict]:
        """
        获取当前会话数据

        Returns:
            会话数据字典，失败返回None
        """
        return self.session_manager.load_session()

    def logout(self):
        """登出并清除会话"""
        self.session_manager.clear_session()
        self.browser_manager.stop()
        logger.info("已登出")
