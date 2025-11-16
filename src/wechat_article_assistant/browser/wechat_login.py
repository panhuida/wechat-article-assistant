"""微信公众平台登录处理模块"""

import time
from typing import Optional, Dict, Any
from .browser_manager import BrowserManager
from .session_manager import SessionManager
from ..config import config
from ..utils.logger import app_logger


class WechatLogin:
    """微信公众平台登录处理器"""

    def __init__(self):
        """初始化登录处理器"""
        self.browser_manager = BrowserManager()
        self.session_manager = SessionManager()
        self.login_url = f"{config.WECHAT_MP_URL}/"

    def check_login_status(self) -> bool:
        """
        检查登录状态

        Returns:
            是否已登录
        """
        return self.session_manager.is_session_valid()

    def get_qr_code_url(self) -> Optional[str]:
        """
        获取登录二维码URL

        Returns:
            二维码URL，失败返回None
        """
        try:
            app_logger.info("开始获取登录二维码")
            page = self.browser_manager.start(headless=False)
            app_logger.info(f"正在访问: {self.login_url}")
            page.goto(self.login_url, wait_until="networkidle")

            # 等待二维码加载，尝试多个可能的选择器
            try:
                # 尝试等待常见的二维码容器选择器
                page.wait_for_selector(
                    ".qrcode, .login_qrcode, #login_qrcode, .qrcode_login", timeout=15000
                )
            except Exception as e:
                app_logger.warning(f"等待二维码选择器超时: {e}")

            # 尝试多个可能的选择器来获取二维码图片
            selectors = [
                ".qrcode img",
                ".login_qrcode img",
                "#login_qrcode img",
                ".qrcode_login img",
                "img[alt*='二维码']",
                "img[alt*='QR']",
                ".weui-desktop-login__qrcode img",
            ]

            qr_url = None
            for selector in selectors:
                try:
                    qr_img = page.query_selector(selector)
                    if qr_img:
                        qr_url = qr_img.get_attribute("src")
                        if qr_url:
                            app_logger.info(f"通过选择器 '{selector}' 获取登录二维码成功")
                            break
                except Exception as e:
                    app_logger.debug(f"选择器 '{selector}' 未找到: {e}")
                    continue

            if not qr_url:
                # 如果还是没找到，尝试获取所有图片并找最大的
                app_logger.warning("未通过选择器找到二维码，尝试查找所有图片")
                all_imgs = page.query_selector_all("img")
                app_logger.info(f"页面共有 {len(all_imgs)} 个图片元素")
                for img in all_imgs:
                    src = img.get_attribute("src")
                    if src:
                        app_logger.info(f"找到图片: {src[:100]}")
                        # 通常二维码图片URL包含特定关键词
                        if any(
                            keyword in src.lower() for keyword in ["qrcode", "qr", "login", "scan"]
                        ):
                            qr_url = src
                            app_logger.info("通过URL关键词匹配找到二维码")
                            break

            if qr_url:
                # 处理相对路径，转换为完整URL
                if qr_url.startswith("/"):
                    qr_url = f"https://mp.weixin.qq.com{qr_url}"
                    app_logger.info(f"转换相对路径为完整URL: {qr_url[:100]}")
                elif qr_url.startswith("//"):
                    qr_url = f"https:{qr_url}"
                    app_logger.info(f"补全协议: {qr_url[:100]}")

                return qr_url
            else:
                app_logger.error("未能获取到二维码URL")
                return None

        except Exception as e:
            app_logger.error(f"获取登录二维码失败: {e}", exc_info=True)
            return None
            return None

    def wait_for_login(self, timeout: int = 300) -> bool:
        """
        等待用户扫码登录

        Args:
            timeout: 超时时间（秒）

        Returns:
            是否登录成功
        """
        try:
            page = self.browser_manager.page
            if not page:
                app_logger.error("浏览器页面未初始化")
                return False

            app_logger.info("开始等待登录...")

            start_time = time.time()
            initial_url = page.url
            app_logger.info(f"初始URL: {initial_url}")

            # 检查初始URL是否已经是登录后的页面
            if any(keyword in initial_url for keyword in ["cgi-bin/home", "token="]):
                app_logger.info("检测到已经在登录后的页面，直接保存会话")
                self._save_login_session()
                app_logger.info("登录成功！")
                return True

            # 等待URL变化
            while time.time() - start_time < timeout:
                try:
                    current_url = page.url

                    # 检查URL是否已经变化（离开登录页）
                    if current_url != initial_url:
                        app_logger.info(f"URL已变化: {current_url}")

                        # 检查是否跳转到了后台页面
                        if any(
                            keyword in current_url
                            for keyword in ["cgi-bin/home", "token=", "home/index"]
                        ):
                            app_logger.info("检测到登录后的页面特征")

                            # 再等待一下确保页面完全加载
                            time.sleep(2)

                            # 检查是否有登录后才有的元素
                            try:
                                page.wait_for_selector("body", timeout=5000)
                                app_logger.info("页面已加载完成")
                            except:
                                pass

                            # 保存会话数据
                            app_logger.info("开始保存登录会话...")
                            self._save_login_session()
                            app_logger.info("登录成功！")
                            return True

                    # 检查是否还有二维码（没有二维码说明已登录或跳转）
                    try:
                        qr_element = page.query_selector(
                            "img[src*='qrcode'], img[src*='scanloginqrcode']"
                        )
                        if not qr_element:
                            app_logger.info("二维码元素已消失，可能已登录")
                            # 再检查一下URL
                            time.sleep(2)
                            current_url = page.url
                            if any(
                                keyword in current_url
                                for keyword in ["cgi-bin/home", "token=", "home/index"]
                            ):
                                app_logger.info(f"确认登录成功，当前URL: {current_url}")
                                self._save_login_session()
                                return True
                    except:
                        pass

                except Exception as e:
                    app_logger.debug(f"检查登录状态时出错: {e}")

                time.sleep(1)

            app_logger.warning("登录超时")
            return False

        except Exception as e:
            app_logger.error(f"等待登录失败: {e}", exc_info=True)
            return False

    def _save_login_session(self):
        """保存登录会话数据"""
        try:
            app_logger.info("开始保存会话数据...")

            # 获取cookies
            cookies = self.browser_manager.get_cookies()
            app_logger.info(f"获取到 {len(cookies)} 个cookies")

            # 提取token（从cookies或页面URL中）
            token = None
            for cookie in cookies:
                if cookie.get("name") == "token":
                    token = cookie.get("value")
                    app_logger.info(f"从cookies中找到token: {token[:20]}...")
                    break

            if not token:
                # 尝试从URL中提取token
                page = self.browser_manager.page
                if page:
                    url = page.url
                    app_logger.info(f"当前URL: {url}")
                    if "token=" in url:
                        token = url.split("token=")[1].split("&")[0]
                        app_logger.info(f"从URL中提取token: {token[:20]}...")

            # 保存会话
            self.session_manager.save_session(cookies, token)
            app_logger.info(f"登录会话已保存到: {self.session_manager.session_file}")

            # 验证保存
            if self.session_manager.session_file.exists():
                app_logger.info("✓ 会话文件保存成功")
            else:
                app_logger.warning("⚠ 会话文件未能保存")

        except Exception as e:
            app_logger.error(f"保存登录会话失败: {e}", exc_info=True)
        except Exception as e:
            app_logger.error(f"保存登录会话失败: {e}")

    def login_with_session(self) -> bool:
        """
        使用已保存的会话登录

        Returns:
            是否登录成功
        """
        try:
            session_data = self.session_manager.load_session()
            if not session_data:
                return False

            page = self.browser_manager.start(headless=True)
            cookies = session_data.get("cookies", [])
            self.browser_manager.set_cookies(cookies)

            # 访问首页验证登录状态
            page.goto(self.login_url)
            time.sleep(2)

            # 检查是否需要重新登录
            if "cgi-bin" in page.url or "home" in page.url:
                app_logger.info("使用会话登录成功")
                return True
            else:
                app_logger.warning("会话已失效")
                return False
        except Exception as e:
            app_logger.error(f"使用会话登录失败: {e}")
            return False

    def logout(self):
        """登出并清除会话"""
        self.session_manager.clear_session()
        self.browser_manager.stop()
        app_logger.info("已登出")

    def close(self):
        """关闭浏览器"""
        self.browser_manager.stop()
