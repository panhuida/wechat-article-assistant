"""诊断工具 - 检查环境配置"""

import sys
from pathlib import Path


def check_environment():
    """检查运行环境"""
    print("=" * 60)
    print("环境诊断工具")
    print("=" * 60)
    print()

    # 检查Python版本
    print("1. Python版本:")
    print(f"   {sys.version}")
    py_version = sys.version_info
    if py_version >= (3, 12):
        print("   ✓ 版本符合要求 (>= 3.12)")
    else:
        print(f"   ✗ 版本过低，需要 Python 3.12+")
    print()

    # 检查依赖包
    print("2. 依赖包检查:")
    required_packages = [
        "flask",
        "sqlalchemy",
        "python-dotenv",
        "playwright",
        "requests",
        "bs4",  # beautifulsoup4
        "PIL",  # pillow
        "qrcode",
    ]

    for package in required_packages:
        try:
            if package == "bs4":
                __import__("bs4")
                print(f"   ✓ beautifulsoup4")
            elif package == "PIL":
                __import__("PIL")
                print(f"   ✓ pillow")
            elif package == "python-dotenv":
                __import__("dotenv")
                print(f"   ✓ {package}")
            else:
                __import__(package)
                print(f"   ✓ {package}")
        except ImportError:
            print(f"   ✗ {package} - 未安装")
    print()

    # 检查Playwright浏览器
    print("3. Playwright浏览器检查:")
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                print("   ✓ Chromium浏览器已安装")
            except Exception as e:
                print(f"   ✗ Chromium浏览器未安装或无法启动")
                print(f"   错误: {e}")
                print("   解决方法: 运行 playwright install chromium")
    except ImportError:
        print("   ✗ Playwright未安装")
    print()

    # 检查目录结构
    print("4. 目录结构检查:")
    required_dirs = ["src", "data", "logs", "tests", "docs"]
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"   ✓ {dir_name}/")
        else:
            print(f"   ✗ {dir_name}/ - 不存在")
            if dir_name in ["data", "logs"]:
                print(f"      尝试创建...")
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    print(f"      ✓ 已创建")
                except Exception as e:
                    print(f"      ✗ 创建失败: {e}")
    print()

    # 检查配置文件
    print("5. 配置文件检查:")
    config_files = [".env.example", "requirements.txt", "pyproject.toml"]
    for file_name in config_files:
        file_path = Path(file_name)
        if file_path.exists():
            print(f"   ✓ {file_name}")
        else:
            print(f"   ✗ {file_name} - 不存在")
    print()

    # 检查网络连接
    print("6. 网络连接检查:")
    try:
        import requests

        response = requests.get("https://mp.weixin.qq.com", timeout=10)
        if response.status_code == 200:
            print("   ✓ 可以访问微信公众平台")
        else:
            print(f"   ⚠ 访问微信公众平台返回状态码: {response.status_code}")
    except Exception as e:
        print(f"   ✗ 无法访问微信公众平台")
        print(f"   错误: {e}")
    print()

    print("=" * 60)
    print("诊断完成")
    print("=" * 60)
    print()
    print("建议:")
    print("1. 确保所有依赖包已安装: pip install -r requirements.txt")
    print("2. 安装Playwright浏览器: playwright install chromium")
    print("3. 检查网络连接，确保可以访问微信公众平台")
    print()


if __name__ == "__main__":
    check_environment()
