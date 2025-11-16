"""测试登录功能的脚本"""

import sys
import time
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from wechat_article_assistant.browser.wechat_login import WechatLogin


def test_login():
    """测试登录流程"""
    print("=" * 60)
    print("微信公众平台登录测试")
    print("=" * 60)
    print()

    login = WechatLogin()

    # 检查登录状态
    print("1. 检查登录状态...")
    is_logged_in = login.check_login_status()
    print(f"   当前登录状态: {'已登录' if is_logged_in else '未登录'}")
    print()

    if not is_logged_in:
        print("2. 获取登录二维码...")
        qr_url = login.get_qr_code_url()

        if qr_url:
            print("   ✓ 二维码URL获取成功")
            print(f"   URL: {qr_url[:100]}...")
            print()
            print("3. 等待扫码登录...")
            print("   请在弹出的浏览器窗口中扫描二维码")
            print()
            print("   【重要提示】")
            print("   - 扫码后请等待，不要手动关闭浏览器")
            print("   - 程序会自动检测登录状态")
            print("   - 最长等待时间: 120秒")
            print()

            # 显示倒计时
            print("   等待中", end="", flush=True)
            success = login.wait_for_login(timeout=120)
            print()  # 换行

            if success:
                print()
                print("   ✓ 登录成功！")
                print()

                # 验证会话文件
                session_file = Path("data/wechat_session.json")
                if session_file.exists():
                    print("   ✓ 会话文件已保存")
                    print(f"   位置: {session_file.absolute()}")
                else:
                    print("   ⚠ 警告: 会话文件未找到")
            else:
                print()
                print("   ✗ 登录失败或超时")
                print()
                print("   可能的原因：")
                print("   1. 未在120秒内完成扫码")
                print("   2. 页面跳转检测失败")
                print("   3. 网络连接问题")
                print()
                print("   建议：")
                print("   1. 重新运行此测试")
                print("   2. 确保扫码后等待页面完全加载")
                print("   3. 查看 logs/app.log 了解详细错误")
        else:
            print("   ✗ 获取二维码失败")
            print()
            print("   请检查以下内容:")
            print("   - Playwright是否正确安装 (playwright install chromium)")
            print("   - 网络连接是否正常")
            print("   - 是否可以访问 https://mp.weixin.qq.com")
    else:
        print("2. 已经登录，无需重新登录")

        # 显示会话信息
        session_file = Path("data/wechat_session.json")
        if session_file.exists():
            import json

            with open(session_file, "r", encoding="utf-8") as f:
                session = json.load(f)
                print(f"   会话文件: {session_file.absolute()}")
                print(f"   Cookies数量: {len(session.get('cookies', []))}")
                print(f"   Token: {'已保存' if session.get('token') else '无'}")

    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)

    # 关闭浏览器
    time.sleep(2)
    login.close()


if __name__ == "__main__":
    try:
        test_login()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        import traceback

        traceback.print_exc()
