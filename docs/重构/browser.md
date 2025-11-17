🧑‍💻 ## USER

@src\wechat_article_assistant\browser\** 如果重新实现，请评估并规划项目结构，以及每个模块的代码结构。


✨ ## MODEL

好的，这是一个非常好的问题。对现有 `browser` 模块进行重新评估和规划，可以显著提升代码的可维护性、可扩展性和健壮性。

### 现有结构评估

当前 `src/wechat_article_assistant/browser/` 目录下的结构存在一些问题：

1.  **职责不清 (Unclear Responsibilities):**
    *   `browser_manager.py`: 只负责启动和关闭浏览器，是一个非常薄的封装。
    *   `session_manager.py`: 负责将 `cookies` 和 `token` 序列化到文件，但它本身不与浏览器直接交互，也不知道 `localStorage` 等其他关键会话信息。
    *   `wechat_login.py`: 成为了一个“上帝对象”，它**既懂浏览器操作，又懂会话管理，还懂微信登录页面的具体UI逻辑**。这三者紧密耦合在一起，难以维护和测试。

2.  **耦合度高 (High Coupling):**
    *   `wechat_login.py` 强依赖于 `BrowserManager` 和 `SessionManager` 的具体实现。如果你想换一种方式管理浏览器或会话，就必须修改 `wechat_login.py`。
    *   会话的保存逻辑（例如从URL提取token）散落在 `wechat_login.py` 中，而不是由会话管理者自己完成。

3.  **可扩展性差 (Poor Extensibility):**
    *   如果未来需要增加对另一个网站（例如“微信开放平台”）的自动化操作，你可能需要复制大量 `wechat_login.py` 的逻辑，导致代码重复。

4.  **同步阻塞 (Synchronous Blocking):**
    *   整个模块基于 `sync_api`，在进行网络等待时会阻塞线程，不符合现代Web应用和I/O密集型任务的最佳实践。

### 重新规划项目结构

为了解决上述问题，我建议采用**分层**和**面向切面**的设计思想，将浏览器管理、业务任务和会话状态彻底解耦。

**新的项目结构规划:**

```
src/wechat_article_assistant/browser/
├── __init__.py         # 模块入口，可以提供单例的BrowserManager实例
├── browser.py          # (新的核心) 统一的、异步的浏览器管理器，内置会话管理
├── tasks/              # (新目录) 存放具体的浏览器操作任务
│   ├── __init__.py
│   └── wechat_mp_login.py  # 专门负责微信公众号登录的UI交互逻辑
└── exceptions.py       # (新文件) 自定义浏览器相关异常
```

---

### 各模块代码结构规划

#### 1. `browser.py` (新的浏览器核心)

这个模块将是**唯一**与 Playwright 直接交互的底层模块。它将 `BrowserManager` 和 `SessionManager` 的职责合并并大幅增强。

**核心职责:**

*   管理 Playwright 浏览器实例的完整生命周期（启动、关闭）。
*   **内置异步会话管理**，使用 Playwright 原生的 `storage_state` 机制，自动处理 Cookies、`localStorage` 等所有会话信息。
*   提供一个简单的、统一的接口（如 `get_page`）供上层业务调用。
*   采用**异步** (`async/await`) 模型。

**代码结构草案:**

```python
# src/wechat_article_assistant/browser/browser.py

import asyncio
from typing import Optional
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, Playwright

from ..config import config
from ..utils.logger import app_logger
from .exceptions import BrowserError

class BrowserManager:
    """
    统一的异步浏览器管理器，内置会话状态持久化。
    设计为单例模式或全局共享实例。
    """
    _instance: Optional["BrowserManager"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        if BrowserManager._instance is not None:
            raise RuntimeError("BrowserManager is a singleton, use get_instance() instead.")
        
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self._storage_state_path = config.DATA_DIR / "browser_state.json"

    @classmethod
    async def get_instance(cls) -> "BrowserManager":
        """获取单例实例"""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
                await cls._instance._initialize()
        return cls._instance

    async def _initialize(self):
        """初始化 Playwright 和浏览器"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=config.HEADLESS)
            app_logger.info("Browser initialized successfully.")
        except Exception as e:
            raise BrowserError(f"Failed to initialize browser: {e}")

    async def get_page(self) -> Page:
        """
        获取一个带有会话状态的页面。
        这是与外部交互的主要方法。
        """
        if not self.browser:
            raise BrowserError("Browser is not initialized.")
        
        storage_state = self._load_storage_state()
        context = await self.browser.new_context(storage_state=storage_state)
        page = await context.new_page()
        return page

    async def save_page_state(self, page: Page):
        """从给定的页面保存其上下文的会话状态"""
        try:
            state = await page.context.storage_state()
            self._storage_state_path.parent.mkdir(exist_ok=True, parents=True)
            with open(self._storage_state_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(state, f, indent=2)
            app_logger.info(f"Browser state saved to {self._storage_state_path}")
        except Exception as e:
            app_logger.error(f"Failed to save browser state: {e}")

    def _load_storage_state(self) -> Optional[dict]:
        """从文件加载会话状态"""
        if self._storage_state_path.exists():
            app_logger.info(f"Loading browser state from {self._storage_state_path}")
            with open(self._storage_state_path, 'r', encoding='utf-8') as f:
                import json
                return json.load(f)
        app_logger.warning("No browser state file found, starting fresh.")
        return None

    async def close(self):
        """关闭浏览器和 Playwright 实例"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        app_logger.info("Browser closed.")

# 在 __init__.py 中可以提供一个全局实例
# browser_manager = await BrowserManager.get_instance()
```

