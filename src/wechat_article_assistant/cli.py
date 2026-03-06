"""命令行工具"""

import argparse
import sys
from pathlib import Path

from .services.article_service import ArticleService
from .services.download_service import DownloadService

__all__ = ["main"]


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

    # 采集最近文章命令
    collect_recent_parser = subparsers.add_parser(
        "collect-recent", help="获取所有公众号最近5次发的文章"
    )
    collect_recent_parser.add_argument("--verbose", "-v", action="store_true", help="显示失败详情")

    args = parser.parse_args()

    if args.command == "download":
        download_command(args)
    elif args.command == "collect-recent":
        collect_recent_command(args)
    else:
        parser.print_help()


def download_command(args: argparse.Namespace) -> None:
    """下载命令处理"""
    download_service = DownloadService()

    # 设置输出目录
    output_dir = Path(args.output) if args.output else None

    if args.file:
        # 从文件批量下载
        print(f"\n{'=' * 60}")
        print(f"从文件读取URL: {args.file}")
        print(f"{'=' * 60}\n")

        success_count, fail_count, errors = download_service.download_from_file(
            args.file, output_dir
        )

        print(f"\n{'=' * 60}")
        print("下载完成!")
        print(f"{'=' * 60}")
        print(f"成功: {success_count} 篇")
        print(f"失败: {fail_count} 篇")

        if errors and args.verbose:
            print("\n错误详情:")
            for error in errors:
                print(f"  ✗ {error}")

        print(f"{'=' * 60}\n")

    elif args.url:
        # 下载单个URL
        print(f"\n{'=' * 60}")
        print(f"下载文章: {args.url}")
        print(f"{'=' * 60}\n")

        success, message = download_service.download_article(
            args.url, "命令行下载", "命令行下载", output_dir
        )

        print(f"\n{'=' * 60}")
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
        print(f"{'=' * 60}\n")

    else:
        print("\n错误: 请指定文章URL或文件路径\n")
        print("示例:")
        print("  # 下载单篇文章")
        print("  wechat-cli download <article_url>")
        print("  python wechat-cli.py download <article_url>")
        print()
        print("  # 批量下载")
        print("  wechat-cli download --file urls.txt")
        print("  python wechat-cli.py download --file urls.txt")
        print()
        print("  # 指定输出目录")
        print("  wechat-cli download <article_url> --output E:\\我的文档\\公众号")
        print()
        print("  # 显示详细日志")
        print("  wechat-cli download <article_url> --verbose")
        print()
        sys.exit(1)


def collect_recent_command(args: argparse.Namespace) -> None:
    """获取所有公众号最近5次发的文章"""
    article_service = ArticleService()

    print(f"\n{'=' * 60}")
    print("开始采集所有公众号最近5次发的文章...")
    print(f"{'=' * 60}\n")

    success, message, stats = article_service.collect_recent_articles_all_accounts()

    print(f"\n{'=' * 60}")
    if success:
        print(f"✓ {message}")
    else:
        print(f"✗ {message}")

    if stats:
        print(f"{'-' * 60}")
        print(f"公众号总数: {stats.get('total_accounts', 0)}")
        print(f"成功采集: {stats.get('success_accounts', 0)}")
        print(f"失败采集: {stats.get('failed_accounts', 0)}")
        print(f"新增文章: {stats.get('total_articles', 0)}")

        failed_list = stats.get("failed_list", [])
        if failed_list and args.verbose:
            print("\n失败详情:")
            for failed_item in failed_list:
                print(f"  ✗ {failed_item}")
    print(f"{'=' * 60}\n")

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
