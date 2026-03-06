"""命令行工具"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from .config import config
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

    # 按时间范围下载已采集文章命令
    download_articles_parser = subparsers.add_parser(
        "download-articles", help="按文章创建时间范围批量下载文章"
    )
    download_articles_parser.add_argument(
        "--start-time",
        help="开始时间，支持 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS，默认最近一天",
        default=None,
    )
    download_articles_parser.add_argument(
        "--end-time",
        help="结束时间，支持 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS，默认当前时间",
        default=None,
    )
    download_articles_parser.add_argument(
        "--format",
        dest="save_format",
        choices=["html", "markdown"],
        default="markdown",
        help="保存格式，默认 markdown",
    )
    download_articles_parser.add_argument(
        "--nickname",
        help="按公众号名称筛选，支持逗号分隔多个名称（精确匹配）",
        default=None,
    )
    download_articles_parser.add_argument(
        "--output",
        "-o",
        help="保存目录，默认使用 .env 中的 DOWNLOAD_PATH / DOWNLOAD_DIR",
        default=None,
    )
    download_articles_parser.add_argument("--verbose", "-v", action="store_true", help="显示失败详情")

    args = parser.parse_args()

    if args.command == "download":
        download_command(args)
    elif args.command == "collect-recent":
        collect_recent_command(args)
    elif args.command == "download-articles":
        download_articles_command(args)
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


def _parse_cli_datetime(value: str, is_end: bool = False) -> datetime:
    """解析 CLI 传入的日期时间字符串"""
    value = value.strip()
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt)
            if fmt == "%Y-%m-%d":
                if is_end:
                    return parsed.replace(hour=23, minute=59, second=59)
                return parsed.replace(hour=0, minute=0, second=0)
            return parsed
        except ValueError:
            continue

    # 兼容 ISO 格式（例如 2026-03-06T12:00:00）
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is not None:
            return parsed.replace(tzinfo=None)
        return parsed
    except ValueError as e:
        raise ValueError(f"无法解析时间: {value}") from e


def download_articles_command(args: argparse.Namespace) -> None:
    """按时间范围批量下载已采集文章"""
    article_service = ArticleService()
    download_service = DownloadService()

    now = datetime.now()
    default_start = now - timedelta(days=1)
    start_time = default_start
    end_time = now

    try:
        if args.start_time:
            start_time = _parse_cli_datetime(args.start_time, is_end=False)
        if args.end_time:
            end_time = _parse_cli_datetime(args.end_time, is_end=True)
    except ValueError as e:
        print(f"\n错误: {e}\n")
        print("示例:")
        print("  wechat-cli download-articles --start-time 2026-03-05 --end-time 2026-03-06")
        print(
            "  wechat-cli download-articles --start-time '2026-03-05 00:00:00' --format markdown"
        )
        print()
        sys.exit(1)

    if start_time > end_time:
        print("\n错误: 开始时间不能晚于结束时间\n")
        sys.exit(1)

    output_dir = Path(args.output) if args.output else None
    nicknames = (
        [item.strip() for item in args.nickname.split(",") if item.strip()] if args.nickname else []
    )
    nickname_display = ",".join(nicknames) if nicknames else "全部"

    print(f"\n{'=' * 60}")
    print("按时间范围批量下载文章")
    print(f"时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ~ {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"公众号名称: {nickname_display}")
    print(f"保存格式: {args.save_format}")
    print(f"保存路径: {output_dir if output_dir else config.DOWNLOAD_DIR}")
    print(f"{'=' * 60}\n")

    articles = article_service.get_articles_by_create_time_range(
        start_time, end_time, nicknames=nicknames
    )
    if not articles:
        print("未找到符合条件的文章。")
        return

    success_count, fail_count, errors = download_service.download_articles_batch(
        articles, output_dir, output_format=args.save_format
    )

    if success_count > 0:
        article_ids = [article["id"] for article in articles if isinstance(article.get("id"), int)]
        if article_ids:
            article_service.mark_as_downloaded(article_ids)

    print(f"\n{'=' * 60}")
    print(f"匹配文章: {len(articles)} 篇")
    print(f"下载成功: {success_count} 篇")
    print(f"下载失败: {fail_count} 篇")
    print(f"{'=' * 60}\n")

    if errors and args.verbose:
        print("失败详情:")
        for error in errors:
            print(f"  ✗ {error}")
        print()

    if fail_count > 0 and success_count == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
