"""命令行工具"""

import sys
import argparse
from pathlib import Path
from .services.download_service import DownloadService
from .utils.logger import download_logger
from .config import config


def main():
    """命令行工具主函数"""
    parser = argparse.ArgumentParser(description="微信公众号文章阅读助手")

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # 下载命令
    download_parser = subparsers.add_parser("download", help="下载文章")
    download_parser.add_argument("url", nargs="?", help="文章URL")
    download_parser.add_argument("--file", "-f", help="包含文章链接的文件路径")
    download_parser.add_argument("--output", "-o", help="输出目录", default=None)
    download_parser.add_argument("--verbose", "-v", action="store_true", help="显示详细日志")

    args = parser.parse_args()

    if args.command == "download":
        download_command(args)
    else:
        parser.print_help()


def download_command(args):
    """下载命令处理"""
    download_service = DownloadService()

    # 设置输出目录
    output_dir = Path(args.output) if args.output else None

    if args.file:
        # 从文件批量下载
        print(f"从文件读取URL: {args.file}")
        success_count, fail_count, errors = download_service.download_from_file(args.file, output_dir)
        print(f"\n下载完成:")
        print(f"  成功: {success_count}")
        print(f"  失败: {fail_count}")

        if errors and args.verbose:
            print("\n错误详情:")
            for error in errors:
                print(f"  - {error}")

    elif args.url:
        # 下载单个URL
        print(f"下载文章: {args.url}")
        success, message = download_service.download_article(
            args.url,
            "命令行下载",
            "命令行下载",
            output_dir
        )

        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")

    else:
        print("错误: 请指定文章URL或文件路径")
        print("示例:")
        print("  python -m wechat_article_assistant download <article_url>")
        print("  python -m wechat_article_assistant download --file <file_path>")
        sys.exit(1)


if __name__ == "__main__":
    main()
