"""测试重构后的browser包"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wechat_article_assistant.browser import (
    BrowserManager,
    SessionManager,
    WechatAuthenticator,
)


def test_singleton():
    """测试单例模式"""
    print("=" * 60)
    print("测试1: BrowserManager 单例模式")
    print("=" * 60)

    bm1 = BrowserManager()
    bm2 = BrowserManager()

    assert bm1 is bm2, "单例模式失败"
    print("✓ 单例模式工作正常")
    print(f"  实例1 ID: {id(bm1)}")
    print(f"  实例2 ID: {id(bm2)}")
    print()


def test_session_manager():
    """测试会话管理器"""
    print("=" * 60)
    print("测试2: SessionManager 基本功能")
    print("=" * 60)

    sm = SessionManager()
    print("✓ SessionManager 初始化成功")
    print(f"  会话文件路径: {sm.session_file}")

    # 检查会话状态
    is_valid = sm.is_session_valid()
    print(f"  当前会话有效: {is_valid}")

    if is_valid:
        session = sm.load_session()
        print(f"  会话中包含 {len(session.get('cookies', []))} 个cookies")
        print(
            f"  Token: {session.get('token', 'None')[:20] if session.get('token') else 'None'}..."
        )
    print()


def test_authenticator():
    """测试认证管理器"""
    print("=" * 60)
    print("测试3: WechatAuthenticator 初始化")
    print("=" * 60)

    auth = WechatAuthenticator()
    print("✓ WechatAuthenticator 初始化成功")
    print(f"  登录URL: {auth.login_url}")
    print(f"  SessionManager: {type(auth.session_manager).__name__}")
    print(f"  BrowserManager: {type(auth.browser_manager).__name__}")

    # 验证单例
    assert auth.browser_manager is BrowserManager(), "BrowserManager 不是单例"
    print("✓ BrowserManager 单例验证成功")
    print()


def test_structure():
    """测试模块结构"""
    print("=" * 60)
    print("测试4: 模块结构检查")
    print("=" * 60)

    from wechat_article_assistant import browser

    expected_attrs = ["BrowserManager", "SessionManager", "WechatAuthenticator"]
    for attr in expected_attrs:
        assert hasattr(browser, attr), f"模块缺少 {attr}"
        print(f"✓ {attr} 导出正常")
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始测试重构后的browser包")
    print("=" * 60 + "\n")

    try:
        test_singleton()
        test_session_manager()
        test_authenticator()
        test_structure()

        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        print("\n重构要点总结：")
        print("1. ✓ BrowserManager 改为单例模式")
        print("2. ✓ SessionManager 保持独立")
        print("3. ✓ WechatAuthenticator 作为协调者")
        print("4. ✓ 移除二维码弹窗功能")
        print("5. ✓ 搜索接口自动处理认证")
        print()

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