#### 2. `tasks/wechat_mp_login.py` (具体的业务任务)

这个模块**只关心一件事**：如何在给定的 `Page` 对象上完成微信公众号的登录流程。它**完全不知道**浏览器是怎么启动的，会话是怎么保存的。

**核心职责:**

*   封装与特定页面（微信公众号登录页）的UI交互逻辑。
*   提供独立的、可测试的、可重用的函数。

**代码结构草案:**

```python
# src/wechat_article_assistant/browser/tasks/wechat_mp_login.py

import asyncio
from typing import Optional
from playwright.async_api import Page

from ..exceptions import LoginTimeoutError
from ...utils.logger import app_logger

async def get_login_qr_code(page: Page) -> Optional[str]:
    """
    在给定的页面上查找并返回登录二维码的URL。
    """
    app_logger.info("Attempting to find QR code on the page.")
    # ... (这里是之前 wechat_login.py 中寻找二维码的逻辑，但改为异步)
    # 例如: await page.wait_for_selector(...)
    # qr_img = await page.query_selector(...)
    # qr_url = await qr_img.get_attribute("src")
    # ...
    # 返回完整的二维码URL
    return "https://mp.weixin.qq.com/..."

async def wait_for_login_redirect(page: Page, timeout: int = 120) -> bool:
    """
    等待页面跳转到登录后的状态。
    成功返回 True，超时或失败则抛出异常。
    """
    app_logger.info("Waiting for user to scan QR code and login...")
    initial_url = page.url
    try:
        # 等待URL变化，并且包含登录后的关键字
        await page.wait_for_url(
            lambda url: "cgi-bin/home" in url or "token=" in url,
            timeout=timeout * 1000
        )
        app_logger.info(f"Login successful, redirected to: {page.url}")
        return True
    except Exception as e:
        app_logger.error("Waiting for login timed out or failed.")
        raise LoginTimeoutError("Login timed out.") from e

```

#### 3. `exceptions.py` (自定义异常)

定义清晰的异常类型，有助于上层代码进行更精确的错误处理。

**代码结构草案:**

```python
# src/wechat_article_assistant/browser/exceptions.py

class BrowserError(Exception):
    """与浏览器操作相关的基类异常"""
    pass

class BrowserConnectionError(BrowserError):
    """浏览器连接或初始化失败"""
    pass

class LoginError(BrowserError):
    """登录流程相关的基类异常"""
    pass

class QRCodeNotFoundError(LoginError):
    """找不到登录二维码"""
    pass

class LoginTimeoutError(LoginError):
    """登录超时"""
    pass
```

### 新旧对比与优势

| 特性 | 旧结构 | 新结构 (规划) |
| :--- | :--- | :--- |
| **职责划分** | 模糊，`wechat_login.py` 是上帝对象 | 清晰，`browser.py`管浏览器，`tasks/`管业务 |
| **耦合性** | 高度耦合 | 低耦合，业务逻辑与浏览器管理完全分离 |
| **会话管理** | 手动、不完整 (仅Cookie/Token) | 自动、完整 (使用`storage_state`) |
| **编程模型** | 同步 | **异步** |
| **可测试性** | 困难，需要同时mock多个类 | 简单，可单独测试每个`task`函数 |
| **可扩展性** | 差，增加新网站需复制大量代码 | 好，只需在`tasks/`下增加新任务文件 |

通过这次重构，`browser` 模块将变得更加专业、健壮和易于维护，并且能真正解决**免密登录**的核心痛点。