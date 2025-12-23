"""微信公众平台认证管理器"""

import base64
import threading
import time
from typing import Any

import requests
from playwright.sync_api import Page

from ..config import config
from ..utils.logger import get_module_logger
from .browser_manager import BrowserManager
from .session_manager import SessionManager

__all__ = ["WechatAuthenticator"]

logger = get_module_logger(__name__)


class WechatAuthenticator:
    """微信公众平台认证管理器（协调SessionManager和BrowserManager）"""

    def __init__(self):
        """初始化认证管理器"""
        self.session_manager = SessionManager()
        self.browser_manager = BrowserManager()
        self.login_url = f"{config.WECHAT_MP_URL}/"
        self._login_in_progress = False
        self._login_start_time: float | None = None
        
        # 用于线程安全的状态共享
        self._login_status_lock = threading.Lock()
        self._login_status: dict[str, Any] = {}
        self._login_qrcode: str | None = None
        self._login_thread: threading.Thread | None = None
        self._login_cancel_event = threading.Event()

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
                allow_redirects=True,
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

    def _wait_for_login(self, page: Page, timeout: int = 300) -> bool:
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
                if any(
                    keyword in current_url for keyword in ["cgi-bin/home", "token=", "home/index"]
                ):
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
                        ".icon_menu",
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

    def _save_session(self, page: Page, browser_manager: BrowserManager | None = None):
        """
        保存登录会话数据

        Args:
            page: 浏览器页面对象
            browser_manager: 浏览器管理器实例，为None时使用self.browser_manager
        """
        try:
            logger.info("开始保存会话数据...")

            # 获取cookies
            bm = browser_manager or self.browser_manager
            cookies = bm.get_cookies()
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

    def get_session_data(self) -> dict[str, Any] | None:
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
        self._login_in_progress = False
        logger.info("已登出")

    # ============ 弹窗登录模式相关方法 ============

    def start_qrcode_login(self) -> dict[str, Any]:
        """
        启动二维码登录流程（弹窗模式）
        
        使用后台线程运行Playwright，避免跨线程访问问题

        Returns:
            包含二维码URL的字典，失败返回错误信息
        """
        try:
            # 如果已有有效会话，直接返回
            if self.session_manager.is_session_valid() and self._verify_session():
                logger.info("已有有效会话，无需登录")
                return {"success": True, "status": "already_logged_in", "message": "已登录"}

            # 如果登录已在进行中，返回当前二维码
            with self._login_status_lock:
                if self._login_in_progress and self._login_qrcode:
                    logger.info("登录已在进行中，返回现有二维码")
                    return {
                        "success": True,
                        "status": "waiting",
                        "qrcodeUrl": self._login_qrcode,
                        "message": "请使用微信扫描二维码登录"
                    }

            # 重置状态
            self._login_cancel_event.clear()
            with self._login_status_lock:
                self._login_status = {"success": True, "status": "initializing", "message": "正在初始化..."}
                self._login_qrcode = None
                self._login_in_progress = True
                self._login_start_time = time.time()

            # 启动后台线程运行登录流程
            self._login_thread = threading.Thread(target=self._login_thread_worker, daemon=True)
            self._login_thread.start()

            # 等待二维码获取完成（最多10秒）
            for _ in range(50):  # 50 * 0.2s = 10s
                time.sleep(0.2)
                with self._login_status_lock:
                    if self._login_qrcode:
                        return {
                            "success": True,
                            "status": "waiting",
                            "qrcodeUrl": self._login_qrcode,
                            "message": "请使用微信扫描二维码登录"
                        }
                    if self._login_status.get("status") == "error":
                        return self._login_status.copy()
                    if self._login_status.get("status") == "already_logged_in":
                        return self._login_status.copy()

            # 超时未获取到二维码
            return {"success": False, "message": "获取二维码超时"}

        except Exception as e:
            logger.error(f"启动二维码登录失败: {e}", exc_info=True)
            self._login_in_progress = False
            return {"success": False, "message": f"启动登录失败: {str(e)}"}

    def _login_thread_worker(self):
        """
        登录线程工作函数
        
        在后台线程中运行Playwright，持续轮询登录状态
        """
        # 创建专用的BrowserManager实例
        browser_manager = BrowserManager()
        
        try:
            logger.info("启动无头浏览器获取二维码...")
            
            # 启动无头浏览器
            page = browser_manager.start(headless=True)

            # 访问登录页面
            logger.info(f"正在访问: {self.login_url}")
            page.goto(self.login_url, wait_until="domcontentloaded", timeout=30000)

            # 等待页面加载
            time.sleep(2)

            # 检查是否已经登录（浏览器中有旧的cookie）
            current_url = page.url
            if any(keyword in current_url for keyword in ["cgi-bin/home", "token=", "home/index"]):
                logger.info(f"检测到浏览器已登录，当前URL: {current_url}")
                self._save_session(page, browser_manager)
                with self._login_status_lock:
                    self._login_status = {"success": True, "status": "already_logged_in", "message": "已登录"}
                    self._login_in_progress = False
                browser_manager.stop()
                return

            # 获取二维码
            qrcode_result = self._capture_qrcode_from_page(page)
            if not qrcode_result.get("success"):
                with self._login_status_lock:
                    self._login_status = qrcode_result
                    self._login_in_progress = False
                browser_manager.stop()
                return

            # 保存二维码
            with self._login_status_lock:
                self._login_qrcode = qrcode_result.get("qrcodeUrl")
                self._login_status = {
                    "success": True,
                    "status": "waiting",
                    "message": "等待扫码..."
                }

            # 开始轮询登录状态
            timeout = 300  # 5分钟超时
            start_time = time.time()
            
            while not self._login_cancel_event.is_set():
                # 检查超时
                if time.time() - start_time > timeout:
                    logger.warning(f"登录超时（{timeout}秒）")
                    with self._login_status_lock:
                        self._login_status = {"success": False, "status": "timeout", "message": "登录超时，请重新获取二维码"}
                        self._login_in_progress = False
                    browser_manager.stop()
                    return

                # 检查登录状态
                try:
                    current_url = page.url
                    
                    # 检查URL是否包含登录成功的特征
                    if any(keyword in current_url for keyword in ["cgi-bin/home", "token=", "home/index"]):
                        logger.info(f"✓ 检测到登录成功！URL: {current_url}")
                        time.sleep(1)  # 等待页面稳定
                        self._save_session(page, browser_manager)
                        with self._login_status_lock:
                            self._login_status = {"success": True, "status": "success", "message": "登录成功"}
                            self._login_in_progress = False
                        browser_manager.stop()
                        return

                    # 检查是否有登录后的特征元素
                    success_selectors = [
                        ".weui-desktop-account__info",
                        ".account_setting_area",
                        ".new_msg_nav",
                        "a[href*='account']",
                        ".icon_menu",
                    ]

                    for selector in success_selectors:
                        try:
                            if page.query_selector(selector):
                                logger.info(f"✓ 检测到登录后的页面元素: {selector}")
                                self._save_session(page, browser_manager)
                                with self._login_status_lock:
                                    self._login_status = {"success": True, "status": "success", "message": "登录成功"}
                                    self._login_in_progress = False
                                browser_manager.stop()
                                return
                        except Exception:
                            continue

                    # 检查页面内容
                    try:
                        page_content = page.content()
                        
                        # 检测已扫码等待确认
                        if "扫描成功" in page_content or "请在手机上确认" in page_content:
                            logger.info("检测到已扫码，等待确认")
                            with self._login_status_lock:
                                self._login_status = {
                                    "success": True,
                                    "status": "scanned",
                                    "message": "已扫码，请在手机上确认登录"
                                }
                        
                        # 检查二维码是否消失（可能需要刷新或已登录）
                        qrcode_element = page.query_selector('img[src*="scanloginqrcode"]')
                        if not qrcode_element:
                            # 二维码消失了，等待页面跳转
                            logger.info("二维码已消失，等待页面跳转...")
                            time.sleep(2)
                            current_url = page.url
                            if any(keyword in current_url for keyword in ["cgi-bin/home", "token=", "home/index"]):
                                logger.info(f"✓ 页面跳转成功！URL: {current_url}")
                                self._save_session(page, browser_manager)
                                with self._login_status_lock:
                                    self._login_status = {"success": True, "status": "success", "message": "登录成功"}
                                    self._login_in_progress = False
                                browser_manager.stop()
                                return
                                
                    except Exception as e:
                        logger.debug(f"检查页面内容时出错: {e}")

                except Exception as e:
                    logger.debug(f"检查登录状态时出错: {e}")

                # 等待后继续轮询
                time.sleep(2)

        except Exception as e:
            logger.error(f"登录线程出错: {e}", exc_info=True)
            with self._login_status_lock:
                self._login_status = {"success": False, "status": "error", "message": f"登录失败: {str(e)}"}
                self._login_in_progress = False
        finally:
            browser_manager.stop()

    def _capture_qrcode_from_page(self, page: Page) -> dict[str, Any]:
        """
        从当前页面获取二维码图片（使用截图方式）

        Args:
            page: 浏览器页面对象
            
        Returns:
            包含二维码base64数据的字典
        """
        try:
            if not page:
                return {"success": False, "message": "浏览器页面未准备好"}

            # 等待二维码图片加载
            try:
                # 微信公众平台的二维码图片选择器
                qrcode_selectors = [
                    'img.qrcode_login_img',
                    'img[src*="scanloginqrcode"]',
                    '.login__type__container__scan__qrcode img',
                    '.qrcode img',
                ]

                qrcode_element = None
                for selector in qrcode_selectors:
                    try:
                        element = page.query_selector(selector)
                        if element:
                            logger.info(f"找到二维码图片元素: {selector}")
                            qrcode_element = element
                            break
                    except Exception:
                        continue

                if qrcode_element:
                    # 使用截图方式获取二维码图片
                    try:
                        # 等待图片加载完成
                        time.sleep(1)
                        
                        # 截取二维码元素
                        screenshot_bytes = qrcode_element.screenshot()
                        
                        # 转换为 base64
                        qrcode_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                        qrcode_data_url = f"data:image/png;base64,{qrcode_base64}"
                        
                        logger.info("成功截取二维码图片")
                        
                        return {
                            "success": True,
                            "status": "waiting",
                            "qrcodeUrl": qrcode_data_url,
                            "message": "请使用微信扫描二维码登录"
                        }
                    except Exception as e:
                        logger.error(f"截取二维码图片失败: {e}")
                        # 降级：尝试返回URL
                        qrcode_url = qrcode_element.get_attribute("src")
                        if qrcode_url:
                            if qrcode_url.startswith("/"):
                                qrcode_url = f"{config.WECHAT_MP_URL}{qrcode_url}"
                            return {
                                "success": True,
                                "status": "waiting",
                                "qrcodeUrl": qrcode_url,
                                "message": "请使用微信扫描二维码登录"
                            }
                
                # 没有找到二维码元素，尝试截取整个登录区域
                logger.warning("未找到二维码图片元素，尝试截取登录区域")
                
                # 尝试找登录容器并截图
                login_selectors = [
                    '.login__type__container__scan',
                    '.qrcode_login',
                    '.login_qrcode_area',
                ]
                
                for selector in login_selectors:
                    try:
                        login_element = page.query_selector(selector)
                        if login_element:
                            screenshot_bytes = login_element.screenshot()
                            qrcode_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                            qrcode_data_url = f"data:image/png;base64,{qrcode_base64}"
                            logger.info(f"成功截取登录区域: {selector}")
                            return {
                                "success": True,
                                "status": "waiting",
                                "qrcodeUrl": qrcode_data_url,
                                "message": "请使用微信扫描二维码登录"
                            }
                    except Exception:
                        continue
                
                return {"success": False, "message": "未找到二维码"}

            except Exception as e:
                logger.error(f"获取二维码图片失败: {e}")
                return {"success": False, "message": f"获取二维码失败: {str(e)}"}

        except Exception as e:
            logger.error(f"获取二维码失败: {e}", exc_info=True)
            return {"success": False, "message": f"获取二维码失败: {str(e)}"}

    def poll_login_status(self) -> dict[str, Any]:
        """
        轮询检查登录状态（弹窗模式）
        
        只读取后台线程更新的共享状态变量，不直接访问Playwright

        Returns:
            登录状态字典
        """
        # 直接返回后台线程更新的状态
        with self._login_status_lock:
            if not self._login_in_progress:
                # 检查是否已有有效会话
                if self.session_manager.is_session_valid():
                    return {"success": True, "status": "success", "message": "已登录"}
                return {"success": False, "status": "not_started", "message": "登录未开始"}
            
            # 返回后台线程更新的状态
            return self._login_status.copy()

    def cancel_login(self):
        """取消登录流程（弹窗模式）"""
        logger.info("取消登录流程")
        self._login_cancel_event.set()  # 通知后台线程停止
        with self._login_status_lock:
            self._login_in_progress = False
            self._login_start_time = None
            self._login_qrcode = None
            self._login_status = {}

    def is_login_in_progress(self) -> bool:
        """检查登录是否正在进行中"""
        with self._login_status_lock:
            return self._login_in_progress

    def get_login_mode(self) -> str:
        """获取当前配置的登录模式"""
        return config.LOGIN_MODE
