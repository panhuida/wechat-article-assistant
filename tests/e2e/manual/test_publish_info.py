"""测试发布时间和地点信息注入功能"""

from pathlib import Path

from src.wechat_article_assistant.services.download_service import DownloadService


def test_download_with_publish_info():
    """测试下载文章并验证发布信息"""

    # 创建下载服务实例
    ds = DownloadService()

    # 测试文章URL（使用已知的公众号文章）
    test_url = "https://mp.weixin.qq.com/s/Wcn1k60h020OVvPFCnYiEA"

    print("=" * 60)
    print("开始测试发布时间和地点信息注入功能")
    print("=" * 60)
    print(f"测试URL: {test_url}")
    print()

    # 下载文章
    success, msg = ds.download_article(
        test_url, "测试文章", "功能测试", save_dir=Path("E:/temp/test_download")
    )

    print()
    print(f"下载结果: {'✅ 成功' if success else '❌ 失败'}")
    print(f"消息: {msg}")
    print()

    if success:
        # 验证HTML文件
        html_file = Path("E:/temp/test_download/功能测试").glob("*.html")
        html_file = next(html_file, None)

        if html_file and html_file.exists():
            print(f"HTML文件: {html_file}")
            print()

            # 读取并验证内容
            content = html_file.read_text(encoding="utf-8")

            # 检查发布时间
            import re

            publish_time_match = re.search(r'id="publish_time"[^>]*>([^<]+)<', content)
            if publish_time_match:
                print(f"✅ 发布时间: {publish_time_match.group(1)}")
            else:
                print("❌ 未找到发布时间")

            # 检查IP归属地
            ip_match = re.search(r'id="js_ip_wording"[^>]*>([^<]+)<', content)
            if ip_match:
                print(f"✅ IP归属地: {ip_match.group(1)}")
            else:
                print("ℹ️  没有IP归属地（某些文章可能没有此信息）")

            print()
            print("=" * 60)
            print("测试完成！")
            print("=" * 60)
        else:
            print("❌ 未找到下载的HTML文件")


if __name__ == "__main__":
    test_download_with_publish_info()
