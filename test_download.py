"""测试文章下载功能"""

import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wechat_article_assistant.services.download_service import DownloadService
from wechat_article_assistant.config import config

def test_download():
    """测试下载单篇文章"""
    
    print("=" * 60)
    print("文章下载功能测试")
    print("=" * 60)
    print()
    
    # 测试URL（使用真实的微信文章URL）
    test_url = input("请输入测试文章URL（直接回车使用默认测试）: ").strip()
    if not test_url:
        print("\n⚠️  请提供一个真实的微信公众号文章URL进行测试")
        print("示例: https://mp.weixin.qq.com/s/xxxxx")
        return
    
    test_title = input("请输入文章标题（默认：测试文章）: ").strip() or "测试文章"
    test_account = input("请输入公众号名称（默认：测试公众号）: ").strip() or "测试公众号"
    
    print()
    print("开始测试下载...")
    print(f"URL: {test_url}")
    print(f"标题: {test_title}")
    print(f"公众号: {test_account}")
    print()
    
    # 创建下载服务
    download_service = DownloadService()
    
    # 执行下载
    success, message = download_service.download_article(
        article_url=test_url,
        article_title=test_title,
        account_name=test_account
    )
    
    print()
    print("=" * 60)
    if success:
        print("✅ 测试成功！")
        print()
        print(message)
        print()
        print("请检查下载的文件:")
        print(f"位置: {config.DOWNLOAD_DIR}")
        print()
        print("验证清单:")
        print("  □ HTML文件能正常打开")
        print("  □ 文章内容完整显示")
        print("  □ 所有图片正常加载")
        print("  □ 样式保持一致")
        print("  □ .assets 文件夹包含图片和CSS")
        print("  □ .meta.json 文件包含源URL")
    else:
        print("❌ 测试失败")
        print()
        print(f"错误: {message}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_download()
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
