"""会话管理模块 - 保存和加载微信公众平台登录会话"""

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from ..config import config
from ..utils.logger import app_logger


class SessionManager:
    """会话管理器"""

    def __init__(self, session_file: Path = None):
        """
        初始化会话管理器

        Args:
            session_file: 会话文件路径
        """
        self.session_file = session_file or config.SESSION_FILE
        self.session_file.parent.mkdir(parents=True, exist_ok=True)

        # 缓存会话数据，避免频繁读取文件
        self._cached_session: Optional[Dict[str, Any]] = None
        self._cache_time: float = 0
        self._cache_ttl: int = 300  # 缓存5分钟

    def save_session(
        self, cookies: list, token: str = None, other_data: Dict[str, Any] = None
    ) -> bool:
        """
        保存会话数据

        Args:
            cookies: Cookie列表
            token: Token值
            other_data: 其他数据

        Returns:
            是否保存成功
        """
        try:
            session_data = {"cookies": cookies, "token": token, "other_data": other_data or {}}
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            # 更新缓存
            self._cached_session = session_data
            self._cache_time = time.time()

            app_logger.info(f"会话数据已保存到: {self.session_file}")
            return True
        except Exception as e:
            app_logger.error(f"保存会话数据失败: {e}")
            return False

    def load_session(self, force_reload: bool = False) -> Optional[Dict[str, Any]]:
        """
        加载会话数据（带缓存）

        Args:
            force_reload: 是否强制重新加载，忽略缓存

        Returns:
            会话数据字典，失败返回None
        """
        try:
            # 检查缓存是否有效
            if not force_reload and self._cached_session is not None:
                cache_age = time.time() - self._cache_time
                if cache_age < self._cache_ttl:
                    app_logger.debug(f"使用缓存的会话数据（缓存年龄: {cache_age:.1f}秒）")
                    return self._cached_session

            # 缓存失效或强制重新加载
            if not self.session_file.exists():
                app_logger.warning("会话文件不存在")
                self._cached_session = None
                return None

            with open(self.session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            # 更新缓存
            self._cached_session = session_data
            self._cache_time = time.time()

            app_logger.info("会话数据加载成功")
            return session_data
        except Exception as e:
            app_logger.error(f"加载会话数据失败: {e}")
            self._cached_session = None
            return None

    def clear_session(self) -> bool:
        """
        清除会话数据

        Returns:
            是否清除成功
        """
        try:
            if self.session_file.exists():
                self.session_file.unlink()
                app_logger.info("会话数据已清除")

            # 清除缓存
            self._cached_session = None
            self._cache_time = 0

            return True
        except Exception as e:
            app_logger.error(f"清除会话数据失败: {e}")
            return False

    def invalidate_cache(self):
        """
        使缓存失效（强制下次加载时重新读取文件）
        """
        self._cached_session = None
        self._cache_time = 0
        app_logger.debug("会话缓存已失效")

    def is_session_valid(self) -> bool:
        """
        检查会话是否有效

        Returns:
            会话是否有效
        """
        session_data = self.load_session()
        if not session_data:
            return False

        # 检查必要字段
        if "cookies" not in session_data or not session_data["cookies"]:
            return False

        # 可以添加更多验证逻辑，比如检查过期时间等
        return True
